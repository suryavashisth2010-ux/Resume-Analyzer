from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import PyPDF2
import os
import requests
import time
import json

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")

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
    return render_template("index.html")

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
You are a professional career coach and ATS (Applicant Tracking System) expert.

The user applied for the role of: {job_type}.
Analyze their resume carefully.

Resume:
{resume_text}

Provide your analysis in STRICT JSON format with the following keys:
- "ats_score": A number between 0 and 100 representing how well the resume matches the {job_type} role.
- "summary": A brief (3-4 sentences) professional summary highlighting the candidate's core value.
- "skills": A list of key professional skills detected in the resume.
- "improvements": A list of 5 actionable and specific tips to improve the resume for this role.

Ensure the response is ONLY valid JSON.
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

        # Verified list of available models for this specific API key
        available_models = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-pro-latest",
            "gemini-flash-latest",
            "gemini-2.5-flash"
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
                        last_error = f"429 on {model}: {response.text}"
                        continue
                    elif response.status_code == 403:
                        print(f"Permission Denied (403) for {model}. Check if API Key has 'Generative Language API' enabled.")
                        last_error = f"403 on {model}: {response.text}"
                        break
                    elif response.status_code == 404:
                        print(f"Not Found (404) for {model}")
                        last_error = f"404 on {model}: {response.text}"
                        break
                    else:
                        print(f"Status {response.status_code} for {model}: {response.text}")
                        last_error = f"Status {response.status_code} on {model}: {response.text}"
                        break
                except Exception as e:
                    print(f"Connection Error on {model}: {e}")
                    last_error = f"Exception on {model}: {str(e)}"
                    break 
            
            if result:
                break
        
        if not result:
             raise Exception(f"All model attempts exhausted. Final failure: {last_error}")

        # Extract feedback and parse JSON
        try:
            raw_feedback = result["candidates"][0]["content"]["parts"][0]["text"]
            # Clean possible markdown code blocks from response
            json_str = raw_feedback.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            feedback_data = json.loads(json_str.strip())
            return jsonify(feedback_data)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print("EXTRACTION/JSON ERROR:", e)
            print("RAW RESPONSE:", result)
            return jsonify({"error": "AI returned unusable data"}), 500

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
             return jsonify({"error": "Rate limit exceeded. Please wait a minute and try again."}), 429
        print("GEMINI / SERVER ERROR:", e)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print("GEMINI / SERVER ERROR:", e)
        return jsonify({"error": str(e)}), 500

