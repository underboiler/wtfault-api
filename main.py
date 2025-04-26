from flask import Flask, request, jsonify, send_from_directory
import os
import time
import traceback
from flask_cors import CORS
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure OpenAI API
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Setup upload directory
UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Serve static files (uploaded images)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Health check route
@app.route("/", methods=["GET"])
def index():
    return "✅ WTFault API is live."

# Text-based job (VIN, DTCs, PIDs from app)
@app.route("/analyze-job", methods=["POST"])
def analyze_job():
    try:
        data = request.get_json()
        vin = data.get("vin", "")
        reg = data.get("reg", "")
        dtcs = data.get("dtcs", [])
        pids = data.get("pids", {})
        notes = data.get("notes", "")
        ocr_text = data.get("ocr_text", "")

        dtc_block = "\n".join(f"- {code}" for code in dtcs) if dtcs else "None"
        pid_block = "\n".join(f"{k}: {v}" for k, v in pids.items()) if pids else "None"
        notes_text = notes if notes.strip() else "None"
        ocr_text_block = ocr_text if ocr_text.strip() else "None"

        prompt = f"""
You are a professional vehicle diagnostics AI for WTFault app.

VIN: {vin}
Registration: {reg}

Fault Codes:
{dtc_block}

Live Sensor Data:
{pid_block}

Technician Notes:
{notes_text}

Extracted OCR Text:
{ocr_text_block}

---
Please provide a full detailed diagnosis, suggested tests, repair advice, and extra expert tips.
IMPORTANT: Write complete paragraphs, not just headings.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )

        result = response.choices[0].message.content.strip()
        return jsonify({"result": result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Image-based job (screenshots/photos)
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        image = request.files['image']
        registration = request.form.get('registration', 'UNKNOWN-REG')
        notes = request.form.get('notes', '')

        # Save uploaded image to /static/ with unique filename
        timestamp = int(time.time())
        filename = f"snap_{timestamp}_{image.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)

        # Build public URL to uploaded image
        server_base_url = "https://wtfault-api.onrender.com"
        image_url = f"{server_base_url}/static/{filename}"

        prompt_text = f"""
Analyze this uploaded automotive diagnostic screenshot.

Registration: {registration}
Technician Notes: {notes}

Extract and clearly explain:
- VIN (Vehicle Identification Number)
- DTC fault codes (Diagnostic Trouble Codes)
- Live sensor data readings
- A full summary of possible root causes and recommended actions.

Respond in full sentences and organized sections.
"""

        # Send to OpenAI with image_url
        response = client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        return jsonify({"result": result_text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Start server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
