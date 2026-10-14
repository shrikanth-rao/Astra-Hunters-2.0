
import csv
import math
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "output" / "facial_signal_reports" / "candidate_blinks.csv"
OUTPUT_PATH = ROOT / "output" / "facial_signal_reports" / "blink_review_contact_sheet.jpg"

# Find the source video without searching inside the virtual environment.
videos = [
    p for p in ROOT.rglob("*.mp4")
    if ".venv" not in p.parts and "node_modules" not in p.parts
]

if not videos:
    raise FileNotFoundError(
        f"No MP4 video found under {ROOT}. "
        "Place Testing Video.mp4 in the project folder or a subfolder."
    )

# Prefer the video named in our current test.
video_path = next(
    (p for p in videos if p.name.lower() == "testing video.mp4"),
    videos[0]
)

with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
    events = list(csv.DictReader(f))

cap = cv2.VideoCapture(str(video_path))
if not cap.isOpened():
    raise RuntimeError(f"Could not open video: {video_path}")

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frame_count / fps if fps else 0

thumb_width = 320
thumb_height = 180
label_height = 28
gap = 8
columns = 3
rows = len(events)

sheet_width = columns * thumb_width + (columns + 1) * gap
sheet_height = rows * (thumb_height + label_height) + (rows + 1) * gap

sheet = 255 * __import__("numpy").ones(
    (sheet_height, sheet_width, 3), dtype="uint8"
)

def get_frame(seconds):
    seconds = max(0, min(seconds, duration - 0.01))
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, frame = cap.read()

    if not ok:
        return None

    return cv2.resize(frame, (thumb_width, thumb_height))

for row, event in enumerate(events):
    start = float(event["start_seconds"])
    end = float(event["end_seconds"])
    midpoint = (start + end) / 2

    samples = [
        (max(0, start - 0.10), "BEFORE"),
        (midpoint, "EVENT"),
        (min(duration - 0.01, end + 0.10), "AFTER"),
    ]

    y = gap + row * (thumb_height + label_height + gap)

    for col, (timestamp, label) in enumerate(samples):
        x = gap + col * (thumb_width + gap)
        frame = get_frame(timestamp)

        if frame is not None:
            sheet[y:y + thumb_height, x:x + thumb_width] = frame

        text = f"{label} | {timestamp:.3f}s"
        cv2.putText(
            sheet, text, (x + 5, y + thumb_height + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1,
            cv2.LINE_AA
        )

    event_label = (
        f"Candidate {row + 1}: {start:.3f}-{end:.3f}s "
        f"(duration {end - start:.3f}s)"
    )
    cv2.putText(
        sheet, event_label, (gap, y - 2 if y >= 18 else y + 15),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 40), 1,
        cv2.LINE_AA
    )

cap.release()
cv2.imwrite(str(OUTPUT_PATH), sheet)

print(f"Video: {video_path}")
print(f"Candidates reviewed: {len(events)}")
print(f"Contact sheet: {OUTPUT_PATH}")
print("Open the image and compare each BEFORE / EVENT / AFTER row.")
