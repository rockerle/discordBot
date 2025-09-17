from PIL import Image

from ascii import text2image
from ascii import image2braille

top_text_img: Image
bottom_text_img: Image


async def convert(src, width, threshold, invert, iT, ttext: str = None, btext: str = None):
    top, bottom = "", ""
    if ttext:
        ttext_img = text2image.draw(ttext)
        top = image2braille.image_to_braille("", width, threshold, iT, png=ttext_img)
    if btext:
        btext_img = text2image.draw(btext)
        bottom = image2braille.image_to_braille("", width, threshold, iT, png=btext_img)
    res = image2braille.image_to_braille(src, width, threshold, invert)
    return top + "\n" + res + "\n" + bottom

