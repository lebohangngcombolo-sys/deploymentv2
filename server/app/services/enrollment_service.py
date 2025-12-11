from app.extensions import db
from app.models import Candidate, User
from datetime import datetime
from app.services.audit2 import AuditService

class EnrollmentService:

    @staticmethod
    def get_or_create_candidate(user_id):
        """
        Fetch existing candidate or create a new one.
        """
        candidate = Candidate.query.filter_by(user_id=user_id).first()
        if candidate:
            return candidate, False

        candidate = Candidate(user_id=user_id)
        db.session.add(candidate)
        return candidate, True  # Commit deferred to main save method

    @staticmethod
    def parse_date(date_str):
        """
        Try multiple common date formats to parse DOB.
        Returns datetime.date or None if parsing fails.
        """
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def save_candidate_enrollment(user_id, data):
        """
        Save candidate enrollment and mark enrollment as completed.
        Returns JSON-like dict and HTTP status code.
        """
        try:
            # Fetch session-bound user
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            # Fetch or create candidate record
            candidate, _ = EnrollmentService.get_or_create_candidate(user.id)

            # Allowed candidate fields
            candidate_fields = {
                "full_name", "phone", "dob", "address", "gender", "bio",
                "title", "location", "nationality", "id_number", "linkedin",
                "github", "cv_url", "cv_text", "portfolio", "cover_letter",
                "profile_picture", "education", "skills", "work_experience",
                "certifications", "languages", "documents", "profile"
            }

            # Update candidate fields
            for field, value in data.items():
                if field == "dob" and isinstance(value, str):
                    parsed_date = EnrollmentService.parse_date(value)
                    if not parsed_date:
                        return {
                            "error": "Invalid date format, expected YYYY-MM-DD or DD/MM/YYYY"
                        }, 400
                    value = parsed_date

                if field in candidate_fields and hasattr(candidate, field):
                    setattr(candidate, field, value)

            # Mark enrollment completed
            user.enrollment_completed = True

            # Commit both candidate and user updates atomically
            db.session.commit()

            # Log the enrollment completion
            AuditService.log(user_id=user.id, action="candidate_enrollment_completed")

            return {
                "message": "Enrollment completed successfully",
                "candidate": candidate.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to save enrollment: {str(e)}"}, 500
