import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import struct

__version__ = (0, 1)

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
    
    # need to factor in that image may not be a multiple of 8 in packing direction
    if axis == 0:
        im = np.frombuffer(im, dtype="uint8").reshape([-1, size[axis]])
    else:
        im = np.frombuffer(im, dtype="uint8").reshape([size[axis], -1])

    im = np.unpackbits(im, axis=axis, bitorder=bitorder).astype(bool)

    im = Image.fromarray(im[:size[1], :size[0]])
    return im


def encode_images(images: dict, encoding="HLSB"):
    img_block = b"\x02"

    offset = 1

    lut = {}

    for key, (wh, img) in images.items():
        wh = struct.pack("ii", *wh)
        img_bytes = img2bytes(img, encoding=encoding)
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


def encode(
    images: dict, 
    yi_type: str, 
    img_encoding: str = "HLSB",
    font_encoding: str = "ascii",
    pointer_length: int = 1
) -> bytes:
    metadata = {
        "version": __version__,
        "yi_type": yi_type,
        "img_encoding": img_encoding,
        "pointer_length": pointer_length,
        "img_count": len(images),
        "max_size": tuple(np.max([i[1].size for i in images.values()], 0))
    }

    if "yi_type" == "font":
        metadata["font_encoding"] = font_encoding

    lut, image_block = encode_images(images, encoding=img_encoding)
    lut_block = encode_lut(lut, pointer_length)
    metadata_block = encode_metadata(metadata)

    combined_blocks = metadata_block + lut_block + image_block

    return combined_blocks


def create_typeset(
    font: ImageFont, 
    glyphs: str, 
    font_encoding: str = "ascii", 
    invert: bool = False,
    fixed_size: bool = True
):
    images = {}

    max_size = tuple(np.max([font.getsize(g) for g in glyphs], 0))
    bg_color = not invert
    fg_color = invert

    for glyph in glyphs:
        size = max_size if fixed_size else font.getsize(glyph)
        i = Image.new(size=size, mode='1', color=bg_color)
        d = ImageDraw.Draw(i)
    
        d.text((0, 0), glyph, font=font, fill=fg_color)

        key = ord(glyph.encode(font_encoding))
        images[key] = (font.getbbox(glyph)[2:], i)

    return images


def create_imageset(
    images
):
    image_dict = {}
    for idx, image in enumerate(images):
        image = image.convert("1")
        image_dict[idx] = (image.size, image)

    return image_dict


def decode_yi_file(file):
    from yokai_image import decode_metadata, decode_lut, read_image
    images = {}
    file.seek(0)

    metadata = decode_metadata(file)
    lut_len, lut = decode_lut(file, metadata)
    img_offset = metadata["metadata_length"] + lut_len

    for key, pointer in lut.items():
        size, image_bytes = read_image(file, offset=img_offset, pointer=pointer)
        image = bytes2img(image_bytes, metadata["max_size"], encoding=metadata["img_encoding"])

        images[key] = image

    return metadata, images