import re
import os
from dotenv import load_dotenv
from openai import OpenAI
from app.models import Requisition
from cloudinary.uploader import upload as cloudinary_upload

load_dotenv()

# OpenRouter API configuration
api_key = os.getenv("OPENROUTER_API_KEY")
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "http://localhost:5000"}
)

class HybridResumeAnalyzer:
    @staticmethod
    def upload_cv(file):
        """Upload resume to Cloudinary."""
        try:
            result = cloudinary_upload(
                file,
                resource_type="raw",
                folder="candidate_cvs"
            )
            return result.get("secure_url")
        except Exception as e:
            print("Cloudinary Upload Error:", e)
            return None

    @staticmethod
    def analyse_resume(resume_content, job_id):
        """
        Analyse resume text against the job description.
        FIXES:
        - Prevents OOM by limiting text size.
        - Uses a fast OpenRouter model.
        - Prevents worker timeout.
        """
        # Ensure resume is string
        if isinstance(resume_content, bytes):
            resume_content = resume_content.decode(errors="ignore")

        # ----------- Prevent OOM / Timeouts -----------
        resume_content = (resume_content or "")[:8000]          # limit 8k chars
        job = Requisition.query.get(job_id)

        if not job:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": "Job not found"
            }

        job_description = (job.description or "")[:4000]        # limit 4k chars

        # ----------- AI Prompt -----------
        prompt = f"""
Resume:
{resume_content}

Job Description:
{job_description}

Task:
- Analyze the resume against the job description.
- Give a match score out of 100.
- Highlight missing skills or experiences.
- Suggest improvements.

Return in format:
Match Score: XX/100
Missing Skills:
- ...
Suggestions:
- ...
"""

        try:
            # ----------- Stable Fast Model -----------
            response = openai_client.chat.completions.create(
                model="google/gemini-2.0-flash-lite-preview",  # FAST & lightweight
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI recruitment assistant. Return results ONLY in the required format."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )

            text = response.choices[0].message.content or ""

            # ----------- Parsing -----------
            score_match = re.search(r"(\d{1,3})(?:/100|%)", text)
            match_score = int(score_match.group(1)) if score_match else 0

            missing_skills_match = re.search(
                r"Missing Skills:\s*(.*?)(?:Suggestions:|$)",
                text,
                re.DOTALL
            )
            missing_skills = []
            if missing_skills_match:
                skills_text = missing_skills_match.group(1)
                missing_skills = [
                    line.strip("- ").strip()
                    for line in skills_text.strip().splitlines()
                    if line.strip()
                ]

            suggestions_match = re.search(
                r"Suggestions:\s*(.*)",
                text,
                re.DOTALL
            )
            suggestions = []
            if suggestions_match:
                suggestions_text = suggestions_match.group(1)
                suggestions = [
                    line.strip("- ").strip()
                    for line in suggestions_text.strip().splitlines()
                    if line.strip()
                ]

            return {
                "match_score": match_score,
                "missing_skills": missing_skills,
                "suggestions": suggestions,
                "raw_text": text
            }

        except Exception as e:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": f"Error during analysis: {str(e)}"
            }
