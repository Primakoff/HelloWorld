"""Synthesised score for the After Dark clip: drone, heartbeat, impacts on cuts, title boom.

usage: python3 sound.py <timeline.json> <out.wav>
"""
import json
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter, sosfilt

SR = 48000
tl = json.load(open(sys.argv[1]))
FPS, N = tl["fps"], tl["n"]
shots = tl["shots"]
DUR = N / FPS + 0.5
n = int(DUR * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(5)


def start_of(s):
    return shots.index(s) / FPS


def env(t0, a, d, length=None):
    x = np.zeros(n)
    i0 = int(t0 * SR)
    L = int((length or (a + d * 6)) * SR)
    tt = np.arange(min(L, n - i0)) / SR
    x[i0:i0 + len(tt)] = np.minimum(tt / max(a, 1e-4), 1) * np.exp(-np.maximum(tt - a, 0) / d)
    return x


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


L = np.zeros(n)
R = np.zeros(n)
title_t = start_of("T")

# drone: dissonant low cluster with slow beating, swelling into the creature section
swell = np.clip(t / 3, 0, 1) * (0.55 + 0.45 * np.clip((t - start_of("C")) / 2, 0, 1)) * (t < title_t + 0.05)
drone = (np.sin(2 * np.pi * 41.2 * t) + 0.7 * np.sin(2 * np.pi * 41.9 * t)
         + 0.45 * np.sin(2 * np.pi * 61.7 * t + 0.5 * np.sin(2 * np.pi * 0.13 * t))
         + 0.25 * np.sin(2 * np.pi * 87.3 * t))
drone = np.tanh(drone * 0.9) * 0.22 * swell
L += drone
R += drone

# wind / breath: band-passed noise with a slow gust envelope, decorrelated per channel
for ch in (L, R):
    w = bp(rng.standard_normal(n), 180, 900)
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.21 * t + rng.uniform(0, 6))
    ch += w * 0.05 * gust * np.clip(t / 2, 0, 1) * (t < title_t)

# heartbeat through the opening, accelerating
beat_t, period = 0.6, 1.05
while beat_t < start_of("C") - 0.2:
    for off, amp in ((0, 1.0), (0.17, 0.65)):
        e = env(beat_t + off, 0.004, 0.06)
        thump = np.sin(2 * np.pi * (52 + 30 * e) * t) * e * 0.55 * amp
        L += thump
        R += thump
    beat_t += period
    period = max(0.55, period * 0.93)

# reverse swell into the first impact
c0 = start_of("C")
rs = np.clip((t - (c0 - 1.6)) / 1.6, 0, 1) ** 3 * (t < c0)
sw = hp(rng.standard_normal(n), 2500) * rs * 0.22
L += sw
R += sw


def impact(t0, size=1.0):
    e_sub = env(t0, 0.002, 0.45 * size)
    freq = 34 + 60 * env(t0, 0.001, 0.08)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * e_sub * 0.9 * size
    crack = hp(rng.standard_normal(n), 1200) * env(t0, 0.001, 0.05) * 0.5 * size
    metal = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * env(t0, 0.002, d) for f, d in
                ((143, 1.1), (227, 0.8), (311.5, 0.7), (468, 0.5), (733, 0.35))) * 0.07 * size
    return sub + crack + metal


for s, size in (("C", 1.0), ("D", 0.9), ("E", 1.1)):
    x = impact(start_of(s), size)
    L += x
    R += x
e0 = start_of("E")
for i in (18, 38, 52):
    x = impact(e0 + i / FPS, 0.55)
    L += x * 0.9
    R += x

# stop-motion ticks in the creature section
d0 = start_of("D")
for k in range(int((e0 - d0) * FPS / 7)):
    tick = hp(rng.standard_normal(n), 3000) * env(d0 + (k * 7 + 6) / FPS, 0.0005, 0.012) * 0.35
    pan = rng.uniform(0.3, 1.0)
    L += tick * pan
    R += tick * (1.3 - pan)

# title: one big boom, then a low diminished pad that fades out
x = impact(title_t, 1.5)
L += x
R += x
pad_env = np.clip((t - title_t - 0.2) / 1.2, 0, 1) * np.clip((DUR - 0.3 - t) / 1.6, 0, 1)
pad = np.zeros(n)
for f in (82.4, 98.0, 116.5, 164.8):
    for det in (-0.4, 0.4):
        pad += ((2 * ((f + det) * t % 1) - 1))  # sawtooth
pad = lp(pad, 700, 4) * pad_env * 0.05
L += pad
R += pad

# room: feedback-comb + allpass reverb on the sum
def reverb(x, mix):
    y = np.zeros_like(x)
    for dl, g in ((1557, 0.84), (1617, 0.83), (1491, 0.85), (1422, 0.86)):
        y += lfilter([1.0], np.r_[1.0, np.zeros(dl - 1), -g], lp(x, 5000, 1))
    for dl in (225, 556):
        y = lfilter(np.r_[-0.5, np.zeros(dl - 1), 1.0], np.r_[1.0, np.zeros(dl - 1), -0.5], y)
    return x * (1 - mix) + y * mix * 0.25


L, R = reverb(L, 0.35), reverb(R, 0.38)
mix = np.stack([L, R], 1)
mix = hp(mix.T, 25).T
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix *= 0.89 / np.abs(mix).max()
fade = np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 0.4, 0, 1)
mix *= fade[:, None]
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", sys.argv[2], f"{DUR:.2f}s")
