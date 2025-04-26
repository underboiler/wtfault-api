from flask import Flask, request, jsonify
import os
import base64
import traceback
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ✅ Your OpenAI API key (use Render environment variables)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

@app.route("/", methods=["GET"])
def index():
    return "✅ WTFault API is live."

# ✅ For structured TEXT jobs (VIN, DTCs, PIDs typed manually)
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

Extracted OCR Text from Image or Screenshot:
{ocr_text_block}

---
Please provide:
- Detailed fault analysis
- Suggested tests
- Recommended repairs
- Any extra expert tips

IMPORTANT: Write full paragraphs, not just headings.
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

# ✅ For IMAGE jobs (screenshots, photos uploaded)
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        image = request.files['image']
        registration = request.form.get('registration', 'UNKNOWN-REG')
        notes = request.form.get('notes', '')

        # Read image file and encode to Base64
        image_bytes = image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        prompt_text = f"""
Analyze this automotive diagnostic screenshot.
Registration: {registration}
Notes: {notes}

Extract:
- Vehicle VIN
- All DTC fault codes
- Any live sensor readings
- Summary of possible issues and recommended actions.

Format your reply cleanly.
"""

        # Send to GPT-4V
        response = client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image", "image": {"base64": image_base64}}
                    ]
                }
            ],
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        # Now parse simple fields out of result (optional basic parsing)
        vin_guess = "UNKNOWN"
        dtc_list = []
        live_data = {}

        lines = result_text.splitlines()
        for line in lines:
            line = line.strip()
            if len(line) == 17 and line.isalnum():
                vin_guess = line.upper()
            if line.upper().startswith(("P", "U", "C", "B")) and len(line) >= 5:
                dtc_list.append(line.upper())
            if ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    live_data[key] = value

        return jsonify({
            "vin": vin_guess,
            "dtcs": dtc_list,
            "live_data": live_data,
            "summary": result_text
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
