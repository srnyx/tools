import sys
import cv2
from os import listdir
from os.path import isfile, join
from tqdm import tqdm

# Get non-cropped MP4 files in directory
sys.path.append('.')
files = [f for f in listdir('.') if isfile(join('.', f)) and f.endswith('.mp4') and not f.endswith('-cropped.mp4')]

# No file found
if len(files) == 0:
    print('No mp4 file found')
    sys.exit(1)
# Multiple files found
if len(files) != 1:
    print('More than one mp4 file found')
    sys.exit(1)

# Open the video
file = files[0]
cap = cv2.VideoCapture(file)

# Characteristics from original video
w_frame, h_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(cv2.CAP_PROP_FRAME_COUNT)

# Here you can define your cropping values
x, y, w, h = 0, 0, w_frame, h_frame - 48  # 48 is the taskbar height

# Output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(f'{file[:-4]}-cropped.mp4', fourcc, fps, (w, h))

count = 0
with tqdm(total=frames, desc='Cropping video', unit=' frames') as pbar:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Save cropped frame
        out.write(frame[y:y + h, x:x + w])

        # Print progress
        count += 1
        pbar.update(1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
out.release()
cv2.destroyAllWindows()
