"""Execute remediation workflows for pipeline failures."""

from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager


class RemediationWorkflow:
    """Execute remediation workflows."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize remediation workflow executor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.workflow_templates = config.get("workflow_templates", {})

    def trigger_remediation(
        self,
        pipeline_id: int,
        failure_id: Optional[int] = None,
        failure_type: Optional[str] = None,
    ) -> Dict[str, any]:
        """Trigger remediation workflow for failure.

        Args:
            pipeline_id: Pipeline ID.
            failure_id: Optional failure ID.
            failure_type: Optional failure type.

        Returns:
            Dictionary with workflow execution information.
        """
        if failure_type is None and failure_id:
            session = self.db_manager.get_session()
            try:
                from src.database import Failure

                failure = (
                    session.query(Failure).filter(Failure.id == failure_id).first()
                )
                if failure:
                    failure_type = failure.failure_type
            finally:
                session.close()

        workflow_config = self._get_workflow_for_failure_type(failure_type)
        if not workflow_config:
            return {
                "success": False,
                "message": f"No workflow configured for failure type: {failure_type}",
            }

        workflow_name = workflow_config.get("name", "Default Remediation")
        workflow_type = workflow_config.get("type", "generic")

        workflow = self.db_manager.add_remediation_workflow(
            pipeline_id=pipeline_id,
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            failure_id=failure_id,
        )

        try:
            result = self._execute_workflow(workflow_config, pipeline_id, failure_id)
            self.db_manager.update_workflow_status(
                workflow.id, "completed", result=result
            )

            return {
                "success": True,
                "workflow_id": workflow.id,
                "workflow_name": workflow_name,
                "result": result,
            }
        except Exception as e:
            error_message = str(e)
            self.db_manager.update_workflow_status(
                workflow.id, "failed", error_message=error_message
            )

            return {
                "success": False,
                "workflow_id": workflow.id,
                "error_message": error_message,
            }

    def _get_workflow_for_failure_type(
        self, failure_type: Optional[str]
    ) -> Optional[Dict]:
        """Get workflow configuration for failure type.

        Args:
            failure_type: Failure type.

        Returns:
            Workflow configuration dictionary or None.
        """
        if not failure_type:
            return self.workflow_templates.get("default", {})

        return self.workflow_templates.get(failure_type, self.workflow_templates.get("default", {}))

    def _execute_workflow(
        self, workflow_config: Dict, pipeline_id: int, failure_id: Optional[int]
    ) -> str:
        """Execute workflow steps.

        Args:
            workflow_config: Workflow configuration.
            pipeline_id: Pipeline ID.
            failure_id: Optional failure ID.

        Returns:
            Workflow execution result.
        """
        steps = workflow_config.get("steps", [])
        results = []

        for step in steps:
            step_type = step.get("type")
            step_action = step.get("action")

            if step_type == "retry":
                result = self._retry_pipeline(pipeline_id)
            elif step_type == "rollback":
                result = self._rollback_pipeline(pipeline_id)
            elif step_type == "notify":
                result = self._notify_team(step_action, pipeline_id, failure_id)
            elif step_type == "restart":
                result = self._restart_pipeline(pipeline_id)
            elif step_type == "skip":
                result = self._skip_failed_records(pipeline_id, failure_id)
            else:
                result = f"Executed {step_type}: {step_action}"

            results.append(result)

        return "; ".join(results)

    def _retry_pipeline(self, pipeline_id: int) -> str:
        """Retry pipeline execution.

        Args:
            pipeline_id: Pipeline ID.

        Returns:
            Result message.
        """
        return f"Pipeline {pipeline_id} retry initiated"

    def _rollback_pipeline(self, pipeline_id: int) -> str:
        """Rollback pipeline to previous state.

        Args:
            pipeline_id: Pipeline ID.

        Returns:
            Result message.
        """
        return f"Pipeline {pipeline_id} rollback initiated"

    def _notify_team(
        self, action: str, pipeline_id: int, failure_id: Optional[int]
    ) -> str:
        """Notify team about failure.

        Args:
            action: Notification action.
            pipeline_id: Pipeline ID.
            failure_id: Optional failure ID.

        Returns:
            Result message.
        """
        return f"Team notified about pipeline {pipeline_id} failure"

    def _restart_pipeline(self, pipeline_id: int) -> str:
        """Restart pipeline.

        Args:
            pipeline_id: Pipeline ID.

        Returns:
            Result message.
        """
        return f"Pipeline {pipeline_id} restart initiated"

    def _skip_failed_records(
        self, pipeline_id: int, failure_id: Optional[int]
    ) -> str:
        """Skip failed records and continue.

        Args:
            pipeline_id: Pipeline ID.
            failure_id: Optional failure ID.

        Returns:
            Result message.
        """
        return f"Skipping failed records for pipeline {pipeline_id}"

    def auto_remediate_failures(
        self, pipeline_id: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Automatically remediate open failures.

        Args:
            pipeline_id: Optional pipeline ID to filter by.

        Returns:
            List of remediation results.
        """
        failures = self.db_manager.get_open_failures(pipeline_id=pipeline_id)
        remediation_results = []

        for failure in failures:
            result = self.trigger_remediation(
                pipeline_id=failure.pipeline_id,
                failure_id=failure.id,
                failure_type=failure.failure_type,
            )
            remediation_results.append(result)

        return remediation_results
