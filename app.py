"""KisanDristi – Pesticide Label Reader for Indian Farmers (Flask + Gemini 2.5 Flash)."""
import json, os, re
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()
app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LANGS = {"en": "English", "hi": "Hindi", "mr": "Marathi", "pa": "Punjabi", "gu": "Gujarati", "ta": "Tamil", "te": "Telugu"}

client = types = None
if KEY:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=KEY)

SYSTEM = ("You are Kisan Mitra, a careful agronomy assistant for small Indian farmers. Use very simple words and short sentences. "
          "Never invent label facts: if something is not printed on the label, say 'not on label' or use null. "
          "Never approve tank-mixes the label does not list. For poisoning or unsafe situations tell the person to call the "
          "Kisan Call Centre 1800-180-1551 or the National Poisons Information Centre 1800-116-117.")

def cfg(**kw):
    # thinking off = faster answers for simple extraction
    return types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0), **kw)

def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    return json.loads(text)

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.get("/api/status")
def status():
    return jsonify(live=bool(client), model=MODEL)

@app.post("/api/analyze")
def analyze():
    if not client:
        return jsonify(error="no_key"), 503
    f = request.files.get("image")
    if not f:
        return jsonify(error="no_image"), 400
    lang = LANGS.get(request.form.get("lang", "hi"), "Hindi")
    prompt = (f"{SYSTEM}\nLook at this photo. Reply ONLY with JSON. Write all text values in {lang} (keep numbers as digits). Keys:\n"
              "is_label (true only if it shows a pesticide/agrochemical product label), product, active_ingredient, "
              "toxicity_color (red|yellow|blue|green from the colour band/triangle, else null), crop, pest, "
              "dose_per_litre_ml (number = ml or g per 1 litre of water; convert from per-acre/per-pump if printed, else null), "
              "dose_note (one short line of the dose exactly as printed), waiting_days (number or null), "
              "ppe_codes (array using ONLY these codes that the label asks for: gloves, mask, goggles, boots, sleeves, wash, no_eat, keep_children, no_wind), "
              "warnings (array of up to 4 short strings), "
              "summary (3 simple sentences to be read aloud).")
    try:
        r = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_bytes(data=f.read(), mime_type=f.mimetype or "image/jpeg"), prompt],
            config=cfg(response_mime_type="application/json", temperature=0.1))
        data = parse_json(r.text)
        if isinstance(data, list):
            data = data[0] if data else {}
        return jsonify(data)
    except Exception as e:
        return jsonify(error="gemini_failed", detail=str(e)[:160]), 502

@app.post("/api/chat")
def chat():
    if not client:
        return jsonify(error="no_key"), 503
    b = request.get_json(force=True, silent=True) or {}
    lang = LANGS.get(b.get("lang", "hi"), "Hindi")
    prompt = (f"{SYSTEM}\nAnswer in {lang}, at most 4 short sentences.\n"
              f"Label facts: {json.dumps(b.get('label') or {}, ensure_ascii=False)}\nFarmer asks: {str(b.get('q', ''))[:500]}")
    try:
        r = client.models.generate_content(model=MODEL, contents=prompt, config=cfg(temperature=0.3))
        return jsonify(answer=r.text)
    except Exception as e:
        return jsonify(error="gemini_failed", detail=str(e)[:160]), 502

if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", 5050)), debug=True)
