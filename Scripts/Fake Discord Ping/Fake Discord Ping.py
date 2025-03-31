# Adds a fake Discord ping to your inputted file (server icon)

from PIL import Image


# Get fake ping and input
ping = Image.open("ping.png")
input_png = Image.open("input.png")

# Paste the fake ping
input_png.paste(ping, (0, 0), ping)

# Save the new icon
input_png.save("output.png")

print("Fake ping added to input.png and saved as output.png")
