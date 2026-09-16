from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

DND_API = "https://www.dnd5eapi.co/api/spells/"
HF_API = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

def query_huggingface(prompt):
    response = requests.post(HF_API, headers=HF_HEADERS, json={"inputs": prompt})
    try:
        return response.json()[0]["generated_text"]
    except:
        return "I could not generate a response."

def get_spell_info(spell_name):
    spell_name = spell_name.lower().replace(" ", "-")
    url = DND_API + spell_name
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json()
    out = {
        "name": data.get("name"),
        "level": data.get("level"),
        "school": data.get("school", {}).get("name"),
        "casting_time": data.get("casting_time"),
        "range": data.get("range"),
        "duration": data.get("duration"),
        "desc": "\n".join(data.get("desc", []))
    }
    return out

@app.route("/ask", methods=["POST"])
def ask():
    content = request.json.get("question", "")

    # Detect spell queries
    if "spell" in content.lower() or "d&d" in content.lower():
        words = content.lower().split()
        for w in words:
            spell = get_spell_info(w)
            if spell:
                return jsonify({
                    "response": (
                        f"**{spell['name']}** (Level {spell['level']} {spell['school']} spell)\n"
                        f"**Casting Time:** {spell['casting_time']}\n"
                        f"**Range:** {spell['range']}\n"
                        f"**Duration:** {spell['duration']}\n\n"
                        f"**Description:**\n{spell['desc']}"
                    )
                })

    # Otherwise use AI model
    ai_response = query_huggingface(content)
    return jsonify({"response": ai_response})

@app.route("/", methods=["GET"])
def home():
    return "AI Agent Online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
