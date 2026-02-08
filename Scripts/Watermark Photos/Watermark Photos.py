# A script to put a configurable diagonal watermark on photos (in given directory and subdirectories)

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

# Colors
red = "\033[31m"
green = "\033[32m"
blue = "\033[34m"
reset = "\033[0m"


# Convert hex color + opacity to an RGBA tuple
def hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join([c * 2 for c in h])
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    a = int(alpha * 255)
    return r, g, b, a


# Load config
if not os.path.exists("config.json"):
    print(f"{red}Config file config.json not found! Please create it with the necessary settings{reset}")
    sys.exit(1)
with open("config.json", 'r') as f:
    config = json.load(f).get("watermark", {})
    folder = config.get("folder")
    text = config.get("text", "Watermark Text")
    rotation = config.get("rotation", 45)
    font = config.get("font", {})
    font_family = font.get("family", "arial.ttf")   # string path/name of font
    font_size = font.get("size", 24)
    opacity = font.get("opacity", 0.5)
    font_color = hex_to_rgba(font.get("color", "#FFFFFF"), opacity)
if not folder or not os.path.exists(folder):
    print(f"{red}Folder '{folder}' not found! Please check the config file{reset}")
    sys.exit(1)

# Walk through the directory and add watermark to each image
print(f"{blue}Processing images in folder: {folder}{reset}")
success = 0
fail = 0
for root, dirs, files in os.walk(folder):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            image_path = os.path.join(root, file)
            try:
                image = Image.open(image_path).convert("RGBA")
                # create a transparent watermark layer
                watermark = Image.new("RGBA", image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark)
                # load font with a fallback to the default font
                try:
                    font_obj = ImageFont.truetype(font_family, font_size)
                except Exception:
                    font_obj = ImageFont.load_default()

                # Create a separate transparent image for the (possibly multiline) text, draw centered lines, rotate, then paste centered.
                lines = text.splitlines() if text else []

                # helper temp draw to measure text reliably
                temp_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_img)

                line_sizes = []
                for line in lines:
                    if hasattr(temp_draw, "textbbox"):
                        l, t, r, b = temp_draw.textbbox((0, 0), line, font=font_obj)
                        w = r - l
                        h = b - t
                    elif hasattr(temp_draw, "textsize"):
                        w, h = temp_draw.textsize(line, font=font_obj)
                    else:
                        try:
                            mask = font_obj.getmask(line)
                            w, h = mask.size
                        except Exception:
                            w = len(line) * (font_size // 2) or font_size
                            h = font_size
                    line_sizes.append((w, h))

                max_width = max((w for w, h in line_sizes), default=0)
                # determine line height using metrics when available, otherwise use measured heights
                try:
                    ascent, descent = font_obj.getmetrics()
                    default_line_height = ascent + descent
                except Exception:
                    default_line_height = max((h for w, h in line_sizes), default=font_size)
                # spacing between lines (20% of font size as a sensible default)
                spacing = max(1, int(font_size * 0.2))
                total_height = sum((h if h > 0 else default_line_height) for _, h in line_sizes) + spacing * (len(lines) - 1)

                padding = max(10, font_size // 2)
                text_img_w = int(max_width + padding * 2)
                text_img_h = int(total_height + padding * 2)
                text_layer = Image.new("RGBA", (text_img_w, text_img_h), (255, 255, 255, 0))
                text_draw = ImageDraw.Draw(text_layer)

                # draw each line centered horizontally; center block vertically inside padded area
                y = padding + int((text_img_h - padding * 2 - total_height) / 2)
                for i, line in enumerate(lines):
                    line_w, line_h = line_sizes[i]
                    if line_h == 0:
                        line_h = default_line_height
                    x = int((text_img_w - line_w) / 2)
                    text_draw.text((x, y), line, font=font_obj, fill=font_color)
                    y += line_h + spacing

                # rotate the text image to make the watermark diagonal
                angle = rotation if isinstance(rotation, (int, float)) else -45
                rotated = text_layer.rotate(angle, expand=True)
                # compute center of the visible (non-transparent) content in the rotated image
                bbox = rotated.getbbox()
                if bbox:
                    content_cx = (bbox[0] + bbox[2]) / 2.0
                    content_cy = (bbox[1] + bbox[3]) / 2.0
                else:
                    # fallback to geometric center of rotated image
                    content_cx = rotated.width / 2.0
                    content_cy = rotated.height / 2.0
                # paste so the content center aligns with the image center
                paste_x = int(image.width / 2.0 - content_cx)
                paste_y = int(image.height / 2.0 - content_cy)
                watermark.paste(rotated, (paste_x, paste_y), rotated)
                watermarked_image = Image.alpha_composite(image, watermark)

                # JPEG/JPG does not support alpha — flatten to RGB before saving.
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    rgb_image = watermarked_image.convert("RGB")
                    rgb_image.save(image_path, quality=95)
                else:
                    watermarked_image.save(image_path)

                print(f"{green}Watermarked {image_path}{reset}")
                success += 1
            except Exception as e:
                print(f"{red}Error processing {image_path}: {e}{reset}")
                fail += 1

print(f"{blue}Successfully watermarked {success} images ({fail} failures){reset}")
