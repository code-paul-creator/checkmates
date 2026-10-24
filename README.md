# 🌿 KisanDristi — Pesticide Label Reader for Indian Farmers
**Hacktoberfest Hack Day · Problem Statement #5** — *Scan. Translate. Understand. Act.*

Pesticide labels are dense and often in English. KisanDristi reads a label photo with **Gemini 2.5 Flash** and explains the
**dose for a 15 L knapsack tank, waiting period and safety steps** in the farmer's own language, with voice readout and a
Kisan Mitra chat bot.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # paste your GEMINI_API_KEY (get one at aistudio.google.com)
python app.py             # http://localhost:5050
```
No key? The site still works in **demo mode** with a sample chlorpyrifos label.

## Features (v2)
Live camera scan · 7 languages with voice · tabbed result (Overview / Dose / Safety / Ask AI) · tank + whole-field (acre) dose calculator · safe-harvest date · icon-first PPE · spray-weather check (Open-Meteo, no key) · WhatsApp share · scan history · voice questions · helpline button

## Features (v1)
Multilingual UI (EN/हिं/मरा) · camera/upload · Gemini vision JSON extraction · tank-size dose calculator ·
toxicity colour band · 🔊 voice · AI chat · Kisan Call Centre 1800-180-1551 · Poison Centre 1800-116-117

## Safety
Always verify against the printed label. The API key stays server-side (`.env` is git-ignored).

## Contribute
PRs welcome — more languages, more crops, offline mode. Licensed MIT.

## Hero video
Add a short muted clip of a farmer spraying a field as `static/hero.mp4` (10–20 s, 1080p, under ~8 MB). Free sources: Pexels, Pixabay. `static/hero.jpg` is the poster/fallback.

## Hero video
Drop a short looping clip of a farmer spraying a field at `static/hero.mp4` (H.264, 1080p, ≤10 MB, no audio needed).
Free stock sources: Pexels and Pixabay — search "farmer spraying pesticide". Until it exists, `static/hero.jpg` is shown.

## Using the camera
"Scan with camera" opens a live viewfinder (needs `localhost` or HTTPS; on a phone over plain HTTP it falls back to the
phone's camera app). The photo is resized to 1600 px, sent to `/api/analyze`, and read by Gemini. Without a key the page shows
a clearly-marked sample instead of your photo.
