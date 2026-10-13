"""Relative depth of the photo with Depth Anything V2 (small, ONNX), averaged with a mirrored pass.

usage: python3 depth.py <model.onnx> <image.png> <out_depth.png>
"""
import sys

import cv2
import numpy as np
import onnxruntime as ort

model, src, dst = sys.argv[1:4]
sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
img = cv2.imread(src)[..., ::-1].astype(np.float32) / 255
h, w = img.shape[:2]


def run(x):
    x = cv2.resize(x, (518, 518), interpolation=cv2.INTER_CUBIC)
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    d = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    return cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)


d = (run(img) + run(img[:, ::-1].copy())[:, ::-1]) / 2
d = (d - np.percentile(d, 1)) / (np.percentile(d, 99.5) - np.percentile(d, 1))
cv2.imwrite(dst, (np.clip(d, 0, 1) * 65535).astype(np.uint16))
print("depth saved", d.shape)
