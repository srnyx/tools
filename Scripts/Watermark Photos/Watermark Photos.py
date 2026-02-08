import os
import sys
import json
import math
import hashlib
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont

# Colors
red = "\033[31m"
green = "\033[32m"
blue = "\033[34m"
reset = "\033[0m"

# cap to keep font rasterization reasonable
MAX_FONT = 2048

# Visual bar length (characters inside the [....])
BAR_LENGTH = 20
# Progress display width will be computed after we know total_files
PROGRESS_COL_WIDTH = None


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
    font_family = font.get("family", "arial.ttf")
    opacity = font.get("opacity", 0.5)
    font_color = hex_to_rgba(font.get("color", "#FFFFFF"), opacity)

# create a simple on-disk cache for watermark layers keyed by settings + image size
cache_dir = os.path.join(folder, ".watermark_cache")
try:
    os.makedirs(cache_dir, exist_ok=True)
except Exception:
    cache_dir = None

# small in-process font cache to avoid repeated expensive truetype loads
_FONT_CACHE = {}

# Allow processing intentionally large images — disables Pillow's decompression-bomb check.
# Set to a numeric value instead of None if you want a hard limit.
Image.MAX_IMAGE_PIXELS = None

# Determine resampling filter in a backward/forward-compatible way
RESAMPLE = None
_resampling_attr = getattr(Image, 'Resampling', None)
if _resampling_attr is not None:
    RESAMPLE = getattr(_resampling_attr, 'LANCZOS', None)
if RESAMPLE is None:
    RESAMPLE = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))


# --- New helper: simplified and faster watermark creation + cache save/load ---
def create_watermark_layer(image_size, cache_key_obj):
    # quick return if nothing to draw
    if not text:
        return Image.new("RGBA", image_size, (255, 255, 255, 0))

    cache_path = None
    if cache_dir:
        key_bytes = json.dumps(cache_key_obj, sort_keys=True).encode("utf-8")
        sha = hashlib.sha1(key_bytes).hexdigest()
        cache_path = os.path.join(cache_dir, f"{sha}.png")
        if os.path.exists(cache_path):
            try:
                cached = Image.open(cache_path).convert("RGBA")
                if cached.size == image_size:
                    return cached
                else:
                    try:
                        os.remove(cache_path)
                    except Exception:
                        pass
            except Exception:
                try:
                    os.remove(cache_path)
                except Exception:
                    pass

    # create transparent watermark layer
    watermark = Image.new("RGBA", image_size, (255, 255, 255, 0))

    # simple render flow (multi-line centered)
    lines = text.splitlines()
    angle = rotation if isinstance(rotation, (int, float)) else -45

    # render at a reasonably large but capped size to avoid extremely slow font rasterization
    diag = int(math.hypot(image_size[0], image_size[1]))
    base_font_size = max(64, min(int(diag * 0.5), MAX_FONT))

    # reuse loaded fonts in this process
    font_cache_key = (font_family, base_font_size)
    try:
        base_font = _FONT_CACHE.get(font_cache_key)
        if base_font is None:
            base_font = ImageFont.truetype(font_family, base_font_size)
            _FONT_CACHE[font_cache_key] = base_font
    except Exception:
        print(f"{red}Warning: failed to load font '{font_family}' at size {base_font_size}, using default font{reset}")
        base_font = ImageFont.load_default()

    temp = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp)
    line_sizes = []
    for line in lines:
        if hasattr(td, "textbbox"):
            l, t, r, b = td.textbbox((0, 0), line, font=base_font)
            w, h = r - l, b - t
        else:
            mask = base_font.getmask(line)
            w, h = mask.size
        line_sizes.append((w, h))

    max_w = max((w for w, h in line_sizes), default=0)
    ascent, descent = base_font.getmetrics()
    line_h = ascent + descent
    spacing = max(1, int(getattr(base_font, "size", line_h) * 0.15))
    total_h = sum((h if h > 0 else line_h) for _, h in line_sizes) + spacing * (len(lines) - 1)

    # slightly larger bottom padding to avoid clipping
    font_size_est = getattr(base_font, "size", 12)
    pad_top = max(6, font_size_est // 12)
    pad_bottom = pad_top + max(6, int(font_size_est * 0.15))

    tw = max(1, int(max_w + pad_top * 2))
    th = max(1, int(total_h + pad_top + pad_bottom))

    text_layer = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)
    y = pad_top + int((th - pad_top - pad_bottom - total_h) / 2)
    for i, line in enumerate(lines):
        w, h = line_sizes[i]
        if h == 0:
            h = line_h
        x = int((tw - w) / 2)
        draw.text((x, y), line, font=base_font, fill=font_color)
        y += h + spacing

    # safety: if drawing touches bottom, expand a little
    bbox_after = text_layer.getbbox()
    if bbox_after:
        _, _, _, bottom = bbox_after
        if bottom >= text_layer.height - 1:
            extra = max(4, int(font_size_est * 0.1))
            new_th = text_layer.height + extra
            new_layer = Image.new("RGBA", (text_layer.width, new_th), (255, 255, 255, 0))
            new_layer.paste(text_layer, (0, 0))
            text_layer = new_layer

    # compute rotated footprint using analytic bounding-box estimate (avoids an extra rotate)
    angle_rad = math.radians(angle % 360)
    cos_a = abs(math.cos(angle_rad))
    sin_a = abs(math.sin(angle_rad))
    rot_w = text_layer.width * cos_a + text_layer.height * sin_a
    rot_h = text_layer.width * sin_a + text_layer.height * cos_a

    if rot_w == 0 or rot_h == 0:
        scale = 1.0
    else:
        max_frac = 0.99
        scale = min((image_size[0] * max_frac) / rot_w, (image_size[1] * max_frac) / rot_h)
        scale = max(0.01, scale)

    if abs(scale - 1.0) > 0.001:
        new_w = max(1, int(text_layer.width * scale))
        new_h = max(1, int(text_layer.height * scale))
        text_layer = text_layer.resize((new_w, new_h), resample=RESAMPLE)

    rotated = text_layer.rotate(angle, expand=True)
    bbox = rotated.getbbox()
    if bbox:
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
    else:
        cx = rotated.width / 2.0
        cy = rotated.height / 2.0
    paste_x = int(image_size[0] / 2.0 - cx)
    paste_y = int(image_size[1] / 2.0 - cy)
    watermark.paste(rotated, (paste_x, paste_y), rotated)

    # simpler cache save (faster): single save, best-effort
    if cache_path:
        try:
            watermark.save(cache_path)
        except Exception:
            pass

    return watermark
# --- End helper ---


# New worker function for parallel processing (must be module-level for ProcessPoolExecutor)
def process_image(image_path):
    try:
        image = Image.open(image_path).convert("RGBA")
        watermark = create_watermark_layer((image.width, image.height), {
            "w": image.width,
            "h": image.height,
        })
        result = Image.alpha_composite(image, watermark)
        extension = os.path.splitext(image_path)[1].lower()
        if extension in ('.jpg', '.jpeg'):
            result.convert("RGB").save(image_path, quality=95)
        else:
            result.save(image_path)
        return image_path, True, None
    except Exception as e:
        return image_path, False, str(e)


# Print a fixed-width progress bar string (no newline).
# The returned string is exactly PROGRESS_COL_WIDTH characters (not counting color codes),
# so the caller can write one space and then the file message and the message will
# always start in the same column.
def print_progress_bar(current, total, bar_length=BAR_LENGTH):
    global PROGRESS_COL_WIDTH
    if PROGRESS_COL_WIDTH is None:
        # Fallback to a reasonable width if not computed yet
        PROGRESS_COL_WIDTH = len(f"[{'#'*bar_length}] 0/0 (0%)")

    if total <= 0:
        visible = ''
    else:
        frac = current / total
        filled = int(round(bar_length * frac))
        bar = '#' * filled + '-' * (bar_length - filled)
        percent = int(round(frac * 100.0))
        visible = f"[{bar}] {current}/{total} ({percent}%)"

    # Pad/truncate the visible text to PROGRESS_COL_WIDTH (visible length only)
    if len(visible) < PROGRESS_COL_WIDTH:
        padded = visible.ljust(PROGRESS_COL_WIDTH)
    else:
        padded = visible[:PROGRESS_COL_WIDTH]
    return f"{blue}{padded}{reset}"

# --- Main entry: gather images and run in parallel ---
if __name__ == "__main__":
    # Collect image files while skipping the cache directory
    image_paths = []
    for root, dirs, files in os.walk(folder):
        if '.watermark_cache' in dirs:
            dirs.remove('.watermark_cache')
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                image_paths.append(os.path.join(root, file))

    # Compute progress widths like Optimize Photos does so the message column lines up
    total_files = len(image_paths)
    PROGRESS_COL_WIDTH = len(f"[{'#'*BAR_LENGTH}] {total_files}/{total_files} (100%)")
    # Decide how many worker processes to use: use cpu_count - 1 (leave one core free), min 1
    cpu = os.cpu_count() or 1
    workers = max(1, cpu - 1)

    print(f"{blue}Starting watermarking process on {total_files} files in {folder} with {workers} workers...{reset}")

    success = 0
    fail = 0
    processed = 0

    with ProcessPoolExecutor(max_workers=workers) as exe:
        futures = {exe.submit(process_image, p): p for p in image_paths}
        for fut in as_completed(futures):
            img, ok, err = fut.result()
            # build a relative path for nicer messages
            try:
                rel = os.path.relpath(img, folder)
            except Exception:
                rel = img

            if ok:
                success += 1
                message = f"{green}{rel}{reset}"
            else:
                fail += 1
                message = f"{red}Error processing {rel}: {err}{reset}"

            processed += 1
            # Write progress and message together so message always starts in the same column
            progress_str = print_progress_bar(processed, total_files)
            sys.stdout.write('\r' + progress_str + ' ' + message + '\n')
            sys.stdout.flush()

    # Move to next line after progress bar
    sys.stdout.write("\n")

    # Delete cache directory after processing all images
    if cache_dir:
        try:
            shutil.rmtree(cache_dir)
        except Exception as e:
            print(f"{red}Failed to delete watermark cache folder {cache_dir}: {e}{reset}")

    print(f"{blue}Successfully watermarked {success} images ({fail} failures){reset}")
