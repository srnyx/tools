from PIL import Image
import numpy as np

color = [150, 255, 0]

img = Image.open('input.png')
dither = np.random.default_rng(seed=42).integers(0, 256, size=(img.height, img.width))
img = np.array(img).astype(int)
new_img = np.copy(img)
color_alpha = color + [255]
transparent = [0, 0, 0, 0]

for y in range(img.shape[0]):  # loop thru y-values
    for x in range(img.shape[1]):  # loop thru x-values
        gray = (img[y, x, 0] + img[y, x, 1] + img[y, x, 2]) / 3  # grayscale (average)
        dither_value = dither[y % dither.shape[0], x % dither.shape[1]]  # dither comparison value
        new_img[y, x] = color_alpha if gray > dither_value else transparent

#new_img = np.clip(new_img, 0, 255) # shouldnt be necessary since all values should be 0 or 255
Image.fromarray(new_img.astype(np.uint8)).save('output.png')
