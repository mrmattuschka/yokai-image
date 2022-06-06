# YOKAI-Image
Lightweight tools that I use to serialize indexed images and font glyphs for use with [YOKAI](https://github.com/mrmattuschka/yokai) and other micropython-based stuff that sports an e-paper display.

Yokai-Image comes with three components:
- A decoder for binary `.yi` files, written solely in standard library python to ensure compatibility with micropython.
- A set of utilities for encoding, data wrangling and displaying to use with standard CPython (this does utilize non-standard lib packages).
- A [webapp](https://share.streamlit.io/mrmattuschka/yokai-image) powered by [streamlit](streamlit.io) to both encode and view sets of images or fonts into `.yi` files.

## Installation & Usage
### On a microcontroller running micropython (decoder only):
Copy `yokai_image.py` to your microcontroller, `import yokai_image` and hope that by then I've documented the decoder.
### Locally on a PC: 
**TODO**
### Run the Streamlit app:
`streamlit streamlit_app.py` or use the app on [streamlit.io](https://share.streamlit.io/mrmattuschka/yokai-image).

## The YOKAI Image format: `.yi`
For more info on the `.yi` format check out the [specifications](specification.md).

## Why this and not \[existing solution\]?
I'm using micropython, does it look like I make good decisions? 🤷‍♂️
