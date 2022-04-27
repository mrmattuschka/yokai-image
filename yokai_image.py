import struct

MAJOR = 0
MONO_VLSB = 0
MONO_HLSB = 3
MONO_HMSB = 4

def read_char(file):
    return int.from_bytes(file.read(1), "little")


def decode_metadata(file):
    
    offset = file.tell()
    block_type = read_char(file)
    assert block_type == 0x00
    
    v_major, v_minor = read_char(file), read_char(file)
    assert v_major == MAJOR
    
    block_length = read_char(file)
    
    metadata = {
        "version": (v_major, v_minor),
        "metadata_length": block_length
    }
    
    while file.tell() < offset + block_length:
        section_type = read_char(file)
        
        if section_type == 0x00:
            metadata["pointer_length"] = read_char(file)
        elif section_type == 0x01:
            yi_type = read_char(file)
            if yi_type == 0x00:
                metadata["yi_type"] = "img"
            elif yi_type == 0x01:
                metadata["yi_type"] = "font"
            else:
                raise NotImplementedError("Unknown yi type: {}".format(yi_type))
        elif section_type == 0x02:
            metadata["img_count"] = read_char(file)
        elif section_type == 0x03:
            metadata["img_encoding"] = read_char(file)
        elif section_type == 0x04:
            font_encoding = read_char(file)
            if font_encoding == 0x00:
                metadata["font_encoding"] = "ascii"
            else:
                raise NotImplementedError("Unknown font encoding: {}".format(font_encoding))
        elif section_type == 0x05:
            wh = file.read(struct.calcsize("2i"))
            w, h = struct.unpack("2i", wh)
            metadata["max_size"] = (w, h)
    
    return metadata


def decode_lut(file, metadata):
    offset = metadata["metadata_length"]
    yi_type = metadata["yi_type"]
    
    file.seek(offset)
    
    block_type = read_char(file)
    assert block_type == 0x01
    
    block_length = struct.unpack("i", file.read(struct.calcsize("i")))[0]
    lut = {}
    
    while file.tell() < offset + block_length:
        if yi_type == "font":
            key = file.read(1)
        elif yi_type == "img":
            key = read_char(file)
        pointer = struct.unpack("i", file.read(struct.calcsize("i")))[0]
        lut[key] = pointer

    return block_length, lut


def read_image_size(file, offset, pointer):
    file.seek(offset + pointer + 4)
    w, h = struct.unpack("ii", file.read(8))
    
    return w, h


def read_image(file, offset, pointer):
    file.seek(offset + pointer)
    section_length = struct.unpack("i", file.read(4))[0]
    w, h = struct.unpack("ii", file.read(8))
    
    img_data = file.read(section_length - 12)
    return (w, h), img_data


def read_image_into(file, offset, pointer, ba):
    file.seek(offset + pointer + 4)
    w, h = struct.unpack("ii", file.read(8))
    
    bytes_read = file.readinto(ba)
    return (w, h), bytes_read