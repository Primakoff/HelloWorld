"""Per-frame dancer masks and head landmarks for the edited shots.

Runs MediaPipe's selfie segmenter and pose landmarker on overlapping, 2x-upscaled tiles,
because on the full wide frame the models only find one or two of the six dancers.

usage: python3 analyze.py <edit_dir> <models_dir> <out_dir>
"""
import json
import os
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

EDIT, MODELS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=f"{MODELS}/selfie_multiclass_256x256.tflite"),
    output_confidence_masks=True))
pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=f"{MODELS}/pose_landmarker_heavy.task"),
    running_mode=vision.RunningMode.IMAGE, num_poses=3, min_pose_detection_confidence=0.25,
    min_pose_presence_confidence=0.25, output_segmentation_masks=True))

Y0, Y1, TW, STEP = 30, 600, 300, 150
XS = list(range(100, 1180 - TW + 1, STEP)) + [1180 - TW]
KEYS = {"nose": 0, "leye": 2, "reye": 5, "lear": 7, "rear": 8, "lsh": 11, "rsh": 12}


def analyze(frame):
    H, W = frame.shape[:2]
    mask = np.zeros((H, W), np.float32)
    heads = []
    for x0 in XS:
        x1 = x0 + TW
        crop = np.ascontiguousarray(cv2.cvtColor(frame[Y0:Y1, x0:x1], cv2.COLOR_BGR2RGB))
        up = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=up)
        bg = seg.segment(img).confidence_masks[0].numpy_view().squeeze()
        person = cv2.resize(1.0 - bg, (TW, Y1 - Y0), interpolation=cv2.INTER_LINEAR)
        r = pose.detect(img)
        for sm, pl in zip(r.segmentation_masks or [], r.pose_landmarks):
            pm = cv2.resize(sm.numpy_view().squeeze(), (TW, Y1 - Y0), interpolation=cv2.INTER_LINEAR)
            person = np.maximum(person, pm)
            pts = {k: (x0 + pl[i].x * TW, Y0 + pl[i].y * (Y1 - Y0), pl[i].visibility) for k, i in KEYS.items()}
            heads.append(pts)
        # feather tile borders so overlapping tiles blend without seams
        ramp = np.minimum(np.arange(TW) / 20.0, 1.0)
        ramp = np.minimum(ramp, ramp[::-1]) if 0 < x0 and x1 < W else ramp * 0 + 1
        mask[Y0:Y1, x0:x1] = np.maximum(mask[Y0:Y1, x0:x1], person * ramp[None, :])
    return mask, dedupe(heads)


def dedupe(heads):
    out = []
    for h in heads:
        c = np.array(h["nose"][:2])
        if all(np.linalg.norm(c - np.array(o["nose"][:2])) > 22 for o in out):
            out.append(h)
    return out


meta = {}
names = sorted(f for f in os.listdir(EDIT) if f.endswith(".png"))
prev = {}
for i, name in enumerate(names):
    shot = name.split("_")[0]
    frame = cv2.imread(f"{EDIT}/{name}")
    m, heads = analyze(frame)
    if shot in prev:  # light temporal smoothing against mask flicker
        m = 0.65 * m + 0.35 * prev[shot]
    prev[shot] = m
    cv2.imwrite(f"{OUT}/{name}", (np.clip(m, 0, 1) * 255).astype(np.uint8))
    meta[name] = heads
    if i % 20 == 0:
        print(f"{i}/{len(names)} {name} heads={len(heads)}", flush=True)
json.dump(meta, open(f"{OUT}/heads.json", "w"))
print("ANALYZE_DONE", flush=True)
