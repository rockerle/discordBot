import requests
from PIL import Image


def image_to_braille(image_path, width=None, threshold=128, invert=False, png=None):
    """
    Converts an image to Braille ASCII art.

    Args:
        image_path (str): The path to the input image file.
        width (int, optional): The desired width of the ASCII art in characters.
                               If None, it tries to use the image's width.
        threshold (int, optional): The brightness threshold (0-255) to determine
                                   if a pixel becomes a dot. Defaults to 128.
        invert (bool, optional): If True, inverts the threshold logic (lighter
                                 pixels become dots). Defaults to False.

    Returns:
        str: The Braille ASCII art representation of the image.
    """
    if png is None:
        try:
            img = Image.open(image_path)
#        except FileNotFoundError:
#            return f"Error: Image file not found at '{image_path}'"
        except Exception as e:
            #return f"Error opening image: {e}"
            try:
                img = Image.open(requests.get(image_path, stream=True).raw)
            except Exception as e:
                return f"Error opening image: {e}"
    else:
        img = png
    # --- Image Preprocessing ---
    img = img.convert('L')  # Convert to grayscale

    # Calculate new dimensions, maintaining aspect ratio
    original_width, original_height = img.size
    aspect_ratio = original_height / original_width

    if width:
        # Braille chars are 2x4 pixels, so image width needs to be 2*chars
        new_width_pixels = width * 2
        # Calculate height ensuring it's a multiple of 4
        new_height_pixels = int(aspect_ratio * new_width_pixels / 4) * 4
    else:
        # Ensure width is a multiple of 2 and height a multiple of 4
        new_width_pixels = int(original_width / 2) * 2
        new_height_pixels = int(original_height / 4) * 4
        if new_width_pixels == 0 or new_height_pixels == 0:
            return "Error: Image too small or width not specified."

    img = img.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)
    pixels = img.load()

    # --- Braille Conversion ---
    braille_art = ""
    # Braille dot mapping (bit values for U+2800)
    # 1 8
    # 2 16
    # 4 32
    # 64 128
    braille_map = [
        [0x01, 0x08],
        [0x02, 0x10],
        [0x04, 0x20],
        [0x40, 0x80]
    ]

    for y in range(0, new_height_pixels, 4):
        for x in range(0, new_width_pixels, 2):
            braille_value = 0x2800  # Base Braille character (all dots off)

            for row in range(4):  # 4 rows in a Braille char
                for col in range(2):  # 2 columns in a Braille char
                    px_x = x + col
                    px_y = y + row

                    # Check if pixel is within bounds (though resizing should prevent this)
                    if px_x < new_width_pixels and px_y < new_height_pixels:
                        pixel_value = pixels[px_x, px_y]

                        is_dot = (pixel_value < threshold) if not invert else (pixel_value > threshold)

                        if is_dot:
                            braille_value += braille_map[row][col]

            braille_art += chr(braille_value)
        braille_art += "\n"

    return braille_art


