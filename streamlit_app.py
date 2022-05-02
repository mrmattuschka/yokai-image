import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import yokai_image_utils as yu
import string
import tempfile

### SETUP ###

font_urls = {
    "Roboto": "https://github.com/googlefonts/roboto-flex/raw/main/fonts/RobotoFlex%5BGRAD%2CXOPQ%2CXTRA%2CYOPQ%2CYTAS%2CYTDE%2CYTFI%2CYTLC%2CYTUC%2Copsz%2Cslnt%2Cwdth%2Cwght%5D.ttf",
    "RobotoMono": "https://github.com/googlefonts/RobotoMono/raw/main/fonts/variable/RobotoMono%5Bwght%5D.ttf",
    "Nunito": "https://github.com/googlefonts/nunito/raw/main/fonts/variable/Nunito%5Bwght%5D.ttf"
}

@st.cache
def get_tempdir():
    return Path(tempfile.mkdtemp())

@st.cache
def download_gfont(fontname):
    import requests
    
    dl_url = font_urls[fontname]
    local_path = get_tempdir() / f"{fontname}.ttf"

    with requests.get(dl_url) as remote_ttf, open(local_path, "wb") as local_ttf:
        local_ttf.write(remote_ttf.content)

    return str(local_path)


### BEGIN APP ###

st.title("YŌKAI image serializer")
st.caption("A tiny web-app to pack images or font faces for use with monochrome e-paper displays")

app_mode_labels = {
    "img": "Encode images",
    "font": "Encode font face",
    "view": "View encoded images"
}

app_mode = st.selectbox( # this is a dropdown
    "Choose whether to encode a series of images or a font face:",
    ["img", "font", "view"], 
    index=0,
    format_func=app_mode_labels.get
)


if app_mode == "img":
    # Encoding parameters
    img_encoding = st.selectbox(
        "Select image encoding",
        ["HLSB", "HMSB", "VLSB"],
        index=0,
        help="Image format as used by Micropython. For more info see [here](https://docs.micropython.org/en/latest/library/framebuf.html#constants)"
    )
    
    image_files = st.file_uploader(
        "Upload images:", 
        type=[".png", ".jpg", ".jpeg", ".bmp"], 
        accept_multiple_files=True
    )

    if image_files:
        st.write("Set indices to use for each image. **Image indices must be unique!**")
        
        images = []
        for image_file in image_files:
            image = Image.open(image_file)

            if image.mode == "RGBA":
                canvas = Image.new("RGBA", image.size, "WHITE") # Create a white rgba background
                canvas.paste(image, (0, 0), image)
                image = canvas
            
            image = image.convert("1")
            images.append(image)

        image_indices = []

        for default_idx, image in enumerate(images):
            col1, col2 = st.columns([1, 4])
            
            with col1:
                index = int(st.number_input("", value=default_idx, step=1))
                image_indices.append(index)

            with col2:
                st.image(image)
        
        if len(image_indices) > len(set(image_indices)): # Don't feel like requiring numpy just for this
            st.error("List indices are not unique!")
        else:
            img_set = {idx: image for idx, image in zip(image_indices, images)}
            img_bytes = yu.encode(img_set, "img", img_encoding=img_encoding)
            
            st.write("") # Little bit of spacing
            st.download_button(
                "Download encoded images",
                data=img_bytes,
                file_name="img_set.yi"
            )


elif app_mode == "font":
    col1, col2 = st.columns([3, 1])

    with col1:
        fontname = st.selectbox(
            "Choose which font to encode:",
            list(font_urls.keys()) + ["Upload custom font"]
        )

    with col2:
        fontsize = int(st.number_input("Set fontsize", value=20, step=1))

    if fontname == "Upload custom font":
        font_file = st.file_uploader("Upload TrueType font:", type=".ttf")
        if font_file is None:
            st.stop()
    else:
        font_file = download_gfont(fontname)

    font = ImageFont.truetype(font_file, size=fontsize)

    try:
        variations = [v.decode() for v in font.get_variation_names()]
        if len(variations) > 1:
            idx = variations.index("Regular") if "Regular" in variations else None

            variant = st.selectbox(
                "Your selected font supports multiple variants! Please choose which one to use:",
                variations,
                index=idx
            )
            font.set_variation_by_name(variant)
    except OSError:
        pass

    # Generate and show a preview of the text
    preview_text = st.text_input("Create a preview:", value="Haha text go brrr")

    size = font.getsize(preview_text)
    preview_image = Image.new(size=size, mode="1", color="WHITE")
    preview_draw = ImageDraw.Draw(preview_image)
    preview_draw.text((0, 0), preview_text, font=font, fill="BLACK")

    st.image(preview_image)

    # Encoding parameters
    col1, col2 = st.columns([1, 1])
    
    with col1:
        font_encoding = st.selectbox("Select text encoding:", ["ascii"], index=0)
    with col2:
        img_encoding = st.selectbox(
            "Select image encoding",
            ["HLSB", "HMSB", "VLSB"],
            index=0,
            help="Image format as used by Micropython. For more info see [here](https://docs.micropython.org/en/latest/library/framebuf.html#constants)"
        )

    img_set = yu.create_typeset(font, glyphs=string.printable, font_encoding=font_encoding)
    
    fontname, fontwght = font.getname() # Font weight seems buggy, don't use it
    fontname = fontname.replace(" ", "-")
    font_filename = f"{fontname}_{fontsize}.yi"
    
    img_bytes = yu.encode(img_set, "font", img_encoding=img_encoding)

    st.write("") # Little bit of spacing
    st.download_button(
        "Download encoded font face",
        data=img_bytes,
        file_name=font_filename
    )

elif app_mode == "view":
    yi_file = st.file_uploader("Upload .yi file:", type=".yi")
    
    if yi_file is not None:
        metadata, images = yu.decode_yi_file(yi_file)


        st.write("Encoded metadata:")
        st.json(metadata)

        st.write("Encoded images:")
        for key, image in images.items():
            col1, col2 = st.columns([1, 9])
            with col1:
                st.text(key)
            with col2:
                st.image(image)
