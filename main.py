from flask import Flask, request, jsonify
import os
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

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
You are a professional vehicle diagnostics AI for WTFault app.

VIN: {vin}
Registration: {reg}

Fault Codes:
{dtc_block}

Live Sensor Data:
{pid_block}

Technician Notes:
{notes_text}

---
Now, please provide a FULL detailed diagnostic analysis including:
- Root cause explanation (not just a heading)
- Suggested tests
- Possible repairs
- Extra tips if applicable

IMPORTANT: Do not just list headings. Write full paragraphs for each section.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )

        result = response.choices[0].message.content.strip()
        return jsonify({"result": result})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
