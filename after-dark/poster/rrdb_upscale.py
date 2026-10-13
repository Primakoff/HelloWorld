"""Real-ESRGAN x4plus (RRDBNet) without PyTorch: convert the .pth to ONNX, then upscale an image in tiles.

usage: python3 rrdb_upscale.py <RealESRGAN_x4plus.pth> <in.png> <out.png>
"""
import os
import sys

import cv2
import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper, numpy_helper

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "clip"))
from esrgan_onnx import load_state_dict  # noqa: E402


def build(sd, path):
    nodes, inits = [], []
    uid = [0]

    def name(p):
        uid[0] += 1
        return f"{p}_{uid[0]}"

    def conv(x, key, act):
        init_w, init_b = f"{key}.weight", f"{key}.bias"
        if init_w not in {i.name for i in inits}:
            inits.append(numpy_helper.from_array(sd[init_w].astype(np.float32), init_w))
            inits.append(numpy_helper.from_array(sd[init_b].astype(np.float32), init_b))
        y = name("conv")
        nodes.append(helper.make_node("Conv", [x, init_w, init_b], [y], pads=[1, 1, 1, 1]))
        if act:
            z = name("lrelu")
            nodes.append(helper.make_node("LeakyRelu", [y], [z], alpha=0.2))
            return z
        return y

    def cat(xs):
        y = name("cat")
        nodes.append(helper.make_node("Concat", xs, [y], axis=1))
        return y

    def scaled_add(a, b, s=0.2):
        if "k02" not in {i.name for i in inits}:
            inits.append(numpy_helper.from_array(np.array(s, np.float32), "k02"))
        m, y = name("mul"), name("add")
        nodes.append(helper.make_node("Mul", [a, "k02"], [m]))
        nodes.append(helper.make_node("Add", [m, b], [y]))
        return y

    def rdb(x, key):
        x1 = conv(x, f"{key}.conv1", True)
        x2 = conv(cat([x, x1]), f"{key}.conv2", True)
        x3 = conv(cat([x, x1, x2]), f"{key}.conv3", True)
        x4 = conv(cat([x, x1, x2, x3]), f"{key}.conv4", True)
        x5 = conv(cat([x, x1, x2, x3, x4]), f"{key}.conv5", False)
        return scaled_add(x5, x)

    def up2(x):
        if "s2" not in {i.name for i in inits}:
            inits.append(numpy_helper.from_array(np.array([1, 1, 2, 2], np.float32), "s2"))
        y = name("up")
        nodes.append(helper.make_node("Resize", [x, "", "s2"], [y], mode="nearest",
                                      coordinate_transformation_mode="asymmetric", nearest_mode="floor"))
        return y

    feat = conv("input", "conv_first", False)
    body = feat
    nblocks = len({k.split(".")[1] for k in sd if k.startswith("body.")})
    for b in range(nblocks):
        r = body
        for j in (1, 2, 3):
            r = rdb(r, f"body.{b}.rdb{j}")
        body = scaled_add(r, body)
    body = conv(body, "conv_body", False)
    s = name("add")
    nodes.append(helper.make_node("Add", [feat, body], [s]))
    f = conv(up2(s), "conv_up1", True)
    f = conv(up2(f), "conv_up2", True)
    f = conv(f, "conv_hr", True)
    out = conv(f, "conv_last", False)
    nodes.append(helper.make_node("Identity", [out], ["output"]))
    g = helper.make_graph(nodes, "rrdb", [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, "h", "w"])],
                          [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, "H", "W"])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)], ir_version=8)
    onnx.save(m, path)


def upscale(sess, img, tile=128, pad=12):
    h, w = img.shape[:2]
    x = img[..., ::-1].astype(np.float32) / 255
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            ya, xa = max(0, y0 - pad), max(0, x0 - pad)
            yb, xb = min(h, y0 + tile + pad), min(w, x0 + tile + pad)
            t = np.ascontiguousarray(x[ya:yb, xa:xb].transpose(2, 0, 1)[None])
            r = sess.run(None, {"input": t})[0][0].transpose(1, 2, 0)
            oy, ox = (y0 - ya) * 4, (x0 - xa) * 4
            th, tw = min(tile, h - y0) * 4, min(tile, w - x0) * 4
            out[y0 * 4:y0 * 4 + th, x0 * 4:x0 * 4 + tw] = r[oy:oy + th, ox:ox + tw]
        print(f"row {y0}/{h}", flush=True)
    return (np.clip(out, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    pth, src, dst = sys.argv[1:4]
    onnx_path = pth.replace(".pth", ".onnx")
    if not os.path.exists(onnx_path):
        build(load_state_dict(pth), onnx_path)
    so = ort.SessionOptions()
    so.intra_op_num_threads = os.cpu_count()
    sess = ort.InferenceSession(onnx_path, so, providers=["CPUExecutionProvider"])
    cv2.imwrite(dst, upscale(sess, cv2.imread(src)))
    print("saved", dst)
