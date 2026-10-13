"""Score for the living poster, synced to the animation's events.json.

usage: python3 sound.py <events.json> <out.wav>
"""
import json
import math
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter, sosfilt

SR = 48000
ev = json.load(open(sys.argv[1]))
DUR = ev["dur"]
n = int(DUR * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(9)
L, R = np.zeros(n), np.zeros(n)
bo0, bo1 = ev["blackout"]


def env(t0, a, d):
    x = np.zeros(n)
    i0 = int(t0 * SR)
    if i0 >= n:
        return x
    tt = np.arange(min(int((a + d * 7) * SR), n - i0)) / SR
    x[i0:i0 + len(tt)] = np.minimum(tt / max(a, 1e-4), 1) * np.exp(-np.maximum(tt - a, 0) / d)
    return x


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), x)


def add(x, pan=0.5):
    global L, R
    L += x * (1.2 - pan)
    R += x * (0.2 + pan)


# low drone: dissonant cluster, silent in the blackout, swelling back after it
gate = np.clip(t / 2.5, 0, 1) * np.where((t > bo0) & (t < bo1), 0.0, 1.0) * (1 + 0.5 * np.clip((t - bo1) / 1.5, 0, 1) * (t > bo1))
drone = np.tanh(np.sin(2 * np.pi * 36.7 * t) + 0.8 * np.sin(2 * np.pi * 37.3 * t) + 0.5 * np.sin(2 * np.pi * 55.0 * t)
                + 0.3 * np.sin(2 * np.pi * 77.8 * t + np.sin(2 * np.pi * 0.17 * t))) * 0.2 * gate
add(drone)
air = filt(rng.standard_normal(n), "band", [200, 1100]) * 0.04 * gate * (0.6 + 0.4 * np.sin(2 * np.pi * 0.19 * t))
add(air, 0.3)
add(filt(rng.standard_normal(n), "band", [200, 1100]) * 0.04 * gate * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t + 2)), 0.7)

# failing bulb: mains hum and crackle while the light flickers on
f0, f1 = ev["flicker"]
on = ((t > f0) & (t < f1 + 0.6)).astype(float)
hum = (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.3 * np.sin(2 * np.pi * 150 * t)) * 0.05 * on
add(hum * (0.5 + 0.5 * (rng.random(n) > 0.3)))
for k in range(26):
    tc = rng.uniform(f0, f1)
    add(filt(rng.standard_normal(n), "high", 2500) * env(tc, 0.0005, 0.008) * rng.uniform(0.2, 0.5), rng.uniform(0.2, 0.8))

# letters of AFTER DARK switching on: heavy relay clunks
for tl in ev["letters"]:
    c = (np.sin(2 * np.pi * 95 * t) * env(tl, 0.001, 0.05) * 0.5 + filt(rng.standard_normal(n), "band", [1500, 5000]) * env(tl, 0.0005, 0.012) * 0.35)
    add(c, rng.uniform(0.3, 0.7))

# heartbeat locked to the red pulses (peaks of sin(2*pi*1.05*t))
k = 0
while True:
    tb = (0.25 + k) / 1.05
    k += 1
    if tb > DUR - 0.5:
        break
    if tb < 5.9 or (bo0 - 0.4 < tb < bo1):
        continue
    for off, amp in ((-0.06, 1.0), (0.12, 0.6)):
        e = env(tb + off, 0.004, 0.07)
        add(np.sin(2 * np.pi * (48 + 34 * e) * t) * e * 0.55 * amp)


def impact(t0, size):
    e = env(t0, 0.002, 0.4 * size)
    f = 33 + 70 * env(t0, 0.001, 0.07)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * e * 0.9 * size
    crack = filt(rng.standard_normal(n), "high", 1500) * env(t0, 0.001, 0.04) * 0.6 * size
    metal = sum(np.sin(2 * np.pi * fr * t + rng.uniform(0, 6)) * env(t0, 0.002, d) for fr, d in
                ((131, 1.0), (207, 0.7), (298.5, 0.6), (451, 0.4), (689, 0.3))) * 0.06 * size
    return sub + crack + metal


# rising scrape into the strobes
s0 = ev["strobes"][0]
rise = np.clip((t - (s0 - 1.8)) / 1.8, 0, 1) ** 3 * (t < s0)
add(filt(rng.standard_normal(n), "high", 3000) * rise * 0.25)
add(np.sin(2 * np.pi * (200 + 900 * rise) * t) * rise * 0.04)
for i, ts in enumerate(ev["strobes"]):
    add(impact(ts, 0.75 + 0.06 * i), 0.5 + (0.15 if i % 2 else -0.15))

# blackout: everything drops out except a breath; then one enormous boom
add(filt(rng.standard_normal(n), "band", [300, 900]) * env(bo0 + 0.08, 0.15, 0.12) * 0.25, 0.5)
add(impact(bo1, 1.7))
pad = np.zeros(n)
for fr in (73.4, 87.3, 103.8, 146.8):
    for det in (-0.35, 0.35):
        pad += 2 * ((fr + det) * t % 1) - 1
pad = filt(pad, "low", 650, 4) * np.clip((t - bo1 - 0.3) / 1.5, 0, 1) * 0.045
add(pad)


def reverb(x, mix):
    y = np.zeros_like(x)
    for dl, g in ((1557, 0.84), (1617, 0.83), (1491, 0.85), (1422, 0.86)):
        y += lfilter([1.0], np.r_[1.0, np.zeros(dl - 1), -g], filt(x, "low", 5000, 1))
    for dl in (225, 556):
        y = lfilter(np.r_[-0.5, np.zeros(dl - 1), 1.0], np.r_[1.0, np.zeros(dl - 1), -0.5], y)
    return x * (1 - mix) + y * mix * 0.25


mix = np.stack([reverb(L, 0.35), reverb(R, 0.38)], 1)
mix = filt(mix.T, "high", 25).T
mix = np.tanh(mix * 1.2) / math.tanh(1.2)
mix *= 0.89 / np.abs(mix).max()
mix *= (np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 0.8, 0, 1))[:, None]
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", sys.argv[2])
