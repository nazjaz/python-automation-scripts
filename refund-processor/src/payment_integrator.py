"""Payment system integration for processing refunds."""

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class PaymentIntegrationError(Exception):
    """Exception raised for payment integration errors."""

    pass


class PaymentIntegrator:
    """Integrates with payment systems to process refunds."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        api_secret: str,
        retry_attempts: int = 3,
        retry_delay_seconds: int = 5,
    ):
        """Initialize payment integrator.

        Args:
            provider: Payment provider name (stripe, paypal, etc.).
            api_key: Payment provider API key.
            api_secret: Payment provider API secret.
            retry_attempts: Number of retry attempts for failed operations.
            retry_delay_seconds: Delay between retry attempts.
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds

    def process_refund(
        self,
        transaction_id: str,
        amount: float,
        currency: str = "USD",
        reason: Optional[str] = None,
    ) -> dict:
        """Process refund through payment provider.

        Args:
            transaction_id: Original payment transaction ID.
            amount: Refund amount.
            currency: Currency code.
            reason: Refund reason (optional).

        Returns:
            Dictionary with refund result including refund ID.

        Raises:
            PaymentIntegrationError: If refund processing fails.
        """
        if self.provider == "stripe":
            return self._process_stripe_refund(transaction_id, amount, currency, reason)
        elif self.provider == "paypal":
            return self._process_paypal_refund(transaction_id, amount, currency, reason)
        else:
            raise PaymentIntegrationError(f"Unsupported payment provider: {self.provider}")

    def _process_stripe_refund(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
        reason: Optional[str],
    ) -> dict:
        """Process refund through Stripe API.

        Args:
            transaction_id: Stripe charge ID.
            amount: Refund amount in cents.
            currency: Currency code.
            reason: Refund reason.

        Returns:
            Dictionary with refund result.

        Raises:
            PaymentIntegrationError: If refund fails.
        """
        amount_cents = int(amount * 100)

        last_exception = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                url = f"https://api.stripe.com/v1/refunds"
                headers = {
                    "Authorization": f"Bearer {self.api_secret}",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                data = {
                    "charge": transaction_id,
                    "amount": amount_cents,
                }
                if reason:
                    data["reason"] = reason

                response = requests.post(url, headers=headers, data=data, timeout=30)
                response.raise_for_status()

                refund_data = response.json()
                logger.info(
                    f"Stripe refund processed: {refund_data.get('id')} for "
                    f"${amount:.2f}"
                )

                return {
                    "success": True,
                    "refund_id": refund_data.get("id"),
                    "status": refund_data.get("status"),
                    "amount": refund_data.get("amount", amount_cents) / 100,
                }

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"Stripe refund attempt {attempt}/{self.retry_attempts} failed: {e}"
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)

        raise PaymentIntegrationError(
            f"Failed to process Stripe refund after {self.retry_attempts} attempts: {last_exception}"
        )

    def _process_paypal_refund(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
        reason: Optional[str],
    ) -> dict:
        """Process refund through PayPal API.

        Args:
            transaction_id: PayPal transaction ID.
            amount: Refund amount.
            currency: Currency code.
            reason: Refund reason.

        Returns:
            Dictionary with refund result.

        Raises:
            PaymentIntegrationError: If refund fails.
        """
        last_exception = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                url = f"https://api.paypal.com/v2/payments/captures/{transaction_id}/refund"
                headers = {
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json",
                }
                data = {
                    "amount": {"value": str(amount), "currency_code": currency},
                }
                if reason:
                    data["note_to_payer"] = reason

                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()

                refund_data = response.json()
                logger.info(
                    f"PayPal refund processed: {refund_data.get('id')} for "
                    f"${amount:.2f}"
                )

                return {
                    "success": True,
                    "refund_id": refund_data.get("id"),
                    "status": refund_data.get("status"),
                    "amount": amount,
                }

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"PayPal refund attempt {attempt}/{self.retry_attempts} failed: {e}"
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)

        raise PaymentIntegrationError(
            f"Failed to process PayPal refund after {self.retry_attempts} attempts: {last_exception}"
        )
