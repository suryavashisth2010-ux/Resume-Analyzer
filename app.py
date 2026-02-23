from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import PyPDF2
import os
import requests
import time
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------- CONFIG ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------- PDF TEXT EXTRACTION ----------------
def extract_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip() or "No readable text found in resume."
    except Exception as e:
        print("PDF ERROR:", e)
        return "Failed to read resume."

# ---------------- FRONTEND ROUTES ----------------
@app.route("/")
def index():
    return
    render_template("index.html")
# ---------------- ANALYZE ROUTE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("resume")
        job_type = request.form.get("jobType", "General")

        if not file:
            return jsonify({"error": "No resume uploaded"}), 400

        resume_text = extract_text(file)

        prompt = f"""
You are a professional career coach.

The user applied for the role of {job_type}.
You have carefully read their resume below.

Resume:
{resume_text}

Please respond like a human:
- Start by acknowledging the resume
- Highlight strengths
- Suggest improvements
- Provide actionable advice
- Keep tone friendly and professional
"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 10000
            }
        }

        headers = {"Content-Type": "application/json"}

        # List of models found to be available for this API Key
        available_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite-001"
        ]

        last_error = None
        result = None

        for model in available_models:
            print(f"--- Attempting with model: {model} ---")
            CURRENT_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            
            # Robust Retry loop per model
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = requests.post(
                        f"{CURRENT_API_URL}?key={GEMINI_API_KEY}",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"SUCCESS with {model}")
                        break
                    elif response.status_code == 429:
                        wait_time = (attempt + 1) * 2
                        print(f"Rate limited (429) on {model}. Retry {attempt+1}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        last_error = f"429 on {model}"
                        continue
                    elif response.status_code == 404:
                        print(f"Not Found (404) for {model}")
                        last_error = f"404 on {model}"
                        break # Go to next model immediately
                    else:
                        print(f"Status {response.status_code} for {model}")
                        last_error = f"Status {response.status_code} on {model}"
                        break # Try next model
                except Exception as e:
                    print(f"Connection Error on {model}: {e}")
                    last_error = str(e)
                    break 
            
            if result:
                break
        
        if not result:
             raise Exception(f"All model attempts exhausted. Final failure: {last_error}")

        # Extract feedback
        try:
            feedback = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            feedback = ""
        if not feedback:
            return jsonify({"error": "AI returned empty feedback"}), 500

        return jsonify({"feedback": feedback})

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
             return jsonify({"error": "Rate limit exceeded. Please wait a minute and try again."}), 429
        print("GEMINI / SERVER ERROR:", e)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print("GEMINI / SERVER ERROR:", e)
        return jsonify({"error": str(e)}), 500

