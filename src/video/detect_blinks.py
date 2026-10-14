
import csv
import json
import glob
import os
from pathlib import Path

# Initial thresholds for exploratory testing.
# Validate these against the video before using the results.
BLINK_THRESHOLD = 0.50
MIN_BLINK_DURATION = 0.03
MAX_BLINK_DURATION = 0.60
MERGE_GAP = 0.10

files = glob.glob("output/*visual_analysis.json")

if not files:
    raise FileNotFoundError("No visual-analysis JSON found.")

json_path = max(files, key=os.path.getmtime)

with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

frames = data.get("frames", [])
events = []

active = False
start_time = None
peak_score = 0.0
last_time = None

for frame in frames:
    timestamp = frame["timestamp_seconds"]
    face = frame.get("face", {})
    shapes = face.get("blendshapes", {})

    if not face.get("detected", False):
        # Missing face data must not be interpreted as a blink.
        if active and start_time is not None and last_time is not None:
            duration = last_time - start_time
            if MIN_BLINK_DURATION <= duration <= MAX_BLINK_DURATION:
                events.append({
                    "start_seconds": round(start_time, 3),
                    "end_seconds": round(last_time, 3),
                    "duration_seconds": round(duration, 3),
                    "peak_score": round(peak_score, 3),
                    "status": "candidate",
                    "note": "Face lost during sequence; verify manually"
                })

        active = False
        start_time = None
        peak_score = 0.0
        last_time = None
        continue

    left = shapes.get("eyeBlinkLeft")
    right = shapes.get("eyeBlinkRight")

    if not isinstance(left, (int, float)) or not isinstance(
        right, (int, float)
    ):
        continue

    score = max(float(left), float(right))
    is_high = score >= BLINK_THRESHOLD

    if is_high:
        if not active:
            active = True
            start_time = timestamp
            peak_score = score
        else:
            peak_score = max(peak_score, score)

        last_time = timestamp

    elif active:
        duration = last_time - start_time

        if MIN_BLINK_DURATION <= duration <= MAX_BLINK_DURATION:
            events.append({
                "start_seconds": round(start_time, 3),
                "end_seconds": round(last_time, 3),
                "duration_seconds": round(duration, 3),
                "peak_score": round(peak_score, 3),
                "status": "candidate",
                "note": "Review against original video"
            })

        active = False
        start_time = None
        peak_score = 0.0
        last_time = None

# Handle a candidate that continues to the final frame.
if active and start_time is not None and last_time is not None:
    duration = last_time - start_time
    if MIN_BLINK_DURATION <= duration <= MAX_BLINK_DURATION:
        events.append({
            "start_seconds": round(start_time, 3),
            "end_seconds": round(last_time, 3),
            "duration_seconds": round(duration, 3),
            "peak_score": round(peak_score, 3),
            "status": "candidate",
            "note": "Review final event against original video"
        })

output_dir = Path("output/facial_signal_reports")
output_dir.mkdir(parents=True, exist_ok=True)

csv_path = output_dir / "candidate_blinks.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as file:
    columns = [
        "start_seconds",
        "end_seconds",
        "duration_seconds",
        "peak_score",
        "status",
        "note",
    ]
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(events)

print("Source:", json_path)
print("Candidate blink events:", len(events))
print("CSV:", csv_path)
print("These are unvalidated candidates, not confirmed blink counts.")
print("Original JSON was not modified.")
