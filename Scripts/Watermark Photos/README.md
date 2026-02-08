# Watermark Photos

A script to put a configurable diagonal watermark on photos (in given directory and subdirectories)

*GitHub Copilot wrote 90% of this, I was in a rush lol*

## `config.json`

```json
{
  "watermark": {
    "folder": "optimized",
    
    "text": "Watermark Text",
    "rotation": 45,
    
    "font": {
      "family": "arial.ttf",
      "color": "#FFFFFF",
      "opacity": 0.5
    }
  }
}
```

- **`text`**: The watermark text to be applied to the photos
- **`font`**: The font properties for the watermark text
  - **`family`**: The font family to be used for the watermark text
  - **`size`**: The font size for the watermark text (24)
  - **`color`**: The color of the watermark text in hexadecimal format ("#FFFFFF" for white)
  - **`opacity`**: The opacity level of the watermark text (0.5 for 50% opacity)
