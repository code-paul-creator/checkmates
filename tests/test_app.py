import io, json, sys, os, types as pytypes
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
from PIL import Image
import app as A

class FakeResp:
    def __init__(self, t): self.text = t

class FakeModels:
    def __init__(self): self.calls, self.reply = 0, None
    def generate_content(self, **kw):
        self.calls += 1
        r = self.reply
        if isinstance(r, Exception): raise r
        return FakeResp(r)

class FakeTypes:
    class Part:
        @staticmethod
        def from_bytes(data, mime_type): return (len(data), mime_type)
    GenerateContentConfig = staticmethod(lambda **k: k)
    ThinkingConfig = staticmethod(lambda **k: k)
    HttpOptions = staticmethod(lambda **k: k)

@pytest.fixture
def env(monkeypatch):
    m = FakeModels()
    monkeypatch.setattr(A, "client", pytypes.SimpleNamespace(models=m))
    monkeypatch.setattr(A, "types", FakeTypes)
    monkeypatch.setattr(A, "GEMINI_RETRIES", 1)
    monkeypatch.setattr(A.time, "sleep", lambda s: None)
    A.cache.d.clear(); A.limiter.hits.clear()
    return A.app.test_client(), m

def jpg(size=(3000, 2000)):
    b = io.BytesIO(); Image.new("RGB", size, "green").save(b, "JPEG"); return b.getvalue()

GOOD = json.dumps({"is_label": True, "product": "Chlorpyrifos", "toxicity_color": "RED",
    "dose_per_litre_ml": "2.5 ml", "waiting_days": 15, "ppe_codes": ["gloves", "hack", "gloves"],
    "warnings": ["a"] * 9, "summary": "ok"})

def post(c, data=None, lang="hi"):
    return c.post("/api/analyze", data={"image": (io.BytesIO(data), "x.jpg"), "lang": lang},
                  content_type="multipart/form-data")

def test_status_and_health(env):
    c, _ = env
    assert c.get("/api/status").json["live"] is True
    assert c.get("/healthz").json["ok"]
    assert c.get("/").status_code == 200

def test_analyze_normalises(env):
    c, m = env; m.reply = "```json\n" + GOOD + "\n```"
    r = post(c, jpg()); j = r.json
    assert r.status_code == 200
    assert j["toxicity_color"] == "red" and j["dose_per_litre_ml"] == 2.5
    assert j["ppe_codes"] == ["gloves"] and len(j["warnings"]) == 4

def test_cache(env):
    c, m = env; m.reply = GOOD
    post(c, jpg()); post(c, jpg())
    assert m.calls == 1

def test_rejects_non_image(env):
    c, _ = env
    assert post(c, b"<html>not an image</html>").status_code == 415

def test_no_image_and_too_large(env):
    c, _ = env
    assert c.post("/api/analyze", data={}).json["error"] == "no_image"
    A.app.config["MAX_CONTENT_LENGTH"] = 1000
    try:
        assert post(c, jpg()).status_code == 413
    finally:
        A.app.config["MAX_CONTENT_LENGTH"] = A.MAX_UPLOAD

def test_retry_then_fail(env):
    c, m = env; m.reply = RuntimeError("503 overloaded")
    r = post(c, jpg())
    assert r.status_code == 502 and r.json["error"] == "gemini_failed" and m.calls == 2

def test_bad_json_from_model(env):
    c, m = env; m.reply = "sorry I cannot"
    assert post(c, jpg()).status_code == 502

def test_not_a_label_not_cached(env):
    c, m = env; m.reply = json.dumps({"is_label": False})
    assert post(c, jpg()).json["is_label"] is False
    assert len(A.cache.d) == 0

def test_chat(env):
    c, m = env; m.reply = "Use 2 ml."
    r = c.post("/api/chat", json={"q": "how much?", "lang": "en", "label": {"product": "X"}})
    assert r.json["answer"] == "Use 2 ml."
    assert c.post("/api/chat", json={"q": " "}).status_code == 400
    assert c.post("/api/chat", data="garbage", content_type="text/plain").status_code == 400

def test_rate_limit(env, monkeypatch):
    c, m = env; m.reply = "ok"
    monkeypatch.setattr(A.limiter, "limit", 3)
    codes = [c.post("/api/chat", json={"q": "hi"}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]

def test_no_key(monkeypatch):
    monkeypatch.setattr(A, "client", None)
    A.limiter.hits.clear()
    assert A.app.test_client().post("/api/chat", json={"q": "x"}).status_code == 503

def test_security_headers(env):
    c, _ = env
    r = c.get("/api/status")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and "X-Request-ID" in r.headers
