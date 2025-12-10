import os
import re
import logging
from dotenv import load_dotenv
from openai import OpenAI
from cloudinary.uploader import upload as cloudinary_upload
import fitz  # PyMuPDF
from app.models import Requisition

# ----------------------------
# Environment & Logging Setup
# ----------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# Hybrid Resume Analyzer Class
# ----------------------------
class HybridResumeAnalyzer:
    def __init__(self):
        # --- OpenRouter AI client ---
        api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_client = None
        if api_key:
            try:
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                    default_headers={"HTTP-Referer": "http://localhost:5000"}
                )
                logger.info("OpenRouter client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client: {e}")

    # ----------------------------
    # Cloudinary Upload
    # ----------------------------
    @staticmethod
    def upload_cv(file):
        """Upload CV to Cloudinary and return secure URL."""
        try:
            result = cloudinary_upload(
                file,
                resource_type="raw",
                folder="candidate_cvs"
            )
            return result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return None

    # ----------------------------
    # PDF Text Extraction
    # ----------------------------
    @staticmethod
    def extract_pdf_text(file):
        """Extract text from PDF file stream."""
        try:
            file.stream.seek(0)
            pdf_doc = fitz.open(stream=file.stream.read(), filetype="pdf")
            text = ""
            for page in pdf_doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    # ----------------------------
    # OpenRouter Online Analysis
    # ----------------------------
    def analyse_online(self, resume_content, job_description):
        """Analyse resume using OpenRouter API."""
        if not self.openai_client:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": "OpenRouter client not initialized"
            }

        prompt = f"""
Resume:
{resume_content}

Job Description:
{job_description}

Task:
- Compare the resume to the job description.
- Return a match score out of 100.
- List missing skills.
- Suggest improvements.

Format strictly:
Match Score: XX/100
Missing Skills:
- skill1
- skill2
Suggestions:
- suggestion1
- suggestion2
"""
        try:
            response = self.openai_client.chat.completions.create(
                model="openrouter/auto",
                messages=[
                    {"role": "system", "content": "You are an AI recruitment assistant. Return only the required format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                request_timeout=10
            )

            text = getattr(response.choices[0].message, "content", "") or ""

            # Parse match score
            score_match = re.search(r"(\d{1,3})(?:/100|%)", text)
            match_score = int(score_match.group(1)) if score_match else 0

            # Parse missing skills
            missing_skills = []
            ms_match = re.search(r"Missing Skills:\s*(.*?)(?:Suggestions:|$)", text, re.DOTALL)
            if ms_match:
                for line in ms_match.group(1).strip().splitlines():
                    line = line.strip()
                    if line.startswith("-"):
                        missing_skills.append(line[1:].strip())

            # Parse suggestions
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
            logger.error(f"Online analysis failed: {e}")
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": f"Error during OpenRouter analysis: {str(e)}"
            }

    # ----------------------------
    # Full Upload + Analyse Pipeline
    # ----------------------------
    def upload_and_analyse(self, file, job_id):
        """Upload resume to Cloudinary and analyse via OpenRouter (PDF supported)."""
        # --- Extract text if PDF ---
        resume_text = ""
        if file.filename.lower().endswith(".pdf"):
            resume_text = self.extract_pdf_text(file)
        else:
            # For other formats, assume plain text uploaded via form
            resume_text = getattr(file, "read", lambda: b"")().decode("utf-8", errors="ignore")

        # --- Upload to Cloudinary ---
        cv_url = self.upload_cv(file)
        if not cv_url:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": "Failed to upload resume"
            }

        # --- Get job description ---
        job = Requisition.query.get(job_id)
        if not job:
            return {
                "match_score": 0,
                "missing_skills": [],
                "suggestions": [],
                "raw_text": "Job not found",
                "cv_url": cv_url
            }

        job_description = job.description or ""

        # --- Analyse via OpenRouter ---
        analysis = self.analyse_online(resume_text, job_description)
        analysis["cv_url"] = cv_url
        return analysis
