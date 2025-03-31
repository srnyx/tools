# Adds a fake Discord ping to your inputted file (server icon)

from PIL import Image
from PIL import ImageSequence


ping = Image.open("ping.png")


def png():
    # Get input
    try:
        input_png = Image.open("input.png")
    except FileNotFoundError:
        return False

    # Resize ping to same size as input
    sized_ping = ping.resize(input_png.size)

    # Paste the fake ping
    input_png.paste(sized_ping, (0, 0), sized_ping)

    # Save the new icon
    input_png.save("output.png")

    print("PNG | Fake ping added to input.png and saved as output.png")
    return True


def gif():
    # Get frames
    try:
        frames = [frame.copy() for frame in ImageSequence.Iterator(Image.open("input.gif"))]
    except FileNotFoundError:
        return False

    # Resize ping to same size as frames
    sized_ping = ping.resize(frames[0].size)

    # Paste the fake ping in each frame
    new_frames = []
    for frame in frames:
        frame = frame.convert("RGBA")
        frame.paste(sized_ping, (0, 0), sized_ping)
        new_frames.append(frame)

    # Save the new icon
    new_frames[0].save("output.gif", save_all=True, append_images=new_frames[1:])

    print("GIF | Fake ping added to input.gif and saved as output.gif")
    return True


# PNG
if not png():
    print("PNG | No input.png found")

# GIF
if not gif():
    print("GIF | No input.gif found")
