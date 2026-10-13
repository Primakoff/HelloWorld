"""Second, denser pose pass (narrow 3x-upscaled tiles) to find heads the first pass missed.

usage: python3 heads_pass2.py <edit_dir> <models_dir> <ana_dir>   -> <ana_dir>/heads2.json
"""
import json
import os
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

EDIT, MODELS, ANA = sys.argv[1:4]
pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=f"{MODELS}/pose_landmarker_heavy.task"),
    running_mode=vision.RunningMode.IMAGE, num_poses=2, min_pose_detection_confidence=0.2,
    min_pose_presence_confidence=0.2))
KEYS = {"nose": 0, "leye": 2, "reye": 5, "lear": 7, "rear": 8, "lsh": 11, "rsh": 12}
Y0, Y1, TW = 30, 600, 210
XS = list(range(180, 1100 - TW + 1, 70))

base = json.load(open(f"{ANA}/heads.json"))
out = {}
names = sorted(f for f in os.listdir(EDIT) if f.endswith(".png"))
for n_i, name in enumerate(names):
    fr = cv2.imread(f"{EDIT}/{name}")
    heads = list(base.get(name, []))
    for x0 in XS:
        crop = np.ascontiguousarray(cv2.cvtColor(fr[Y0:Y1, x0:x0 + TW], cv2.COLOR_BGR2RGB))
        up = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        r = pose.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=up))
        for pl in r.pose_landmarks:
            pts = {k: (x0 + pl[i].x * TW, Y0 + pl[i].y * (Y1 - Y0), pl[i].visibility) for k, i in KEYS.items()}
            c = np.array(pts["nose"][:2])
            # keep only plausible heads (shoulders below-ish and close) not already found
            if np.linalg.norm(np.array(pts["lsh"][:2]) - c) > 90:
                continue
            if all(np.linalg.norm(c - np.array(h["nose"][:2])) > 20 for h in heads):
                heads.append(pts)
    out[name] = heads
    if n_i % 25 == 0:
        print(f"{n_i}/{len(names)} {name} heads {len(base.get(name, []))} -> {len(heads)}", flush=True)
json.dump(out, open(f"{ANA}/heads2.json", "w"))
print("PASS2_DONE", flush=True)
