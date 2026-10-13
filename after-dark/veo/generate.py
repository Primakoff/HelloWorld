"""Generate After Dark shots with Google Veo (Gemini API) from a photo of the costumed dancers.

Reads the API key from the GEMINI_API_KEY environment variable (set it as an environment
secret, never in code or chat).

usage:
  python3 generate.py models                       # list Veo models this key can use
  python3 generate.py run <photo> <out_dir> [model] # render every shot in SHOTS
"""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
KEY = os.environ.get("GEMINI_API_KEY", "")

STYLE = ("Dark Ukrainian folk-horror ritual on a black theatre stage. Performers in torn, ash-grey "
         "linen rags and white cracked plaster masks shaped like a spiked sun, a crescent moon, a "
         "five-point star and a bird beak, half human, half mythical creature. One hard spotlight "
         "from above, drifting smoke, wet black floor with reflections, desaturated sepia and grey "
         "grade with a deep red accent light, 35mm film grain, shallow depth of field, cinematic.")

# choreography taken from the rehearsal: rising arms, wing spread, collapse to the floor,
# animal crouch with clawed hands, explosive lunge
SHOTS = [
    ("01_awakening", "Very slow push-in. The masked figures stand frozen in the dark, then one by one "
     "lift their heads and slowly raise their arms overhead; rags tremble; the spotlight flickers on."),
    ("02_wings", "Medium shot circling slowly around the group. They spread their arms wide like wings "
     "and sway together in a hypnotic ritual; dust floats in the beam; giant shadows move on the wall."),
    ("03_collapse", "Sudden movement: the figures fold to the floor, crouching like animals with clawed "
     "hands, heads jerking in unnatural stop-motion twitches; red light rises from the floor."),
    ("04_lunge", "Low angle. The creatures explode upward in wide lunges toward the camera, rags flying, "
     "white flashes of light, then everything cuts to black."),
]
NEGATIVE = "cartoon, anime, bright colors, daylight, gore, blood, smiling faces, text, captions, watermark, modern clothing"


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, headers={"x-goog-api-key": KEY, "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body else None)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def list_models():
    models = call("GET", f"{API}/models?pageSize=200").get("models", [])
    return [m["name"].split("/")[-1] for m in models if "veo" in m["name"]]


def generate(photo, prompt, model, out_path):
    mime = mimetypes.guess_type(photo)[0] or "image/png"
    img = base64.b64encode(open(photo, "rb").read()).decode()
    body = {"instances": [{"prompt": f"{prompt} {STYLE}", "image": {"bytesBase64Encoded": img, "mimeType": mime}}],
            "parameters": {"aspectRatio": "16:9", "negativePrompt": NEGATIVE}}
    op = call("POST", f"{API}/models/{model}:predictLongRunning", body)
    while not op.get("done"):
        time.sleep(15)
        op = call("GET", f"{API}/{op['name']}")
    if "error" in op:
        raise RuntimeError(op["error"])
    samples = op["response"]["generateVideoResponse"]["generatedSamples"]
    req = urllib.request.Request(samples[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
    with urllib.request.urlopen(req, timeout=300) as r, open(out_path, "wb") as f:
        f.write(r.read())


if __name__ == "__main__":
    if not KEY:
        sys.exit("GEMINI_API_KEY is not set")
    if sys.argv[1] == "models":
        print("\n".join(list_models()))
    else:
        photo, out = sys.argv[2], sys.argv[3]
        model = sys.argv[4] if len(sys.argv) > 4 else sorted(list_models())[-1]
        os.makedirs(out, exist_ok=True)
        for name, prompt in SHOTS:
            path = f"{out}/{name}.mp4"
            if os.path.exists(path):
                continue
            print("generating", name, "with", model, flush=True)
            generate(photo, prompt, model, path)
            print("saved", path, flush=True)
