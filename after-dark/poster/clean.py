"""Remove the poster's typography, QR code and logo strip so the photo can be animated and re-typeset.

usage: python3 clean.py <poster.png> <out_dir>
"""
import sys

import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
im = cv2.imread(src)
qr = im[440:522, 24:112]
data, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.resize(qr, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC))
print("QR:", data or "(not readable)")

H = 535  # everything below is the sponsor strip
img = im[:H].copy()
lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
red = (img[..., 2].astype(np.int32) - img[..., 1]) > 40
mask = np.zeros(lum.shape, np.uint8)
# boxes around each text block (source pixel coordinates)
for x0, y0, x1, y1 in [(30, 50, 180, 68), (26, 72, 207, 246), (26, 252, 198, 288), (26, 308, 156, 362),
                       (26, 370, 202, 402), (26, 418, 112, 524)]:
    roi = (lum[y0:y1, x0:x1] > 38) | red[y0:y1, x0:x1]
    mask[y0:y1, x0:x1] = roi.astype(np.uint8) * 255
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
clean = cv2.inpaint(img, mask, 6, cv2.INPAINT_TELEA)
floor = np.median(img[:300, 5:20].reshape(-1, 3), axis=0)
# text sits on plain black: fill it with that black instead of letting inpainting borrow the moon's light
soft = cv2.GaussianBlur(cv2.dilate(mask, np.ones((5, 5), np.uint8)).astype(np.float32) / 255, (0, 0), 1.5)
soft[:, 209:] = 0
# the right edge of the letter R touches the moon mask; clear that sliver by hand
soft[72:113, 203:212] = np.maximum(soft[72:113, 203:212], (lum[72:113, 203:212] > 30).astype(np.float32))
soft[113:162, 203:210] = np.maximum(soft[113:162, 203:210], (lum[113:162, 203:210] > 90).astype(np.float32))
clean = (clean * (1 - soft[..., None]) + floor * soft[..., None]).astype(np.uint8)
# the area left of the figures is plain darkness: pull it to the photo's own black so no smudges remain
dark = np.zeros(lum.shape, np.float32)
dark[:, :200] = 1
dark = cv2.GaussianBlur(dark, (0, 0), 12) * (cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 6) > 0.02)
clean = (clean * (1 - dark[..., None] * 0.85) + floor * dark[..., None] * 0.85).astype(np.uint8)
cv2.imwrite(f"{out}/clean.png", clean)
cv2.imwrite(f"{out}/textmask.png", mask)
open(f"{out}/qr.txt", "w").write(data or "")
