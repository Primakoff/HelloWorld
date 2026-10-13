"""Living poster: the After Dark photo brought to life with depth parallax, swaying figures,
fluttering rags, smoke, failing stage light, a strobe climax and re-set typography.

usage:
  python3 animate.py <work> preview 2.0,5.0,9.4   # stills at given seconds
  python3 animate.py <work> full <frames_dir>     # every frame as JPEG
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORK, MODE = sys.argv[1], sys.argv[2]
P, FONTS = f"{WORK}/poster", f"{WORK}/fonts"
W, H, FPS, DUR = 1728, 2160, 30, 15.0
N = int(DUR * FPS)
SRC_W = 482
S = W / SRC_W                     # source poster pixel -> canvas pixel
PH = int(round(535 * S))          # photo height on canvas; below it the wet floor continues
rng = np.random.default_rng(31)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def sstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def guided(I, p, r, eps):
    box = lambda x: cv2.boxFilter(x, -1, (r, r))
    mI, mp = box(I), box(p)
    a = (box(I * p) - mI * mp) / (box(I * I) - mI * mI + eps)
    b = mp - a * mI
    return box(a) * I + box(b)


# ------------------------------------------------------------------ plates
photo = cv2.resize(cv2.imread(f"{P}/clean_x4.png"), (W, PH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
depth = cv2.imread(f"{P}/depth.png", cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
depth = cv2.resize(depth, (W, PH), interpolation=cv2.INTER_CUBIC)
gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
depth = np.clip(guided(gray, depth, 9, 2e-3), 0, 1)

# wet floor below the photo: mirrored, darkened reflection of its bottom rows
ext = H - PH
fade = (0.75 * np.exp(-np.arange(ext, dtype=np.float32) / (ext * 0.28)))[:, None, None]
refl = cv2.GaussianBlur(photo[PH - ext:][::-1], (0, 0), 2.5) * fade
img0 = np.concatenate([photo, refl], 0)
seam = smoothstep(PH - 40, PH + 40, np.arange(H, dtype=np.float32))[:, None, None]
img0 = img0 * (1 - seam * 0.25) + cv2.GaussianBlur(img0, (0, 0), 2) * seam * 0.25
D = np.concatenate([depth, depth[PH - ext:][::-1]], 0)
lum0 = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
fg = cv2.GaussianBlur(smoothstep(0.16, 0.32, D) * smoothstep(0.02, 0.09, lum0), (0, 0), 3)
# the empty black around the figures carries compression banding; smooth it out
calm = (smoothstep(0.06, 0.025, cv2.GaussianBlur(lum0, (0, 0), 4)) * (1 - fg))[..., None]
img0 = img0 * (1 - calm) + cv2.GaussianBlur(img0, (0, 0), 7) * calm

# the nine creatures: (head, pivot at the body below it, influence radius) in poster pixels
FIGS = [((265, 55), (265, 210), 48, "thorns"), ((325, 112), (320, 265), 58, "sun"), ((437, 90), (440, 255), 52, "star"),
        ((240, 150), (240, 295), 48, "moon"), ((395, 200), (395, 335), 42, "beak"), ((315, 245), (320, 365), 42, "cone"),
        ((450, 240), (445, 385), 46, "moon"), ((230, 280), (240, 435), 58, "sun"), ((370, 370), (360, 525), 72, "crown")]
figs = []
for k, ((hx, hy), (px, py), r, kind) in enumerate(FIGS):
    h = np.array([hx, hy], np.float32) * S
    p = np.array([px, py], np.float32) * S
    R = r * S
    x0, x1 = int(max(0, h[0] - 2.6 * R)), int(min(W, h[0] + 2.6 * R))
    y0, y1 = int(max(0, h[1] - 2.6 * R)), int(min(H, p[1] + 1.2 * R))
    sub = (slice(y0, y1), slice(x0, x1))
    d_head = float(np.median(D[int(h[1]) - 6:int(h[1]) + 6, int(h[0]) - 6:int(h[0]) + 6]))
    # upper body moves most, feet stay planted
    reach = np.exp(-(((xx[sub] - h[0]) ** 2) / (2 * (1.3 * R) ** 2) + ((yy[sub] - h[1]) ** 2) / (2 * (1.7 * R) ** 2)))
    affinity = np.exp(-((D[sub] - d_head) / 0.1) ** 2)
    w = (reach * affinity * fg[sub]).astype(np.float32)
    figs.append(dict(sub=sub, w=w, dx=xx[sub] - p[0], dy=yy[sub] - p[1], amp=0.018 + 0.012 * rng.random(),
                     f=0.11 + 0.08 * rng.random(), ph=rng.uniform(0, 6.28), kind=kind, h=h))


def fbm(h, w, octaves, seed, sx=1.0, sy=1.0):
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int((h >> (octaves - o)) * sy))
        gw = max(2, int((w >> (octaves - o)) * sx))
        acc += amp * cv2.resize(r.random((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.55
    return acc / tot


SMOKE = fbm(540, 864, 6, 3)                       # tiled sideways for drifting smoke
SMOKE = np.concatenate([SMOKE, SMOKE[:, ::-1]], 1)
WISP = fbm(270, 864, 5, 8, sx=1.6, sy=0.6)
WISP = np.concatenate([WISP, WISP[:, ::-1]], 1)
RAGS = fbm(540, 432, 5, 5, sx=1.2, sy=0.35)       # vertical streaks: rags hang down
RAGS = np.concatenate([RAGS, RAGS], 0)

key_light = np.exp(-(((xx - W * 0.92) / (W * 0.55)) ** 2 + ((yy + H * 0.05) / (H * 0.55)) ** 2)).astype(np.float32)
floor_red = smoothstep(H * 0.55, H * 0.95, yy).astype(np.float32)
vign = (1 - 0.7 * smoothstep(0.35, 1.25, np.sqrt(((xx - W * 0.6) / (W * 0.7)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2))).astype(np.float32)

ND = 420
dust = dict(x=rng.uniform(W * 0.3, W, ND), y=rng.uniform(0, H, ND), r=rng.uniform(1.0, 4.0, ND),
            v=rng.uniform(-14, 6, ND), b=rng.uniform(0.2, 1.0, ND), ph=rng.uniform(0, 6.28, ND))

# ------------------------------------------------------------------ typography
F_ANTON = f"{FONTS}/Anton-Regular.ttf"
F_OSW = f"{FONTS}/Oswald.ttf"
CREAM, RED, ASH = (240, 233, 220), (214, 24, 32), (176, 168, 156)


def font(path, size, var=None):
    f = ImageFont.truetype(path, size)
    if var:
        f.set_variation_by_name(var)
    return f


def text_sprite(text, f, color, track=0):
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    widths = [d.textlength(ch, font=f) for ch in text]
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(sum(widths) + track * len(text)) + 8, asc + desc + 8), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x, xs = 4, []
    for ch, wd in zip(text, widths):
        dr.text((x, 4), ch, font=f, fill=color + (255,))
        xs.append((x, wd))
        x += wd + track
    return np.asarray(im).astype(np.float32) / 255, xs


def element(text, f, color, pos, track=0):
    spr, xs = text_sprite(text, f, color, track)
    return dict(spr=spr, xs=xs, pos=pos, text=text)


X0 = int(28 * S)


def fitted(text, path, var, width_src, cap_top_src, color, track=0, x_src=28):
    """Size a line so it spans the same width as on the original poster, caps aligned to the same top."""
    size = 100
    for _ in range(3):
        f = font(path, size, var)
        spr, _ = text_sprite(text, f, color, track)
        size = int(size * (width_src * S) / (spr.shape[1] - 8))
    f = font(path, size, var)
    el = element(text, f, color, (0, 0), track)
    cap = f.getbbox("H")[1]
    el["pos"] = (int(x_src * S) - 4, int(cap_top_src * S) - cap - 4)
    return el


EL = {
    "kicker": fitted("REBIRTH.UKRAINE  X  135 CLUB", F_OSW, b"SemiBold", 131, 55, CREAM, 6, x_src=39),
    "after": fitted("AFTER", F_ANTON, None, 179, 77, CREAM),
    "dark": fitted("DARK", F_ANTON, None, 150, 163, CREAM),
    "imm1": fitted("IMMERSIVE HALLOWEEN", F_OSW, b"SemiBold", 168, 258, RED, 4),
    "imm2": fitted("EXPERIENCE", F_OSW, b"SemiBold", 82, 274, RED, 4),
    "date": fitted("OCTOBER 30", F_ANTON, None, 122, 316, CREAM),
    "time": fitted("7PM - 1AM", F_ANTON, None, 79, 342, CREAM),
    "venue": fitted("UKRAINIAN NATIONAL HOME", F_OSW, b"Medium", 170, 375, CREAM, 6),
    "addr": fitted("140 2ND AVE, NEW YORK, NY 10003", F_OSW, b"Regular", 137, 388, ASH, 2),
    "tickets": fitted("TICKETS", F_ANTON, None, 52, 425, CREAM),
}

qr_url = open(f"{P}/qr.txt").read().strip() or "https://www.eventbrite.com/e/after-dark-halloween-experience-tickets-2002981128474"
qr = cv2.QRCodeEncoder.create().encode(qr_url)
qs = int(70 * S) // qr.shape[0] * qr.shape[0]
qr = cv2.resize(qr, (qs, qs), interpolation=cv2.INTER_NEAREST).astype(np.float32) / 255
quiet = 16
qr_spr = np.ones((qs + 2 * quiet, qs + 2 * quiet, 4), np.float32)
qr_spr[..., :3] = np.array(CREAM, np.float32)[::-1] / 255
qr_spr[quiet:-quiet, quiet:-quiet, :3] = np.where(qr[..., None] > 0.5, qr_spr[quiet:-quiet, quiet:-quiet, :3], 0.05)
qr_spr = qr_spr[..., [2, 1, 0, 3]]  # store as RGBA like the text sprites
QR_POS = (X0 - quiet, int(445 * S) - quiet)

# when each letter of AFTER DARK switches on (seconds), like bulbs warming up
LETTER_ON = {("after", i): 2.9 + 0.11 * k + rng.uniform(0, 0.08) for k, i in enumerate(rng.permutation(5))}
LETTER_ON.update({("dark", i): 3.15 + 0.11 * k + rng.uniform(0, 0.08) for k, i in enumerate(rng.permutation(4))})

STROBES = [9.0, 9.33, 9.6, 9.93, 10.2, 10.47]
BLACKOUT = (10.75, 11.2)


def letter_alpha(key, i, t):
    on = LETTER_ON[(key, i)]
    if t < on:
        return 0.0
    k = (t - on) * FPS
    if k < 8:  # a few failed sparks before it holds
        return [1, 0, 0.6, 0, 0, 1, 0.3, 1][int(k)]
    return 1.0


def element_alpha(name, t):
    starts = {"kicker": (2.3, 0.7), "imm1": (4.4, 0.25), "imm2": (4.75, 0.25), "date": (5.4, 0.5), "time": (5.7, 0.5),
              "venue": (6.2, 0.5), "addr": (6.45, 0.5), "tickets": (6.9, 0.5)}
    s, d = starts[name]
    return sstep(s, s + d, t)


def paste(out, spr, pos, alpha, xs=None, per_letter=None, glow=0.0, shift=0):
    """Composite an RGBA sprite (RGB order) onto the BGR canvas."""
    h, w = spr.shape[:2]
    x, y = pos[0] + shift, pos[1]
    if alpha <= 0.001 or x >= W or y >= H:
        return
    a = spr[..., 3] * alpha
    if per_letter is not None:
        m = np.zeros(w, np.float32)
        for (lx, lw), la in zip(xs, per_letter):
            m[int(lx):int(lx + lw + 1)] = la
        a = a * m[None, :]
    rgb = spr[..., [2, 1, 0]]
    y0, x0 = max(0, y), max(0, x)
    y1, x1 = min(H, y + h), min(W, x + w)
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x, None]
    region = out[y0:y1, x0:x1]
    if glow > 0:
        g = cv2.GaussianBlur(sa[..., 0], (0, 0), 14)[..., None] * glow
        region += g * np.array([0.55, 0.62, 0.8], np.float32)
    out[y0:y1, x0:x1] = region * (1 - sa) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * sa


# ------------------------------------------------------------------ frame
def exposure(t):
    if t < 0.5:
        return 0.0
    if t < 1.9:  # a failing bulb
        k = int((t - 0.5) * FPS)
        pattern = [0, 0.4, 0, 0, 0.9, 0.1, 0, 0, 0, 0.7, 1, 0.2, 0, 0.5, 0.8, 0, 0.3, 1, 1, 0.6, 1, 1, 0.8, 1, 1, 1, 0.9, 1, 1, 1,
                   1, 1, 0.85, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        return pattern[min(k, len(pattern) - 1)] * sstep(0.5, 1.9, t) ** 0.3
    e = 1.0 + 0.04 * math.sin(t * 7.1) * math.sin(t * 2.3)
    if STROBES[0] - 0.1 < t < BLACKOUT[0]:
        e *= 0.35
    if BLACKOUT[0] <= t < BLACKOUT[1]:
        e = 0.02
    if BLACKOUT[1] <= t < BLACKOUT[1] + 0.9:
        e *= sstep(BLACKOUT[1], BLACKOUT[1] + 0.9, t)
    return e


def climax(t):
    return STROBES[0] - 0.05 <= t < BLACKOUT[0]


def compose(fi):
    t = fi / FPS
    # stop-motion stutter in the climax: motion holds for three frames at a time
    tm = (int(fi / 3) * 3) / FPS if climax(t) else t
    prog = sstep(0, DUR, t)

    # camera: slow push with depth parallax, a shudder during the strobes
    z = 1.0 + 0.085 * prog + (0.02 if climax(t) else 0)
    sx = 26 * math.sin(2 * math.pi * t / DUR * 0.9 - 0.6)
    sy = -14 * prog
    if climax(t):
        sx += rng.uniform(-9, 9)
        sy += rng.uniform(-6, 6)
    cx, cy = W * 0.62, H * 0.42
    zd = 1 + (z - 1) * (0.55 + 0.9 * D)
    mx = cx + (xx - cx) / zd - sx * (D - 0.3) * 1.6
    my = cy + (yy - cy) / zd - sy * (D - 0.3) * 1.6

    # creatures sway and breathe around their own pivots; in the climax they twitch
    for k, fgd in enumerate(figs):
        th = fgd["amp"] * math.sin(2 * math.pi * fgd["f"] * tm + fgd["ph"])
        breathe = 0.006 * math.sin(2 * math.pi * 0.23 * tm + fgd["ph"] * 2)
        if climax(t):
            th += np.random.default_rng(int(tm * 40) * 13 + k).uniform(-0.07, 0.07)
        c, s = math.cos(-th) * (1 - breathe), math.sin(-th) * (1 - breathe)
        sub, w = fgd["sub"], fgd["w"]
        mx[sub] += ((c - 1) * fgd["dx"] - s * fgd["dy"]) * w
        my[sub] += (s * fgd["dx"] + (c - 1) * fgd["dy"]) * w

    # rags: vertical streak noise drifting downward, only on the bodies
    off = int(tm * 22) % 540
    rag = cv2.resize(RAGS[off:off + 540], (W, H), interpolation=cv2.INTER_LINEAR) - 0.5
    rag2 = cv2.resize(RAGS[(off * 2 + 200) % 540:(off * 2 + 200) % 540 + 540], (W, H), interpolation=cv2.INTER_LINEAR) - 0.5
    mx += (rag * 5 + rag2 * 2.5) * fg * smoothstep(0.1, 0.5, (yy / H))
    my += rag2 * 1.5 * fg

    out = cv2.remap(img0, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    Dw = cv2.remap(D, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # light: exposure, a slow searching beam, warm key from the top right
    E = exposure(t)
    bx = W * (0.62 + 0.25 * math.sin(2 * math.pi * t / 11.0 + 1.2))
    beam = np.exp(-(((xx - bx - (yy - H * 0.3) * 0.25) / (W * 0.16)) ** 2)).astype(np.float32)
    out = out * (E * (0.78 + 0.35 * key_light[..., None] + 0.32 * beam[..., None] * smoothstep(0.1, 0.3, Dw)[..., None]))

    # red: heartbeat pulses from the floor, flooding during the climax
    beat = max(0.0, math.sin(2 * math.pi * 1.05 * t)) ** 12 if t > 6.0 else 0.0
    red_amt = 0.12 * beat + (0.55 if climax(t) else 0.0) + (0.18 * sstep(11.2, 13.0, t) if t > 11.2 else 0.0)
    lum = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    redl = red_amt * (0.35 * floor_red + 0.65 * smoothstep(0.05, 0.5, lum)) * smoothstep(0.12, 0.35, Dw)
    out[..., 2] += redl * 0.9
    out[..., 1] *= 1 - redl * 0.35
    out[..., 0] *= 1 - redl * 0.45

    # smoke in depth: thicker behind the figures and in the top-right light
    ox = int(t * 14) % 864
    sm = cv2.resize(SMOKE[:, ox:ox + 864], (W, H), interpolation=cv2.INTER_LINEAR)
    sm = smoothstep(0.35, 0.85, sm) * (0.25 + 0.75 * (1 - Dw)) * (0.35 + 0.9 * key_light)
    ow = int(t * 30) % 864
    wisp = cv2.resize(WISP[:, ow:ow + 864], (W, H), interpolation=cv2.INTER_LINEAR)
    wisp = smoothstep(0.5, 0.9, wisp) * smoothstep(H * 0.55, H, yy)
    haze = (sm * 0.2 + wisp * 0.12) * max(E, 0.15)
    out += haze[..., None] * np.array([0.78, 0.82, 0.86], np.float32)

    # dust in the beam
    dl = np.zeros((H // 2, W // 2), np.float32)
    dy = (dust["y"] + dust["v"] * t) % H
    dx = dust["x"] + 20 * np.sin(t * 0.7 + dust["ph"])
    for x, y, r, b in zip(dx, dy, dust["r"], dust["b"]):
        xi, yi = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
        bb = b * (0.25 + key_light[yi, xi] + beam[yi, xi]) * E
        if bb > 0.05:
            cv2.circle(dl, (xi // 2, yi // 2), max(1, int(r / 2)), float(bb), -1, cv2.LINE_AA)
    out += cv2.resize(cv2.GaussianBlur(dl, (0, 0), 1.0), (W, H))[..., None] * 0.35

    # strobes
    flash = 0.0
    for s in STROBES:
        k = (t - s) * FPS
        if 0 <= k < 4:
            flash = max(flash, [1.0, 0.55, 0.22, 0.08][int(k)])
    if flash:
        out = out * (1 + 2.8 * flash) + flash * 0.06
    # chromatic tear in the climax
    if climax(t):
        sh = int(6 + 10 * flash)
        out[..., 2] = np.roll(out[..., 2], sh, axis=1)
        out[..., 0] = np.roll(out[..., 0], -sh, axis=1)

    # bloom from the plaster masks and the light
    hi = cv2.resize(np.clip(out - 0.55, 0, None), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    out += cv2.resize(cv2.GaussianBlur(hi, (0, 0), 4), (W, H)) * np.array([0.5, 0.55, 0.65], np.float32)

    # typography
    tshift = 0
    glitch = climax(t) and np.random.default_rng(fi).random() < 0.6
    if glitch:
        tshift = int(np.random.default_rng(fi + 7).integers(-26, 26))
    for key in ("after", "dark"):
        e = EL[key]
        la = [letter_alpha(key, i, t) for i in range(len(e["text"]))]
        if BLACKOUT[0] <= t < BLACKOUT[1]:
            la = [v * 0.85 for v in la]
        paste(out, e["spr"], e["pos"], 1.0, e["xs"], la, glow=0.45 + (0.6 if climax(t) else 0), shift=tshift)
    for key in ("kicker", "imm1", "imm2", "date", "time", "venue", "addr", "tickets"):
        a = element_alpha(key, t) * (0.3 if BLACKOUT[0] <= t < BLACKOUT[1] else 1.0)
        paste(out, EL[key]["spr"], EL[key]["pos"], a, shift=tshift // 2 if glitch else 0)
    paste(out, qr_spr, QR_POS, sstep(7.1, 7.7, t) * (0.3 if BLACKOUT[0] <= t < BLACKOUT[1] else 1.0))

    # finish: vignette, filmic shoulder, grain, slight gate weave
    out *= vign[..., None]
    out = 1 - np.exp(-np.clip(out, 0, None) * 1.35)
    out = out / (1 - math.exp(-1.35))
    g = cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H))
    out += g[..., None] * 0.03
    if fi % 2:
        out = np.roll(out, 1, axis=0)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    json.dump({"fps": FPS, "dur": DUR, "strobes": STROBES, "blackout": BLACKOUT,
               "letters": sorted(LETTER_ON.values()), "flicker": [0.5, 1.9]}, open(f"{P}/events.json", "w"))
    if MODE == "preview":
        os.makedirs(f"{P}/preview", exist_ok=True)
        for t in map(float, sys.argv[3].split(",")):
            cv2.imwrite(f"{P}/preview/t_{t:05.2f}.jpg", compose(int(t * FPS)), [cv2.IMWRITE_JPEG_QUALITY, 92])
            print("preview", t, flush=True)
    else:
        fdir = sys.argv[3]
        os.makedirs(fdir, exist_ok=True)
        start = 0
        while start < N and os.path.exists(f"{fdir}/f_{start:04d}.jpg"):
            start += 1
        for fi in range(start, N):
            cv2.imwrite(f"{fdir}/f_{fi:04d}.jpg", compose(fi), [cv2.IMWRITE_JPEG_QUALITY, 96])
            if fi % 30 == 0:
                print("frame", fi, "/", N, flush=True)
        print("ANIM_DONE", flush=True)
