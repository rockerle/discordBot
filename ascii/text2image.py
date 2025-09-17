from PIL import Image, ImageDraw, ImageFont

ubuntu_fallback_font = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'


def draw(text: str):
    width = 300
    height = 100
    font_size = 30
    font: ImageFont.truetype

    try:
        font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', font_size)
    except OSError as e:
        font = ImageFont.truetype(ubuntu_fallback_font, font_size)

    text_length_px = font.getlength(text)
    text_box = font.getbbox(text)
    print("Text " + text + " " + str(font_size) + " is " + str(text_length_px) + " pixel wide")
    print("getBox of " + text + ": \n")
    print(text_box)

    im = Image.new('RGBA', (int(text_length_px), int(text_box[3])), (255, 255, 255, 255))
    drawing = ImageDraw.Draw(im)
    drawing.text((0, 0), text, (0, 0, 0), font=font)
    return im

