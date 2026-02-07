# Optimize Photos

A script to optimize all images in the same directory and its subdirectories

*GitHub Copilot wrote 90% of this, I was in a rush lol*

## `config.json`

```json
{
  "original_folder": "original",
  "optimized_folder": "optimized",
  "quality": 25,
  
  "resizing": {
    "enabled": true,
    "max_width": 4096,
    "max_height": 3072,
    "upscale": false
  }
}
```

- **`original_folder`:** The folder where the original images are located
- **`optimized_folder`:** The folder where the optimized images will be saved
- **`quality`:** The quality of the optimized images (0-100)
- **`resizing`:** Options for image resizing
  - **`enabled`:** Whether to resize images
  - **`max_width`:** The maximum width of the optimized images
  - **`max_height`:** The maximum height of the optimized images
  - **`upscale`:** Whether to upscale images that are smaller than the max dimensions
