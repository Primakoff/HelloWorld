"""After Dark music-video render: dancers from rehearsal footage -> masked creatures on a dark ritual stage, 4K.

usage:
  python3 render.py <scratch> full            # whole clip, piped to ffmpeg
  python3 render.py <scratch> preview 40,200  # selected output frames as JPEG
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont

S = sys.argv[1]
MODE = sys.argv[2]
EDIT, ANA, MODELS, FONTS = f"{S}/edit", f"{S}/ana", f"{S}/models", f"{S}/fonts"
OUT_W, OUT_H, FPS = 3840, 2160, 30
CX0, CY0, CW, CH = 160, 40, 960, 540   # crop of the 1280x720 source, x4 = 4K
K = OUT_W / CW
FLOOR_Y = int((427 - CY0) * K)          # wall/floor line of the rehearsal hall
rng = np.random.default_rng(13)

# ---------------------------------------------------------------- timeline
SHOTS = [l.split() for l in open(f"{EDIT}/shots.txt").read().split("\n") if l.strip()]
frames = sorted(f for f in os.listdir(EDIT) if f.endswith(".png"))
timeline = []  # (shot, edit file or None, index within shot, shot length)
for name, *_ in SHOTS:
    fs = [f for f in frames if f.startswith(name + "_")]
    if name == "D":  # stop-motion jerk: hold every 7th frame for two extra frames
        held = []
        for i, f in enumerate(fs):
            held += [f] * (3 if i % 7 == 6 else 1)
        fs = held[: len(fs) + 10]
    for i, f in enumerate(fs):
        timeline.append((name, f, i, len(fs)))
TITLE_N = int(3.8 * FPS)
for i in range(TITLE_N):
    timeline.append(("T", None, i, TITLE_N))
N = len(timeline)
cut_frames = [i for i in range(1, N) if timeline[i][0] != timeline[i - 1][0]]
json.dump({"n": N, "fps": FPS, "cuts": cut_frames, "shots": [t[0] for t in timeline]}, open(f"{S}/timeline.json", "w"))

# ---------------------------------------------------------------- heads -> smoothed tracks
heads_raw = json.load(open(f"{ANA}/heads2.json" if os.path.exists(f"{ANA}/heads2.json") else f"{ANA}/heads.json"))
CROWNS = ["sun", "thorns", "moon", "antlers", "halo", "star"]


def head_geom(h):
    P = {k: np.array(v[:2]) for k, v in h.items()}
    V = {k: v[2] for k, v in h.items()}
    ears = V["lear"] > 0.3 and V["rear"] > 0.3
    c = (P["lear"] + P["rear"]) / 2 if ears else P["nose"]
    s = max(np.linalg.norm(P["lear"] - P["rear"]) if ears else 0,
            np.linalg.norm(P["leye"] - P["reye"]) * 2.4, 0.36 * np.linalg.norm(P["lsh"] - P["rsh"]))
    s = float(np.clip(s, 11, 34))
    sh = (P["lsh"] + P["rsh"]) / 2
    up = c - sh
    up = up / (np.linalg.norm(up) + 1e-6)
    face = V["nose"] > 0.6 and V["leye"] > 0.5 and V["reye"] > 0.5
    return dict(c=c, s=s, up=up, face=face, le=P["leye"], re=P["reye"], nose=P["nose"])


def build_tracks():
    """Greedy nearest-neighbour tracking per shot, then centred smoothing and gap filling."""
    tracks = {}
    for name, *_ in SHOTS:
        fs = [f for f in frames if f.startswith(name + "_")]
        live = []  # each: dict(frames={i: geom})
        for i, f in enumerate(fs):
            dets = [head_geom(h) for h in heads_raw.get(f, [])]
            used = set()
            for t in live:
                last_i = max(t["frames"])
                if i - last_i > 6:
                    continue
                lc = t["frames"][last_i]["c"]
                best, bd = None, 30.0
                for j, d in enumerate(dets):
                    dd = np.linalg.norm(d["c"] - lc)
                    if j not in used and dd < bd:
                        best, bd = j, dd
                if best is not None:
                    used.add(best)
                    t["frames"][i] = dets[best]
            for j, d in enumerate(dets):
                if j not in used:
                    live.append({"frames": {i: d}})
        out = []
        for t in live:
            idx = sorted(t["frames"])
            if len(idx) < 8:
                continue
            full = np.arange(idx[0], idx[-1] + 1)
            def interp(key, dim):
                return np.stack([np.interp(full, idx, [t["frames"][k][key][d] for k in idx]) for d in range(dim)], 1)
            c, up = interp("c", 2), interp("up", 2)
            le, re = interp("le", 2), interp("re", 2)
            s = np.interp(full, idx, [t["frames"][k]["s"] for k in idx])
            face = np.interp(full, idx, [float(t["frames"][k]["face"]) for k in idx])
            ker = np.ones(5) / 5
            sm = lambda a: np.stack([np.convolve(np.pad(a[:, d], 2, mode="edge"), ker, "valid") for d in range(a.shape[1])], 1)
            c, up, le, re = sm(c), sm(up), sm(le), sm(re)
            s = np.convolve(np.pad(s, 4, mode="edge"), np.ones(9) / 9, "valid")
            face = np.convolve(np.pad(face, 3, mode="edge"), np.ones(7) / 7, "valid")
            out.append(dict(start=int(full[0]), c=c, up=up, s=s, face=face, le=le, re=re, n=len(full),
                            mx=float(np.median(c[:, 0])), my=float(np.median(c[:, 1]))))
        # three pairs of dancers stand left / centre / right; each pair gets its own two crowns
        groups = {0: ["sun", "thorns"], 1: ["moon", "star"], 2: ["antlers", "halo"]}
        for tr in out:
            g = 0 if tr["mx"] < 470 else (1 if tr["mx"] < 760 else 2)
            peers = sorted({round(o["my"] / 25) for o in out if (0 if o["mx"] < 470 else (1 if o["mx"] < 760 else 2)) == g})
            tr["crown"] = groups[g][min(1, peers.index(round(tr["my"] / 25)))]
        tracks[name] = out
    return tracks


TRACKS = build_tracks()

# ---------------------------------------------------------------- static layers
yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


BEAM_X, BEAM_TOP = OUT_W * 0.5, -500.0
beam_half = 260 + (yy - BEAM_TOP) / (OUT_H - BEAM_TOP) * 1500
beam = np.clip(1 - np.abs(xx - BEAM_X) / beam_half, 0, 1) ** 1.6
beam *= smoothstep(-200, 900, yy)
pool = np.exp(-(((xx - BEAM_X) / 1750) ** 2 + ((yy - 1880) / 330) ** 2)) * (yy > FLOOR_Y - 40)
wall = (0.020 + 0.018 * (yy / OUT_H)) * (yy < FLOOR_Y)
floor = (0.012 + 0.03 * smoothstep(FLOOR_Y, OUT_H, yy)) * (yy >= FLOOR_Y)
horizon = np.exp(-((yy - FLOOR_Y) / 26) ** 2) * 0.05
vign = 1 - 0.85 * smoothstep(0.25, 1.15, np.sqrt(((xx - OUT_W / 2) / (OUT_W * 0.62)) ** 2 + ((yy - OUT_H * 0.48) / (OUT_H * 0.7)) ** 2))
red_floor = smoothstep(OUT_H * 0.45, OUT_H, yy) * (0.4 + 0.6 * smoothstep(0, 1, np.abs(xx - BEAM_X) / (OUT_W * 0.5)))
light_on_dancer = (0.42 + 0.55 * np.clip(1 - np.abs(xx - BEAM_X) / (beam_half * 1.1), 0, 1)) * (1.05 - 0.45 * smoothstep(300, OUT_H, yy))


def fbm(h, w, octaves=5, seed=0):
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, h >> (octaves - o)), max(2, w >> (octaves - o))
        acc += amp * cv2.resize(r.random((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.55
    return acc / tot


HAZE = fbm(540, 960 * 2, seed=3)   # scrolled sideways for drifting smoke
WOBBLE = fbm(135, 240 * 2, octaves=4, seed=9)

# dust motes in the beam
ND = 650
dust_x = rng.normal(BEAM_X, 700, ND)
dust_y = rng.uniform(0, OUT_H, ND)
dust_r = rng.uniform(1.2, 4.5, ND)
dust_v = rng.uniform(-1.2, 0.6, ND)
dust_b = rng.uniform(0.15, 0.9, ND)

# ---------------------------------------------------------------- super resolution
so = ort.SessionOptions()
so.intra_op_num_threads = int(os.environ.get("SR_THREADS", os.cpu_count()))
SR = ort.InferenceSession(f"{MODELS}/realesr-x4v3.onnx", so, providers=["CPUExecutionProvider"])


def super_res(crop_bgr):
    x = np.ascontiguousarray(crop_bgr[..., ::-1].transpose(2, 0, 1)[None]).astype(np.float32) / 255
    y = SR.run(None, {"input": x})[0][0]
    return np.clip(y.transpose(1, 2, 0)[..., ::-1], 0, 1)


def static_masks():
    """Pixels the segmenter keeps for a whole shot without any change in brightness are furniture, not dancers."""
    out = {}
    for name, *_ in SHOTS:
        fs = [f for f in frames if f.startswith(name + "_")]
        ms = np.stack([cv2.imread(f"{ANA}/{f}", cv2.IMREAD_GRAYSCALE) > 110 for f in fs]).mean(0)
        g = np.stack([cv2.cvtColor(cv2.imread(f"{EDIT}/{f}"), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in fs])
        out[name] = ((ms > 0.8) & (g.std(0) < 7)).astype(np.uint8)
    # dancers holding still in one shot look static too, so only keep what is static in 4 of 5 shots
    votes = sum(cv2.dilate(v, np.ones((13, 13), np.uint8)).astype(np.int32) for v in out.values())
    furniture = cv2.dilate((votes >= len(out) - 1).astype(np.uint8), np.ones((5, 5), np.uint8))
    for name in out:
        st = cv2.dilate(out[name], np.ones((7, 7), np.uint8)) & furniture
        st[280:] = 0  # the table behind the dancers stays as a dark altar; only wall fixtures go
        out[name] = cv2.GaussianBlur(st.astype(np.float32), (0, 0), 2)
    return out


STATIC = static_masks()


def dancer_layer(fname):
    src = cv2.imread(f"{EDIT}/{fname}")[CY0:CY0 + CH, CX0:CX0 + CW]
    m = cv2.imread(f"{ANA}/{fname}", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    m = (m * (1 - STATIC[fname.split('_')[0]]))[CY0:CY0 + CH, CX0:CX0 + CW]
    # drop small islands (wall speakers, specks); dancers are always large connected blobs
    nlab, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0.3).astype(np.uint8), 8)
    keep = np.zeros(nlab, np.float32)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 900
    m = m * cv2.dilate(keep[lab], np.ones((5, 5), np.uint8))
    img = np.zeros((OUT_H, OUT_W, 3), np.float32)
    ys, xs = np.where(m > 0.15)
    if len(xs):
        x0, x1 = max(0, xs.min() - 12), min(CW, xs.max() + 13)
        y0, y1 = max(0, ys.min() - 12), min(CH, ys.max() + 13)
        img[int(y0 * K):int(y1 * K), int(x0 * K):int(x1 * K)] = super_res(src[y0:y1, x0:x1])
    a = cv2.resize(m, (OUT_W, OUT_H), interpolation=cv2.INTER_CUBIC)
    a = smoothstep(0.32, 0.7, a)
    a = cv2.GaussianBlur(a, (0, 0), 1.6)
    return img, a


# ---------------------------------------------------------------- crowns and masks
BONE = np.array([196, 206, 214], np.float32) / 255  # BGR, cold plaster
INK = np.array([22, 24, 28], np.float32) / 255


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def to4k(p):
    return np.array([(p[0] - CX0) * K, (p[1] - CY0) * K])


def draw_crown(lay, alpha, kind, c, up, s, t, seed):
    """c, s in 4K pixels; up = unit vector from shoulders to head (image coords)."""
    r = np.random.default_rng(seed)
    side = np.array([-up[1], up[0]])
    base = c + up * s * 0.25
    polys = []
    if kind == "sun":
        n = 15
        for k in range(n):
            ang = (k / (n - 1) - 0.5) * math.pi * 1.25
            d = rot(up, ang)
            L = s * (1.25 if k % 2 == 0 else 0.75) * (1 + 0.06 * math.sin(t * 0.21 + k))
            p0 = base + d * s * 0.55
            w = rot(d, math.pi / 2) * s * 0.075
            polys.append(np.array([p0 - w, base + d * (s * 0.55 + L), p0 + w]))
    elif kind == "thorns":
        for k in range(17):
            ang = r.uniform(-1.15, 1.15)
            d = rot(up, ang)
            L = s * r.uniform(0.7, 1.7)
            p0 = base + d * s * 0.45
            w = rot(d, math.pi / 2) * s * 0.035
            polys.append(np.array([p0 - w, base + d * (s * 0.45 + L) + side * r.uniform(-0.1, 0.1) * s, p0 + w]))
    elif kind == "antlers":
        for sgn in (-1, 1):
            p = base + side * sgn * s * 0.35
            d = rot(up, sgn * 0.45)
            for seg in range(4):
                q = p + d * s * 0.55
                polys.append(("line", p, q, max(2, int(s * 0.09))))
                tine = rot(d, -sgn * 0.9)
                polys.append(("line", q, q + tine * s * 0.42, max(2, int(s * 0.06))))
                p, d = q, rot(d, sgn * 0.28)
    elif kind == "moon":
        R = s * 1.35
        cc = base + up * s * 0.35
        a0 = math.atan2(side[1], side[0])
        outer = [cc + R * np.array([math.cos(a0 + math.pi + math.pi * i / 40), math.sin(a0 + math.pi + math.pi * i / 40)]) for i in range(41)]
        inner = [cc + side * R * 0.38 + R * 0.78 * np.array([math.cos(a0 + math.pi + math.pi * i / 40), math.sin(a0 + math.pi + math.pi * i / 40)]) for i in range(40, -1, -1)]
        polys.append(np.array(outer + inner))
    elif kind == "halo":
        polys.append(("ring", base + up * s * 0.2, s * 1.25, max(3, int(s * 0.16))))
        for k in range(24):
            d = rot(up, k / 24 * 2 * math.pi)
            p0 = base + up * s * 0.2 + d * s * 1.25
            polys.append(("line", p0, p0 + d * s * 0.32, max(2, int(s * 0.05))))
    elif kind == "star":
        cc = base + up * s * 0.75
        R, rr = s * 1.25, s * 0.48
        a0 = math.atan2(-up[1], -up[0]) + math.pi + 0.15 * math.sin(t * 0.05)
        pts = [cc + (R if i % 2 == 0 else rr) * np.array([math.cos(a0 + i * math.pi / 5), math.sin(a0 + i * math.pi / 5)]) for i in range(10)]
        polys.append(np.array(pts))
    for p in polys:
        if isinstance(p, tuple):
            if p[0] == "line":
                cv2.line(lay, tuple(np.int32(p[1] * 4)), tuple(np.int32(p[2] * 4)), BONE.tolist(), p[3], cv2.LINE_AA, shift=2)
                cv2.line(alpha, tuple(np.int32(p[1] * 4)), tuple(np.int32(p[2] * 4)), 1.0, p[3], cv2.LINE_AA, shift=2)
            else:
                cv2.circle(lay, tuple(np.int32(p[1] * 4)), int(p[2] * 4), BONE.tolist(), p[3], cv2.LINE_AA, shift=2)
                cv2.circle(alpha, tuple(np.int32(p[1] * 4)), int(p[2] * 4), 1.0, p[3], cv2.LINE_AA, shift=2)
        else:
            pts = np.int32(p * 4).reshape(-1, 1, 2)
            cv2.fillPoly(lay, [pts], BONE.tolist(), cv2.LINE_AA, shift=2)
            cv2.fillPoly(alpha, [pts], 1.0, cv2.LINE_AA, shift=2)
            cv2.polylines(lay, [pts], True, (INK * 2).tolist(), 2, cv2.LINE_AA, shift=2)


def draw_face(lay, alpha, c, up, s, le, re, vis):
    """Blank plaster face with hollow eyes over the real face."""
    if vis < 0.05:
        return
    side = np.array([-up[1], up[0]])
    eyes_mid = (le + re) / 2
    cc = eyes_mid - up * s * 0.12
    ang = math.degrees(math.atan2(side[1], side[0]))
    axes = (int(s * 0.5 * 4), int(s * 0.64 * 4))
    col = (BONE * 0.95).tolist()
    cv2.ellipse(lay, tuple(np.int32(cc * 4)), axes, ang, 0, 360, col, -1, cv2.LINE_AA, shift=2)
    cv2.ellipse(alpha, tuple(np.int32(cc * 4)), axes, ang, 0, 360, vis, -1, cv2.LINE_AA, shift=2)
    for e in (le, re):
        cv2.ellipse(lay, tuple(np.int32(e * 4)), (int(s * 0.13 * 4), int(s * 0.07 * 4)), ang, 0, 360, (0.0, 0.0, 0.0), -1, cv2.LINE_AA, shift=2)
    # thin dark slit under the eyes reads as a carved mouth
    m0 = cc - up * s * 0.38
    cv2.line(lay, tuple(np.int32((m0 - side * s * 0.12) * 4)), tuple(np.int32((m0 + side * s * 0.12) * 4)), (0.05, 0.05, 0.06), max(2, int(s * 0.03)), cv2.LINE_AA, shift=2)


def creature_layer(shot, i, t):
    lay = np.zeros((OUT_H, OUT_W, 3), np.float32)
    alpha = np.zeros((OUT_H, OUT_W), np.float32)
    if shot not in TRACKS:
        return lay, alpha
    src_i = edit_index[(shot, i)]
    # one crown per head: when two tracks sit on the same head, keep the longer one
    live = [(k, tr) for k, tr in enumerate(TRACKS[shot]) if 0 <= src_i - tr["start"] < tr["n"]]
    live.sort(key=lambda kt: -kt[1]["n"])
    chosen = []
    for k, tr in live:
        j = src_i - tr["start"]
        if all(np.linalg.norm(tr["c"][j] - o["c"][src_i - o["start"]]) > 1.3 * tr["s"][j] for _, o in chosen):
            chosen.append((k, tr))
    for k, tr in chosen:
        j = src_i - tr["start"]
        fade = min(1.0, (j + 1) / 6, (tr["n"] - j) / 6)
        c = to4k(tr["c"][j])
        up = tr["up"][j] / (np.linalg.norm(tr["up"][j]) + 1e-6)
        s = tr["s"][j] * K
        la = np.zeros_like(alpha)
        draw_crown(lay, la, tr["crown"], c, up, s * 1.45, t, seed=k * 31 + ord(shot))
        draw_face(lay, la, c, up, s, to4k(tr["le"][j]), to4k(tr["re"][j]), float(np.clip(tr["face"][j] * 1.4 - 0.2, 0, 1)))
        alpha = np.maximum(alpha, la * fade)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.0)
    return lay, alpha


# maps (shot, timeline index within shot) -> index of the underlying edit frame (holds repeat frames)
edit_index = {}
for shot, f, i, n in timeline:
    if f:
        edit_index[(shot, i)] = int(f.split("_")[1].split(".")[0]) - 1

# ---------------------------------------------------------------- text
F_ANTON = f"{FONTS}/Anton-Regular.ttf"
F_MONO = f"{FONTS}/IBMPlexMono-SemiBold.ttf"


def text_layer(items):
    """items: (text, font, size, (x, y), rgb, alpha, tracking) -> float BGR + alpha."""
    im = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for text, font, size, (x, y), rgb, a, track in items:
        if a <= 0:
            continue
        f = ImageFont.truetype(font, size)
        cx = x
        for ch in text:
            d.text((cx, y), ch, font=f, fill=(*rgb, int(255 * a)))
            cx += d.textlength(ch, font=f) + track
    arr = np.asarray(im).astype(np.float32) / 255
    return arr[..., [2, 1, 0]], arr[..., 3]


# ---------------------------------------------------------------- per-frame composition
echo = np.zeros((OUT_H // 2, OUT_W // 2, 3), np.float32)
last_dancer = None


def act_params(shot, i, n):
    p = i / max(1, n - 1)
    if shot == "A":
        return dict(light=smoothstep(0.0, 0.55, p) * (0.75 + 0.25 * (math.sin(i * 1.7) > -0.6 or p > 0.5)), red=0.0, echo=0.0, wob=0.0, push=0.04 * p)
    if shot == "B":
        return dict(light=1.0, red=0.15 * p, echo=0.35, wob=0.0, push=0.04 + 0.03 * p)
    if shot == "C":
        return dict(light=0.9, red=0.55, echo=0.55, wob=0.4, push=0.02 + 0.05 * p)
    if shot == "D":
        return dict(light=0.85, red=0.9, echo=0.6, wob=1.0, push=0.06 + 0.04 * p)
    if shot == "E":
        return dict(light=1.1, red=0.6, echo=0.7, wob=0.6, push=0.0 + 0.08 * p)
    return dict(light=0.55, red=0.25, echo=0.0, wob=0.0, push=0.03 * p)


def grade_dancers(img, prm):
    lum = img @ np.array([0.114, 0.587, 0.299], np.float32)
    g = lum[..., None] + (img - lum[..., None]) * 0.28          # ashen, near-grey skin
    g = g * np.array([1.06, 1.0, 0.94], np.float32)              # cold cast
    g = np.clip(g, 0, 1)
    g = g * g * (3 - 2 * g) * 0.65 + g * 0.35                      # contrast
    return g * light_on_dancer[..., None] * (0.35 + 0.75 * prm["light"])


def compose(idx):
    global echo, last_dancer
    shot, fname, i, n = timeline[idx]
    t = idx
    prm = act_params(shot, i, n)
    flick = 1.0 + 0.05 * math.sin(t * 0.9) * math.sin(t * 2.3)

    # stage
    hz = HAZE[:, (t * 3) % 960:(t * 3) % 960 + 960]
    hz = cv2.resize(hz, (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
    beam_l = beam * (0.55 + 0.9 * hz) * 0.16 * prm["light"] * flick
    base = wall + floor + horizon * prm["light"] + pool * 0.08 * prm["light"]
    bg = np.empty((OUT_H, OUT_W, 3), np.float32)
    bg[..., 0] = base * 1.08 + beam_l * 0.92
    bg[..., 1] = base * 1.0 + beam_l * 0.97
    bg[..., 2] = base * 0.95 + beam_l * 1.0
    red = red_floor * prm["red"] * (0.16 + 0.04 * math.sin(t * 0.37))
    bg[..., 2] += red
    bg[..., 1] += red * 0.08
    bg[..., 0] += red * 0.05

    if fname:
        dimg, a = dancer_layer(fname)
        last_dancer = (dimg, a)
    elif last_dancer is not None:
        dimg, a = last_dancer
        a = a * 0.22 * (1 - i / n * 0.4)
    else:
        dimg, a = np.zeros_like(bg), np.zeros((OUT_H, OUT_W), np.float32)

    if prm["wob"] > 0:  # creature tremor: low-frequency displacement of the bodies
        off = (t * 5) % 240
        w = cv2.resize(WOBBLE[:, off:off + 240], (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR) - 0.5
        dx = (w * 22 * prm["wob"]).astype(np.float32)
        mapx, mapy = xx + dx, yy + dx * 0.6
        dimg = cv2.remap(dimg, mapx, mapy, cv2.INTER_LINEAR)
        a = cv2.remap(a, mapx, mapy, cv2.INTER_LINEAR)

    dg = grade_dancers(dimg, prm)
    # red underlight climbing the bodies
    dg[..., 2] += red_floor * prm["red"] * 0.06 * a
    # rim light from the matte edge
    edge = np.clip(a - np.roll(a, 7, axis=0), 0, 1) * 0.8 + np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1) * 0.2
    edge = cv2.GaussianBlur(edge, (0, 0), 1.8)
    rim = np.array([0.95, 0.92, 0.88], np.float32) * (1 - prm["red"] * 0.6) + np.array([0.15, 0.12, 0.95], np.float32) * prm["red"] * 0.6
    dg += edge[..., None] * rim * 0.32 * prm["light"]

    # wet-floor reflection: mirror each column about its lowest matte pixel (the feet)
    col = (a[FLOOR_Y - 300:] > 0.4)
    has = col.any(0)
    foot = np.where(has, FLOOR_Y - 300 + (col.shape[0] - 1 - np.argmax(col[::-1], 0)), 0).astype(np.float32)
    foot = cv2.GaussianBlur(foot.reshape(1, -1), (0, 0), 40).ravel() / np.maximum(cv2.GaussianBlur(has.astype(np.float32).reshape(1, -1), (0, 0), 40).ravel(), 1e-3)
    foot = np.where(has | (cv2.GaussianBlur(has.astype(np.float32).reshape(1, -1), (0, 0), 40).ravel() > 0.2), foot, -1e4)
    my = np.where(yy > foot[None, :], 2 * foot[None, :] - yy, -10).astype(np.float32)
    small = (slice(None, None, 2), slice(None, None, 2))
    refl = cv2.remap(dg[small], xx[small] / 2, my[small] / 2, cv2.INTER_LINEAR, borderValue=0)
    ra = cv2.remap(a[small], xx[small] / 2, my[small] / 2, cv2.INTER_LINEAR, borderValue=0)
    fall = np.exp(-np.clip(yy[small] - foot[None, ::2], 0, None) / 260)
    ra = cv2.GaussianBlur(ra * fall * 0.28, (0, 0), 3)
    refl = cv2.GaussianBlur(refl, (0, 0), 3)
    refl = cv2.resize(refl, (OUT_W, OUT_H)); ra = cv2.resize(ra, (OUT_W, OUT_H))
    out = bg * (1 - ra[..., None]) + refl * ra[..., None]

    # ghost echo trails
    small_d = cv2.resize(dg * a[..., None], (OUT_W // 2, OUT_H // 2), interpolation=cv2.INTER_AREA)
    echo = np.maximum(echo * 0.86, small_d) if fname else echo * 0.8
    if prm["echo"] > 0:
        ghost = cv2.resize(cv2.GaussianBlur(echo, (0, 0), 2), (OUT_W, OUT_H))
        tint = np.array([1.0, 0.95, 0.9], np.float32) * (1 - prm["red"]) + np.array([0.35, 0.3, 1.0], np.float32) * prm["red"]
        out += ghost * tint * prm["echo"] * 0.4 * (1 - a[..., None])

    # crowns and plaster faces
    if fname:
        cl, ca = creature_layer(shot, i, t)
    else:
        cl, ca = np.zeros_like(dg), np.zeros_like(a)

    # giant shadows of the creatures thrown onto the haze behind them
    q = cv2.resize(np.maximum(a, ca), (OUT_W // 4, OUT_H // 4), interpolation=cv2.INTER_AREA)
    sc = 1.75
    cxq, cyq = BEAM_X / 4, FLOOR_Y / 4 + 60
    Ms = np.float32([[sc, 0, cxq * (1 - sc) + 40], [0, sc, cyq * (1 - sc) - 30]])
    sh = cv2.GaussianBlur(cv2.warpAffine(q, Ms, (OUT_W // 4, OUT_H // 4)), (0, 0), 3.5)
    sh = cv2.resize(sh, (OUT_W, OUT_H)) * (yy < FLOOR_Y + 20)
    out = out * (1 - 0.72 * sh[..., None] * min(1.0, prm["light"] + 0.2))

    out = out * (1 - a[..., None]) + dg * a[..., None]

    if fname:
        cl = cl * light_on_dancer[..., None] * (0.3 + 0.75 * prm["light"])
        glow = cv2.resize(cv2.GaussianBlur(cv2.resize(cl * ca[..., None], (OUT_W // 4, OUT_H // 4)), (0, 0), 6), (OUT_W, OUT_H))
        out = out * (1 - ca[..., None]) + cl * ca[..., None] + glow * 0.6 * prm["light"]

    # dust motes in the beam
    dl = np.zeros((OUT_H // 2, OUT_W // 2), np.float32)
    dy = (dust_y + dust_v * t * 2.2) % OUT_H
    dx = dust_x + np.sin(t * 0.03 + dust_b * 20) * 30
    for x, y, r, b in zip(dx, dy, dust_r, dust_b):
        bb = b * float(beam[int(min(y, OUT_H - 1)), int(np.clip(x, 0, OUT_W - 1))])
        if bb > 0.03:
            cv2.circle(dl, (int(x / 2), int(y / 2)), max(1, int(r / 2)), bb, -1, cv2.LINE_AA)
    dl = cv2.resize(cv2.GaussianBlur(dl, (0, 0), 0.8), (OUT_W, OUT_H))
    out += dl[..., None] * np.array([0.8, 0.85, 0.9], np.float32) * 0.5 * prm["light"]

    # title card
    if shot == "T":
        out = title(out, i, n)

    # opening credit
    if shot == "A" and i < 75:
        aa = smoothstep(5, 25, i) * (1 - smoothstep(55, 75, i))
        tl, ta = text_layer([("REBIRTH.UKRAINE  ×  135 CLUB", F_MONO, 54, (OUT_W // 2 - 620, OUT_H // 2 - 600), (225, 220, 212), aa, 14)])
        out = out * (1 - ta[..., None]) + tl * ta[..., None]

    # flashes on cuts and on the climax beats
    flash = 0.0
    for c in cut_frames:
        if 0 <= idx - c < 4 and timeline[c][0] in "CDE":
            flash = max(flash, [0.9, 0.45, 0.18, 0.06][idx - c])
    if shot == "E" and i in (18, 19, 38, 39, 52):
        flash = max(flash, 0.5)
    out = out + flash * (0.25 + out * 1.5)

    # camera push and shake
    z = 1.0 + prm["push"]
    shake = (0.0 if shot in "ABT" else 6.0 * prm["wob"])
    sx, sy = math.sin(t * 1.9) * shake, math.cos(t * 2.7) * shake
    M = np.float32([[z, 0, OUT_W / 2 * (1 - z) + sx], [0, z, OUT_H / 2 * (1 - z) + sy]])
    out = cv2.warpAffine(out, M, (OUT_W, OUT_H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    # finishing: halation, grade, vignette, grain
    hal = cv2.resize(cv2.GaussianBlur(cv2.resize(np.clip(out - 0.5, 0, None), (OUT_W // 8, OUT_H // 8)), (0, 0), 5), (OUT_W, OUT_H))
    out = out + hal * np.array([0.25, 0.35, 0.6], np.float32)
    lum = out @ np.array([0.114, 0.587, 0.299], np.float32)
    shadows = (1 - smoothstep(0.0, 0.35, lum))[..., None]
    out = out + shadows * np.array([0.012, 0.008, 0.0], np.float32)       # steel-grey shadows
    out = out * vign[..., None]
    if shot == "A" and i < 12:
        out *= i / 12
    out = 1 - np.exp(-out * 1.9)                                         # soft filmic shoulder
    grain = cv2.resize(rng.standard_normal((OUT_H // 2, OUT_W // 2)).astype(np.float32), (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
    out += grain[..., None] * 0.028 * (1 - 0.6 * lum[..., None].clip(0, 1))
    out = np.clip(out, 0, 1) ** (1 / 1.15)
    return (out * 255 + 0.5).astype(np.uint8)


def title(out, i, n):
    p = i / n
    out = out * 0.75
    items = []
    # letters of AFTER DARK switch on like failing bulbs
    word_a = smoothstep(4, 10, i) * (0.55 + 0.45 * (i > 16 or (i % 3 != 0)))
    items.append(("AFTER DARK", F_ANTON, 520, (OUT_W // 2 - 1270, OUT_H // 2 - 470), (240, 233, 220), word_a, 6))
    items.append(("IMMERSIVE  HALLOWEEN  EXPERIENCE", F_MONO, 64, (OUT_W // 2 - 1270, OUT_H // 2 + 170), (205, 22, 32), smoothstep(26, 40, i), 10))
    items.append(("30 OCTOBER  ·  7PM – 1AM", F_ANTON, 120, (OUT_W // 2 - 1270, OUT_H // 2 + 330), (240, 233, 220), smoothstep(40, 56, i), 4))
    items.append(("UKRAINIAN NATIONAL HOME  ·  140 2ND AVE, NEW YORK", F_MONO, 50, (OUT_W // 2 - 1270, OUT_H // 2 + 500), (170, 164, 154), smoothstep(52, 68, i), 8))
    tl, ta = text_layer(items)
    return out * (1 - ta[..., None]) + tl * ta[..., None]


# ---------------------------------------------------------------- run
if MODE == "preview":
    os.makedirs(f"{S}/preview", exist_ok=True)
    for idx in map(int, sys.argv[3].split(",")):
        img = compose(idx)
        cv2.imwrite(f"{S}/preview/p_{idx:04d}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("preview", idx, timeline[idx][:3], flush=True)
else:
    out_path = sys.argv[3]
    start, end = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, N)
    for idx in range(max(0, start - 15), start):  # warm up the ghost-echo buffer
        compose(idx)
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OUT_W}x{OUT_H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "13",
                           "-pix_fmt", "yuv420p", "-x264-params", "aq-mode=3", out_path], stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for idx in range(start, end):
        img = compose(idx)
        ff.stdin.write(img.tobytes())
        if idx % 30 == 0:
            cv2.imwrite(f"{S}/preview/run_{idx:04d}.jpg", cv2.resize(img, (1920, 1080)), [cv2.IMWRITE_JPEG_QUALITY, 88])
            print(f"frame {idx}/{end} {(time.time() - t0) / (idx - start + 1):.2f}s/frame", flush=True)
    ff.stdin.close()
    ff.wait()
    print("RENDER_DONE", flush=True)
