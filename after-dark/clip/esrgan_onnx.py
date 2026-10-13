"""Convert Real-ESRGAN realesr-general-x4v3 (SRVGGNetCompact) weights to ONNX without PyTorch.

usage: python3 esrgan_onnx.py realesr-general-x4v3.pth realesr-x4v3.onnx
"""
import pickle
import sys
import zipfile

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

DTYPES = {"FloatStorage": np.float32, "HalfStorage": np.float16}


def load_state_dict(path):
    z = zipfile.ZipFile(path)
    root = z.namelist()[0].split("/")[0]

    class Unpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "torch._utils" and name == "_rebuild_tensor_v2":
                def rebuild(storage, offset, size, stride, *_):
                    arr = np.lib.stride_tricks.as_strided(
                        storage[offset:], shape=size, strides=[s * storage.itemsize for s in stride])
                    return np.ascontiguousarray(arr)
                return rebuild
            if module == "torch" and name in DTYPES:
                return name
            if module == "collections" and name == "OrderedDict":
                import collections
                return collections.OrderedDict
            return super().find_class(module, name)

        def persistent_load(self, pid):
            _, stype, key, _, _ = pid
            return np.frombuffer(z.read(f"{root}/data/{key}"), dtype=DTYPES[stype])

    obj = Unpickler(z.open(f"{root}/data.pkl")).load()
    return obj.get("params_ema") or obj.get("params") or obj


def build(sd, out):
    nodes, inits = [], []
    def init(name, arr):
        inits.append(numpy_helper.from_array(arr.astype(np.float32), name))
    x = "input"
    idx = sorted({int(k.split(".")[1]) for k in sd if k.startswith("body.")})
    for i in idx:
        w = sd.get(f"body.{i}.weight")
        if w is None:
            continue
        if w.ndim == 4:  # conv
            init(f"w{i}", w); init(f"b{i}", sd[f"body.{i}.bias"])
            nodes.append(helper.make_node("Conv", [x, f"w{i}", f"b{i}"], [f"c{i}"], pads=[1, 1, 1, 1]))
            x = f"c{i}"
        else:  # PReLU, one slope per channel
            init(f"p{i}", w.reshape(-1, 1, 1))
            nodes.append(helper.make_node("PRelu", [x, f"p{i}"], [f"a{i}"]))
            x = f"a{i}"
    nodes.append(helper.make_node("DepthToSpace", [x], ["up"], blocksize=4, mode="CRD"))
    init("scales", np.array([1, 1, 4, 4], np.float32))
    nodes.append(helper.make_node("Resize", ["input", "", "scales"], ["base"], mode="nearest",
                                  coordinate_transformation_mode="asymmetric", nearest_mode="floor"))
    nodes.append(helper.make_node("Add", ["up", "base"], ["output"]))
    g = helper.make_graph(nodes, "srvgg",
                          [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, "h", "w"])],
                          [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, "H", "W"])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)], ir_version=8)
    onnx.checker.check_model(m)
    onnx.save(m, out)


if __name__ == "__main__":
    sd = load_state_dict(sys.argv[1])
    print(len(sd), "tensors")
    build(sd, sys.argv[2])
    print("saved", sys.argv[2])
