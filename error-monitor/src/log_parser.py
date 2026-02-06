"""Parse application log files for error extraction."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LogParser:
    """Parse log files to extract error information."""

    def __init__(self, config: Dict):
        """Initialize log parser.

        Args:
            config: Configuration dictionary with parsing settings.
        """
        self.config = config
        self.error_patterns = config.get("error_patterns", [])
        self.log_format = config.get("log_format", "standard")
        self.timestamp_format = config.get("timestamp_format", "%Y-%m-%d %H:%M:%S")

    def parse_log_file(self, file_path: Path) -> List[Dict[str, any]]:
        """Parse log file and extract errors.

        Args:
            file_path: Path to log file.

        Returns:
            List of error dictionaries.
        """
        if not file_path.exists():
            return []

        errors = []
        current_error = None
        stack_trace_lines = []

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                error_info = self._parse_line(line)
                if error_info:
                    if current_error:
                        current_error["stack_trace"] = "\n".join(stack_trace_lines)
                        errors.append(current_error)
                        stack_trace_lines = []

                    current_error = error_info
                elif current_error and self._is_stack_trace_line(line):
                    stack_trace_lines.append(line)
                elif current_error:
                    current_error["stack_trace"] = "\n".join(stack_trace_lines)
                    errors.append(current_error)
                    current_error = None
                    stack_trace_lines = []

        if current_error:
            current_error["stack_trace"] = "\n".join(stack_trace_lines)
            errors.append(current_error)

        return errors

    def _parse_line(self, line: str) -> Optional[Dict[str, any]]:
        """Parse a single log line for error information.

        Args:
            line: Log line to parse.

        Returns:
            Error dictionary or None if not an error.
        """
        if self.log_format == "json":
            return self._parse_json_line(line)
        elif self.log_format == "standard":
            return self._parse_standard_line(line)
        else:
            return self._parse_standard_line(line)

    def _parse_standard_line(self, line: str) -> Optional[Dict[str, any]]:
        """Parse standard log format line.

        Args:
            line: Log line to parse.

        Returns:
            Error dictionary or None.
        """
        error_keywords = ["ERROR", "EXCEPTION", "FATAL", "CRITICAL", "FAILED"]
        line_upper = line.upper()

        if not any(keyword in line_upper for keyword in error_keywords):
            return None

        timestamp = self._extract_timestamp(line)
        error_type = self._extract_error_type(line)
        error_message = self._extract_error_message(line)

        if not error_message:
            return None

        return {
            "error_message": error_message,
            "error_type": error_type,
            "timestamp": timestamp,
            "severity": self._determine_severity(line),
        }

    def _parse_json_line(self, line: str) -> Optional[Dict[str, any]]:
        """Parse JSON log format line.

        Args:
            line: Log line to parse.

        Returns:
            Error dictionary or None.
        """
        try:
            import json

            log_entry = json.loads(line)
            level = log_entry.get("level", "").upper()

            if level not in ["ERROR", "FATAL", "CRITICAL"]:
                return None

            return {
                "error_message": log_entry.get("message", ""),
                "error_type": log_entry.get("exception_type", ""),
                "timestamp": self._parse_timestamp(log_entry.get("timestamp", "")),
                "severity": self._determine_severity(level),
                "application": log_entry.get("application", ""),
                "environment": log_entry.get("environment", ""),
                "user_id": log_entry.get("user_id", ""),
                "request_id": log_entry.get("request_id", ""),
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line.

        Args:
            line: Log line.

        Returns:
            Parsed datetime or None.
        """
        timestamp_patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]",
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return datetime.strptime(match.group(1), self.timestamp_format)
                except ValueError:
                    continue

        return datetime.utcnow()

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string.

        Args:
            timestamp_str: Timestamp string.

        Returns:
            Parsed datetime or None.
        """
        if not timestamp_str:
            return datetime.utcnow()

        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.strptime(timestamp_str, self.timestamp_format)
            except ValueError:
                return datetime.utcnow()

    def _extract_error_type(self, line: str) -> Optional[str]:
        """Extract error type from log line.

        Args:
            line: Log line.

        Returns:
            Error type or None.
        """
        error_type_patterns = [
            r"(\w+Exception)",
            r"(\w+Error)",
            r"(\w+Failure)",
            r"ERROR:\s*(\w+)",
        ]

        for pattern in error_type_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_error_message(self, line: str) -> Optional[str]:
        """Extract error message from log line.

        Args:
            line: Log line.

        Returns:
            Error message or None.
        """
        error_message_patterns = [
            r"ERROR[:\s]+(.+)",
            r"EXCEPTION[:\s]+(.+)",
            r"FATAL[:\s]+(.+)",
            r"CRITICAL[:\s]+(.+)",
        ]

        for pattern in error_message_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                message = match.group(1).strip()
                if len(message) > 10:
                    return message

        return None

    def _determine_severity(self, line: str) -> str:
        """Determine error severity from log line.

        Args:
            line: Log line.

        Returns:
            Severity level (low, medium, high, critical).
        """
        line_upper = line.upper()

        if any(keyword in line_upper for keyword in ["FATAL", "CRITICAL"]):
            return "critical"
        elif "ERROR" in line_upper:
            return "high"
        elif "WARNING" in line_upper:
            return "medium"
        else:
            return "low"

    def _is_stack_trace_line(self, line: str) -> bool:
        """Check if line is part of stack trace.

        Args:
            line: Log line.

        Returns:
            True if stack trace line.
        """
        stack_trace_indicators = [
            "at ",
            "File \"",
            "Traceback",
            "Caused by:",
            "in ",
        ]

        return any(indicator in line for indicator in stack_trace_indicators)
