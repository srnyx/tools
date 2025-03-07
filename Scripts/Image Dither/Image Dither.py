from PIL import Image
import numpy as np

primary_color = [90, 230, 250, 255]
secondary_color = [0, 0, 0, 255]

img = Image.open('input.png')
dither = np.random.default_rng(seed=42).integers(0, 256, size=(img.height, img.width))
img = np.array(img).astype(int)
new_img = np.copy(img)
primary_color_three = primary_color[:3]
secondary_color_three = secondary_color[:3]
transparent = [0, 0, 0, 0]

for y in range(img.shape[0]): # loop thru y-values
    for x in range(img.shape[1]): # loop thru x-values
        pixel = img[y, x]
        four_values = len(pixel) == 4
        
        if four_values and pixel[3] == 0:
            new_img[y, x] = transparent
            continue
            
        gray = (img[y, x, 0] + img[y, x, 1] + img[y, x, 2]) / 3  # grayscale (average)
        dither_value = dither[y % dither.shape[0], x % dither.shape[1]]  # dither comparison value
        
        make_color = gray > dither_value
        if four_values:
            new_img[y, x] = primary_color if make_color else secondary_color
        else:
            new_img[y, x] = primary_color_three if make_color else secondary_color_three

#new_img = np.clip(new_img, 0, 255) # shouldnt be necessary since all values should be 0 or 255
Image.fromarray(new_img.astype(np.uint8)).save('output.png')
