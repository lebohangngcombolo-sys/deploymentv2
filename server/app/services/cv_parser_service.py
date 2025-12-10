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
    default_headers={"HTTP-Referer": "https://willowy-scone-c14f7c.netlify.app/"}
)


class HybridResumeAnalyzer:

    @staticmethod
    def upload_cv(file):
        """
        Upload resume file to Cloudinary and return secure URL.
        """
        try:
            result = cloudinary_upload(
                file,
                folder="candidate_cvs",
                resource_type="raw"
            )
            return result.get("secure_url")
        except Exception as e:
            print("Cloudinary Upload Error:", str(e))
            return None

    @staticmethod
    def analyse_resume(resume_content, job_id):
        """
        Analyse resume against job description and return:
        match_score, missing_skills, suggestions, raw_text
        """

        # Fetch job
        job = Requisition.query.get(job_id)
        if not job:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": "Job not found"
            }

        job_description = job.description or ""

        # -----------------------------
        # Optimized Prompt
        # -----------------------------
        prompt = f"""
You are an AI recruitment assistant. Compare the resume to the job description.
Return ONLY the following sections:

Match Score: XX/100
Missing Skills:
- item
Suggestions:
- item

Resume:
{resume_content}

Job Description:
{job_description}
"""

        try:
            # -----------------------------
            # Optimized API call
            # -----------------------------
            response = openai_client.chat.completions.create(
                model="openrouter/auto",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
                timeout=30  # HARD STOP (prevents Gunicorn killing worker)
            )

            text = response.choices[0].message.content or ""

            # -----------------------------
            # Parsing
            # -----------------------------

            # Score (e.g., 75/100 or 75%)
            score_match = re.search(r"(\d{1,3})(?:/100|%)", text)
            match_score = min(int(score_match.group(1)), 100) if score_match else 0

            # Missing Skills
            missing_skills = []
            ms_match = re.search(r"Missing Skills:\s*(.*?)(?:Suggestions:|$)", text, re.DOTALL)
            if ms_match:
                for line in ms_match.group(1).strip().splitlines():
                    line = line.strip()
                    if line.startswith("-"):
                        missing_skills.append(line[1:].strip())

            # Suggestions
            suggestions = []
            sug_match = re.search(r"Suggestions:\s*(.*)", text, re.DOTALL)
            if sug_match:
                for line in sug_match.group(1).strip().splitlines():
                    line = line.strip()
                    if line.startswith("-"):
                        suggestions.append(line[1:].strip())

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
