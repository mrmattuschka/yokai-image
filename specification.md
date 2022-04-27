# Yokai Image File Specification
The Yokai Image (**.yi**) format is what I use to store images and font glyphs (of fixed size) for use with YOKAI (enter link here) and other micropython-based stuff that runs an e-paper display.****

A file stores multiple glyphs/images and consists of three blocks:
- metadata block
- a lookup table
- a series of monochrome images/glyphs (up to 256 in v0.1) stored as bitmaps, where each byte encodes 8 pixels TODO: mode?
  
**...in this exact order**


### Block specification
The first byte of a block always delimits the type:
Value | Description
--- | ---
`0x00` | Metadata block
`0x01` | Lookup table (LUT, will be loaded into a dict by YOKAI)
`0x02` | Bitmap block

### Metadata block specification

- Byte `0x00`: block type (`0x00` for metadata)
- Bytes `0x01`, `0x02`: version (major, minor)
- Byte `0x03`: block length (<=256 in v0.1 including bytes `0x00`-`0x03`)
- Byte `0x04` and onward: A series of metadata entries. Each entry consists of a type byte followed by a series of type-specific bytes. Following entries are possible:

Value | Name | length (incl. type) | Format | Description
--- | --- | --- | --- | ---
`0x00` | pointer_length | 2 | c | length of pointers used by LUT
`0x01` | yi_type | 2 | c | type of yi file: font (`0x00`) or images (`0x01`)
`0x02` | img_count | 2 | c | number of images in the file (max 256)
`0x03` | img_encoding | 2 | c | bitmap encoding as used by micropython's `framebuf` TODO add link to framebuf
`0x04` | font_encoding | 2 | c | encoding used for fonts (as of now there's only ASCII: `0x00`)
`0x05` | max_size | 9 | ii | maximum image dimensions encountered in the file in pixels (w, h)

### Lookup table

The LUT consists of a series of key-pointer pairs. 


- Byte `0x00`: block type (`0x01` for LUT)
- Bytes `0x01`-`0x05`: block length, format `i` (including `0x00` and lut_len bytes)
- Bytes `0x06` and onward: a series of key-pointer pairs (i.e. the format is `i{n}i`, where n is the pointer length). 

Key length is 1 byte for both images and fonts (this may however change if I ever add more font encodings or the option to have more images in general). For font glyphs the key corresponds to the chosen encoding's hex code for the respective glyph.  
Pointer length is fixed for a single yi file and stated in the metadata block. 
**Pointer values are relative to the bitmap block's type byte, with pointer `0x01` referring to the first byte following the type byte.**

### Bitmap block
- Byte `0x00`: block type: (`0x02` for bitmap block)
- Byte `0x01` and onward: bitmap sections. Each bitmap consists of a few info bytes and the actual bitmap data.
  - Bytes `0x00`-`0x03`: length of the bitmap section in bytes (format i)
  - Bytes `0x04`-`0x07`, `0x08`-`0x11`: width and height of image (format ii)
  - Byte `0x12` and onward: bitmap data