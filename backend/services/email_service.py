"""
Email Service for automated reminders
Uses Gmail SMTP for sending emails
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails via Gmail SMTP
    """

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_APP_PASSWORD")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Financial Advisor")

        if not self.email_address or not self.email_password:
            logger.warning("Email credentials not configured. Email features will be disabled.")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.email_address or not self.email_password:
            logger.error("Email service not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.email_address}>"
            msg['To'] = to_email

            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_policy_renewal_reminder(
        self,
        client_name: str,
        client_email: str,
        policy_number: str,
        provider: str,
        renewal_date: date,
        days_until: int
    ) -> bool:
        """
        Send policy renewal reminder email

        Args:
            client_name: Client's name
            client_email: Client's email
            policy_number: Policy number
            provider: Insurance provider
            renewal_date: Policy renewal date
            days_until: Days until renewal

        Returns:
            True if sent successfully
        """
        subject = f"Policy Renewal Reminder - {days_until} days remaining"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .highlight {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏦 Policy Renewal Reminder</h1>
                </div>
                <div class="content">
                    <p>Dear {client_name},</p>

                    <p>This is a friendly reminder that your insurance policy is due for renewal soon.</p>

                    <div class="highlight">
                        <strong>Policy Details:</strong><br>
                        Policy Number: <strong>{policy_number}</strong><br>
                        Provider: <strong>{provider}</strong><br>
                        Renewal Date: <strong>{renewal_date.strftime('%B %d, %Y')}</strong><br>
                        Days Remaining: <strong>{days_until} days</strong>
                    </div>

                    <p>To ensure uninterrupted coverage, please:</p>
                    <ul>
                        <li>Review your policy coverage</li>
                        <li>Ensure premium payment is ready</li>
                        <li>Contact us if you have any questions</li>
                    </ul>

                    <p>We're here to help! Feel free to reach out if you need assistance.</p>

                    <p>Best regards,<br><strong>{self.from_name}</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(client_email, subject, html_body)

    def send_sip_due_reminder(
        self,
        client_name: str,
        client_email: str,
        fund_name: str,
        amount: float,
        sip_day: int
    ) -> bool:
        """
        Send SIP payment due reminder

        Args:
            client_name: Client's name
            client_email: Client's email
            fund_name: Mutual fund name
            amount: SIP amount
            sip_day: Day of month SIP is due

        Returns:
            True if sent successfully
        """
        subject = f"SIP Payment Reminder - {fund_name}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .highlight {{ background: #e8f4fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 SIP Payment Reminder</h1>
                </div>
                <div class="content">
                    <p>Dear {client_name},</p>

                    <p>This is a reminder that your SIP installment is due this month.</p>

                    <div class="highlight">
                        <strong>SIP Details:</strong><br>
                        Fund: <strong>{fund_name}</strong><br>
                        Amount: <strong>₹{amount:,.2f}</strong><br>
                        Due Date: <strong>{sip_day}th of this month</strong>
                    </div>

                    <p>Please ensure sufficient funds are available in your account for the automatic deduction.</p>

                    <p>Regular SIP investments help you build wealth systematically through market cycles.</p>

                    <p>Best regards,<br><strong>{self.from_name}</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(client_email, subject, html_body)

    def send_payment_confirmation(
        self,
        client_name: str,
        client_email: str,
        payment_type: str,  # "policy" or "sip"
        item_name: str,
        amount: float,
        payment_date: date
    ) -> bool:
        """
        Send payment confirmation email

        Args:
            client_name: Client's name
            client_email: Client's email
            payment_type: "policy" or "sip"
            item_name: Policy number or fund name
            amount: Payment amount
            payment_date: Date of payment

        Returns:
            True if sent successfully
        """
        subject = f"Payment Confirmation - {item_name}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .highlight {{ background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Payment Confirmed</h1>
                </div>
                <div class="content">
                    <p>Dear {client_name},</p>

                    <p>We have successfully received your payment.</p>

                    <div class="highlight">
                        <strong>Payment Details:</strong><br>
                        Type: <strong>{payment_type.upper()}</strong><br>
                        {payment_type.capitalize()}: <strong>{item_name}</strong><br>
                        Amount: <strong>₹{amount:,.2f}</strong><br>
                        Date: <strong>{payment_date.strftime('%B %d, %Y')}</strong>
                    </div>

                    <p>Thank you for your timely payment. Your account has been updated.</p>

                    <p>Best regards,<br><strong>{self.from_name}</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated confirmation. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(client_email, subject, html_body)


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get singleton instance of email service"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
