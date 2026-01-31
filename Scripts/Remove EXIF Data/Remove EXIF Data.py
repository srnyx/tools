import os
from PIL import Image

# Colors
red = "\033[31m"
green = "\033[32m"
blue = "\033[34m"
reset = "\033[0m"


# Remove EXIF data from images in current directory and subdirectories
print(f"{blue}Starting EXIF data removal process...")
success = 0
fail = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith((".jpg", ".jpeg", ".tiff", ".png")):
            file_path = os.path.join(root, file)
            try:
                with Image.open(file_path) as img:
                    tmp_path = file_path + ".tmp"
                    img.info.pop("exif", None)
                    img.save(tmp_path, format=img.format)
                os.replace(tmp_path, file_path)
                print(f"{green}Removed EXIF data from {file_path}")
                success += 1
            except Exception as e:
                print(f"{red}Error processing {file_path}: {e}")
                fail += 1

print(f"{blue}Successfully removed EXIF data from {success} files ({fail} failures){reset}")
