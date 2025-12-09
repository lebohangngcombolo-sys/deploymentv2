import logging
from threading import Thread
from flask import render_template, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class EmailService:
    """Async SendGrid email service with HTML templates + fallback plain text."""

    # ---------------- Public Email Methods ----------------
    @staticmethod
    def send_verification_email(email, verification_code):
        subject = "Verify Your Email Address"
        html, text = EmailService._render_template(
            "email_templates/verification_email.html",
            verification_code=verification_code,
            fallback_text=f"Your verification code is: {verification_code}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_password_reset_email(email, reset_token):
        subject = "Password Reset Request"
        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        html, text = EmailService._render_template(
            "email_templates/password_reset_email.html",
            reset_link=reset_link,
            fallback_text=f"Reset your password using this link: {reset_link}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_interview_invitation(email, candidate_name, interview_date, interview_type, meeting_link=None):
        subject = "Interview Invitation"
        html, text = EmailService._render_template(
            "email_templates/interview_invitation.html",
            candidate_name=candidate_name,
            interview_date=interview_date,
            interview_type=interview_type,
            meeting_link=meeting_link,
            fallback_text=f"Hi {candidate_name}, your {interview_type} interview is scheduled on {interview_date}. Link: {meeting_link}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_interview_reschedule_email(email, candidate_name, old_time, new_time, interview_type, meeting_link=None):
        subject = "Interview Rescheduled"
        html, text = EmailService._render_template(
            "email_templates/interview_reschedule.html",
            candidate_name=candidate_name,
            old_time=old_time,
            new_time=new_time,
            interview_type=interview_type,
            meeting_link=meeting_link,
            fallback_text=f"Hi {candidate_name}, your {interview_type} interview has been rescheduled from {old_time} to {new_time}. Link: {meeting_link}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_interview_cancellation(email, candidate_name, interview_date, interview_type, reason=None):
        subject = "Interview Cancellation Notice"
        reason_text = reason or "No specific reason provided."
        html, text = EmailService._render_template(
            "email_templates/interview_cancellation.html",
            candidate_name=candidate_name,
            interview_date=interview_date,
            interview_type=interview_type,
            reason=reason_text,
            fallback_text=f"Hi {candidate_name}, your {interview_type} interview scheduled on {interview_date} has been cancelled. Reason: {reason_text}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_application_status_update(email, candidate_name, status, position_title):
        subject = f"Application Update for {position_title or 'your position'}"
        html, text = EmailService._render_template(
            "email_templates/application_status_update.html",
            candidate_name=candidate_name,
            status=status,
            position_title=position_title,
            fallback_text=f"Hi {candidate_name}, your application for {position_title} status is: {status}"
        )
        EmailService._send_async(subject, [email], html, text)

    @staticmethod
    def send_temporary_password(email, password, first_name=None):
        subject = "Your Temporary Password"
        html, text = EmailService._render_template(
            "email_templates/temporary_password.html",
            password=password,
            first_name=first_name,
            current_year=2025,
            fallback_text=f"Hello {first_name or ''},\n\nYour temporary password is: {password}"
        )
        EmailService._send_async(subject, [email], html, text)

    # ---------------- Internal Helpers ----------------
    @staticmethod
    def _render_template(template_path, fallback_text, **context):
        """Render HTML template; return fallback text if rendering fails."""
        try:
            html = render_template(template_path, **context)
        except Exception:
            logging.error(f"Failed to render template {template_path}", exc_info=True)
            html = fallback_text
        return html, fallback_text

    @staticmethod
    def _send_async(subject, recipients, html_body, text_body=None):
        """Send email asynchronously using SendGrid with Flask app context."""
        app = current_app._get_current_object()  # capture actual app instance

        def send_email():
            with app.app_context():  # push app context for this thread
                try:
                    api_key = app.config.get("SENDGRID_API_KEY")
                    sender = app.config.get("MAIL_DEFAULT_SENDER")
                    if not api_key or not sender:
                        raise ValueError("Missing SendGrid API key or sender.")

                    sg = SendGridAPIClient(api_key)
                    for recipient in recipients:
                        message = Mail(
                            from_email=sender,
                            to_emails=recipient,
                            subject=subject,
                            html_content=html_body or text_body,
                            plain_text_content=text_body
                        )
                        response = sg.send(message)
                        logging.info(f"✅ Email sent to {recipient}: {response.status_code}")

                except Exception as e:
                    logging.error(f"❌ SendGrid error for {recipients}: {e}", exc_info=True)

        Thread(target=send_email, daemon=True).start()
