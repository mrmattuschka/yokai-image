import numpy as np
from PIL import Image
import struct

encodings = {
    "HLSB": (1, "big"),
    "HMSB": (1, "little"),
    "VLSB": (0, "big")
}


def img2bytes(im, encoding="HLSB"):
    axis, bitorder = encodings[encoding]
    im = np.array(im).astype(bool)

    pad = 8 - im.shape[axis] % 8
    if axis == 0:
        pad_sizes = [[0, pad], [0, 0]]
    else:
        pad_sizes = [[0, 0], [0, pad]]

    im = np.pad(im, pad_sizes, constant_values=0)
    im = np.packbits(im, axis=axis, bitorder=bitorder).tobytes()

    return im


def bytes2img(im, size, encoding="HLSB"):
    axis, bitorder = encodings[encoding]

    if axis == 0:
        im = np.frombuffer(im, dtype="uint8").reshape([-1, size[axis]])
    else:
        im = np.frombuffer(im, dtype="uint8").reshape([size[axis], -1])

    im = np.unpackbits(im, axis=axis, bitorder=bitorder).astype(bool)

    im = Image.fromarray(im[:size[1], :size[0]])
    return im


def encode_images(images: dict):
    img_block = b"\x02"

    offset = 1

    lut = {}

    for key, img in images.items():
        wh = struct.pack("ii", *img.size)
        img_bytes = img2bytes(img)
        length = 4 + len(wh) + len(img_bytes)
        length_bytes = struct.pack("i", length)
        section = length_bytes + wh + img_bytes
        lut[key] = offset
        img_block += section
        offset += length

    return lut, img_block


def encode_lut(lut, pointer_length=1):
    lut_block = b""

    for key, pointer in lut.items():
        key_byte = chr(key).encode("ascii")
        pointer_bytes = struct.pack("{}i".format(pointer_length), pointer)
        lut_block += (key_byte + pointer_bytes)

    lut_length = len(lut_block) + 4 + 1
    lut_length_bytes = struct.pack("i", lut_length)

    lut_block = b"\x01" + lut_length_bytes + lut_block

    return lut_block


def encode_metadata(metadata: dict):
    metadata_block = b''

    for key, value in metadata.items():
        if key == "version":
            continue
        elif key == "yi_type":
            if value == "img":
                metadata_block += b"\x01\x00"
            elif value == "font":
                metadata_block += b"\x01\x01"
            else:
                raise ValueError(f"Unknown yi type: {value}")
        elif key == "img_count":
            metadata_block += (b"\x02" + chr(value).encode("ascii"))
        elif key == "img_encoding":
            if value == "HLSB":
                metadata_block += b"\x03\x03"
            elif value == "HMSB":
                metadata_block += b"\x03\x04"
            elif value == "VLSB":
                metadata_block += b"\x03\x00"
            else:
                raise ValueError(f"Unknown encoding: {value}") 
        elif key == "font_encoding":
            if value == "ascii":
                metadata_block += b"\x04\x00"
            else:
                raise ValueError(f"Unknown encoding: {value}")
        elif key == "max_size":
            metadata_block += (b"\x05" + struct.pack("ii", *value))
        
    version_section = chr(metadata["version"][0]).encode("ascii") + chr(metadata["version"][1]).encode("ascii")
    metadata_length = chr(2 + len(version_section) + len(metadata_block)).encode("ascii")
    metadata_block = b"\x00" + version_section + metadata_length + metadata_block

    return metadata_block