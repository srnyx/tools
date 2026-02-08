import os
import sys
import threading
import json
import shutil                                     # added
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageOps

# Parallel config
max_workers = min(32, (os.cpu_count() or 1) * 4)  # tuned for IO-heavy work

# Visual bar length (characters inside the [....])
BAR_LENGTH = 20
# Progress display width will be computed after we know total_files
PROGRESS_COL_WIDTH = None

# Colors
red = "\033[31m"
green = "\033[32m"
blue = "\033[34m"
reset = "\033[0m"

# Load config
if not os.path.exists("config.json"):
    print(f"{red}Config file config.json not found. Please create it with the necessary settings.{reset}")
    sys.exit(1)
with open("config.json", 'r') as f:
    config = json.load(f).get("optimization", {})
    original_folder = config.get("original_folder", "original")
    optimized_folder = config.get("optimized_folder", "optimized")
    quality = config.get("quality", 85)
    resizing = config.get("resizing", {})
    resizing_enabled = resizing.get("enabled", True)
    resizing_max_width = resizing.get("max_width", 4096)
    resizing_max_height = resizing.get("max_height", 3072)
    resizing_upscale = resizing.get("upscale", False)

# Delete existing optimized_folder
if os.path.exists(optimized_folder):
    try:
        shutil.rmtree(optimized_folder)
    except Exception as e:
        print(f"{red}Failed to remove optimized folder {optimized_folder}: {e}{reset}")

# Stats (thread-safe updates)
stats_lock = threading.Lock()
stats = {
    'success': 0,
    'fail': 0,
    'resized': 0,
    'processed': 0,
    'total_original_bytes': 0,
    'total_optimized_bytes': 0,
}

VALID_EXTS = (".jpg", ".jpeg", ".tiff", ".png")

# Determine resampling filter in a backward/forward-compatible way
RESAMPLE = None
resampling_attr = getattr(Image, 'Resampling', None)
if resampling_attr is not None:
    RESAMPLE = getattr(resampling_attr, 'LANCZOS', None)
if RESAMPLE is None:
    RESAMPLE = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))


def human_readable_bytes(num_bytes):
    """Return a human-readable string for bytes (GB/MB/KB/bytes)."""
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0 or unit == 'TB':
            if unit == 'bytes':
                return f"{num_bytes} {unit}"
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def print_progress_bar(current, total, bar_length=BAR_LENGTH):
    """Return a fixed-width progress bar string (no newline).

    The returned string is exactly PROGRESS_COL_WIDTH characters (not counting color codes),
    so the caller can write one space and then the file message and the message will
    always start in the same column.
    """
    global PROGRESS_COL_WIDTH
    if PROGRESS_COL_WIDTH is None:
        # Fallback to a reasonable width if not computed yet
        # (this should not happen in normal runs since we compute it before processing)
        PROGRESS_COL_WIDTH = len(f"[{'#'*bar_length}] 0/0 (0%)")

    if total <= 0:
        # return an empty padded area
        visible = ''
    else:
        frac = current / total
        filled = int(round(bar_length * frac))
        bar = '#' * filled + '-' * (bar_length - filled)
        percent = int(round(frac * 100.0))  # no decimals per user request
        # build visible without trailing spaces so adding one single space later yields
        # exactly one space between progress and the file message
        visible = f"[{bar}] {current}/{total} ({percent}%)"

    # Pad/truncate the visible text to PROGRESS_COL_WIDTH (visible length only)
    if len(visible) < PROGRESS_COL_WIDTH:
        padded = visible.ljust(PROGRESS_COL_WIDTH)
    else:
        padded = visible[:PROGRESS_COL_WIDTH]
    # Return with color codes applied around the padded text
    return f"{blue}{padded}{reset}"


def process_image(original_path, optimized_path):
    """Process a single image: resize/optimize and return stats and a log message."""
    try:
        # Ensure output dir exists
        os.makedirs(os.path.dirname(optimized_path), exist_ok=True)

        original_size = os.path.getsize(original_path)

        with Image.open(original_path) as img:
            # Ensure EXIF orientation is applied so portrait images aren't rotated
            img = ImageOps.exif_transpose(img)

            # Try to get EXIF and remove orientation tag so saved file won't contain a leftover tag
            exif = None
            try:
                if hasattr(img, 'getexif'):
                    exif = img.getexif()
                    # Remove orientation tag (274) if present
                    if exif is not None and 274 in exif:
                        try:
                            del exif[274]
                        except Exception:
                            # ignore if deletion fails
                            pass
            except Exception:
                exif = None

            width, height = img.size
            should_resize = False
            if resizing_enabled:
                if not resizing_upscale and width <= resizing_max_width and height <= resizing_max_height:
                    should_resize = False
                else:
                    if width > resizing_max_width or height > resizing_max_height or resizing_upscale:
                        should_resize = True

            if should_resize:
                ratio = min(resizing_max_width / width, resizing_max_height / height)
                new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
                # Use high-quality resampling
                try:
                    img = img.copy()
                    img.thumbnail(new_size, RESAMPLE)
                except Exception:
                    img = img.resize(new_size, RESAMPLE)

            # Handle saving differences for JPEG (no alpha channel)
            ext = os.path.splitext(optimized_path)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                if img.mode in ('RGBA', 'LA'):
                    # Paste onto white background to remove alpha
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    alpha = img.split()[-1]
                    background.paste(img, mask=alpha)
                    img_to_save = background
                else:
                    img_to_save = img.convert('RGB') if img.mode != 'RGB' else img
                # Save JPEG with sanitized EXIF if available to avoid keeping orientation tag
                try:
                    if exif is not None:
                        try:
                            exif_bytes = exif.tobytes()
                        except Exception:
                            exif_bytes = None
                        if exif_bytes:
                            img_to_save.save(optimized_path, optimize=True, quality=quality, exif=exif_bytes)
                        else:
                            img_to_save.save(optimized_path, optimize=True, quality=quality)
                    else:
                        img_to_save.save(optimized_path, optimize=True, quality=quality)
                except Exception:
                    # Fallback without exif parameter if Pillow version doesn't support it
                    img_to_save.save(optimized_path, optimize=True, quality=quality)
            elif ext == '.png':
                # PNG: optimize; quality parameter is not used for PNG by Pillow
                img.save(optimized_path, optimize=True)
            else:
                # Fallback: let Pillow decide format from extension
                img.save(optimized_path)

        optimized_size = os.path.getsize(optimized_path) if os.path.exists(optimized_path) else 0

        # Compute reduction
        saved_bytes = max(0, original_size - optimized_size)
        percent = (saved_bytes / original_size * 100.0) if original_size > 0 else 0.0

        # Show original path relative to the original folder (remove leading 'original/')
        rel_original = os.path.relpath(original_path, original_folder)

        msg = (f"{green}{rel_original}"
               f"{(' (resized)' if should_resize else '')}"
               f" - {human_readable_bytes(original_size)} -> {human_readable_bytes(optimized_size)} ({percent:.1f}% reduction){reset}")

        # Update stats
        with stats_lock:
            stats['success'] += 1
            if should_resize:
                stats['resized'] += 1
            stats['processed'] += 1
            stats['total_original_bytes'] += original_size
            stats['total_optimized_bytes'] += optimized_size

        return True, msg

    except Exception as e:
        with stats_lock:
            stats['fail'] += 1
            stats['processed'] += 1
        msg = f"{red}Error optimizing {original_path}: {e}{reset}"
        return False, msg


# Collect files to process
files_to_process = []
for root, dirs, files in os.walk(original_folder):
    for file in files:
        if file.lower().endswith(VALID_EXTS):
            original_path = os.path.join(root, file)
            relative_path = os.path.relpath(original_path, original_folder)
            optimized_path = os.path.join(optimized_folder, relative_path)
            files_to_process.append((original_path, optimized_path))

total_files = len(files_to_process)
# Compute a tight progress column width based on BAR_LENGTH and total_files so the
# progress area is no wider than necessary and the file message begins one space later.
PROGRESS_COL_WIDTH = len(f"[{'#'*BAR_LENGTH}] {total_files}/{total_files} (100%)")

print(f"{blue}Starting image optimization process on {total_files} files with {max_workers} workers...{reset}")

# Run in parallel
with ThreadPoolExecutor(max_workers=max_workers) as ex:
    future_to_file = {ex.submit(process_image, o, p): (o, p) for o, p in files_to_process}
    for future in as_completed(future_to_file):
        success_flag, message = future.result()
        # Update progress bar (read thread-safe processed count)
        with stats_lock:
            current = stats['processed']
        # Write progress and message together so message always starts in the same column
        progress_str = print_progress_bar(current, total_files)
        # Use carriage return to overwrite line and then write progress + a single space + message + newline
        sys.stdout.write('\r' + progress_str + ' ' + message + '\n')
        sys.stdout.flush()

# Move to next line after progress bar
sys.stdout.write("\n")

# Final summary
success = stats['success']
fail = stats['fail']
resized = stats['resized']
orig_bytes = stats['total_original_bytes']
opt_bytes = stats['total_optimized_bytes']
bytes_saved = max(0, orig_bytes - opt_bytes)
percent_saved = (bytes_saved / orig_bytes * 100.0) if orig_bytes > 0 else 0.0

print(f"{blue}Successfully optimized {success} files with {fail} failures ({resized} images resized){reset}")
print(f"{blue}Total size: {human_readable_bytes(orig_bytes)} -> {human_readable_bytes(opt_bytes)}, "
      f"saved {human_readable_bytes(bytes_saved)} ({percent_saved:.1f}% total reduction){reset}")
