from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/analyze-job", methods=["POST"])
def analyze_job():
    try:
        data = request.get_json()
        vin = data.get("vin", "")
        reg = data.get("reg", "")
        dtcs = data.get("dtcs", [])
        pids = data.get("pids", {})
        notes = data.get("notes", "")

        dtc_block = "\n".join(f"- {code}" for code in dtcs) if dtcs else "None"
        pid_block = "\n".join(f"{k}: {v}" for k, v in pids.items()) if pids else "None"
        notes_text = notes if notes.strip() else "None"

        prompt = f"""
WTFault AI Diagnostic Request
------------------------------
VIN: {vin}
REG: {reg}

❗ Fault Codes:
{dtc_block}

📊 Live Sensor Data:
{pid_block}

📝 Notes:
{notes_text}

---
Please provide:
- Root cause analysis
- Testing suggestions
- Common fixes or procedures
"""

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        result = response.choices[0].message.content.strip()
        return jsonify({"result": result})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
