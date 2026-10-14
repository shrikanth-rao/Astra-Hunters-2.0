
import csv
import json
import math
import re
from bisect import bisect_left
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output" / "integrated_reports"

HEAD_POSE_DIR = PROJECT_DIR / "output" / "head_pose_reports"
FACIAL_DIR = PROJECT_DIR / "output" / "facial_signal_reports"

# Match a measurement only when its timestamp is within 0.25 s.
MATCH_TOLERANCE_SECONDS = 0.25

# Files generated for youtube1.mp4.
HEAD_POSE_FILE = HEAD_POSE_DIR / "youtube1_head_pose_samples.csv"
BLINK_FILE = FACIAL_DIR / "candidate_blinks.csv"


# ============================================================
# CSV AND DATA HELPERS
# ============================================================

def read_csv(path):
    """Read a CSV file, returning an empty list if it is unavailable."""
    if not path:
        return []

    path = Path(path)

    if not path.exists():
        print(f"WARNING: CSV not found: {path}")
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def to_float(value):
    """Convert a value to a finite float, or None if invalid."""
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def flatten_dict(data, prefix=""):
    """Flatten nested dictionaries into CSV-friendly column names."""
    result = {}

    if not isinstance(data, dict):
        return result

    for key, value in data.items():
        name = f"{prefix}_{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten_dict(value, name))
        elif isinstance(value, (int, float, bool, str)) or value is None:
            result[name] = value

    return result


def choose_file(title, filetypes):
    """Open a file-selection dialog."""
    return filedialog.askopenfilename(
        title=title,
        initialdir=str(PROJECT_DIR),
        filetypes=filetypes,
    )


def save_csv(path, rows, columns=None):
    """Save rows to CSV, including headers for empty reports."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if columns is None:
        columns = sorted({
            key
            for row in rows
            for key in row
        })

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# TIMESTAMP ALIGNMENT
# ============================================================

def add_nearest_measurements(rows, source_rows, prefix):
    """
    Merge timestamped measurements into frame rows.

    Only measurements within MATCH_TOLERANCE_SECONDS are matched.
    Source values are prefixed to avoid column-name collisions.
    """
    if not source_rows:
        print(f"{prefix}: no source data loaded")
        return 0

    timed = []

    for item in source_rows:
        timestamp = to_float(item.get("timestamp_seconds"))

        if timestamp is not None:
            timed.append((timestamp, item))

    timed.sort(key=lambda item: item[0])
    times = [item[0] for item in timed]
    matched = 0

    for row in rows:
        timestamp = row["timestamp_seconds"]
        position = bisect_left(times, timestamp)
        candidates = []

        if position < len(timed):
            candidates.append(timed[position])

        if position > 0:
            candidates.append(timed[position - 1])

        if not candidates:
            row[f"{prefix}_matched"] = False
            continue

        nearest_time, nearest_row = min(
            candidates,
            key=lambda item: abs(item[0] - timestamp),
        )

        difference = abs(nearest_time - timestamp)

        if difference > MATCH_TOLERANCE_SECONDS:
            row[f"{prefix}_matched"] = False
            continue

        row[f"{prefix}_matched"] = True
        row[f"{prefix}_source_timestamp_seconds"] = nearest_time
        row[f"{prefix}_timestamp_difference_seconds"] = round(
            difference, 4
        )

        for key, value in nearest_row.items():
            if key != "timestamp_seconds":
                row[f"{prefix}_{key}"] = value

        matched += 1

    print(f"{prefix}: matched {matched}/{len(rows)} rows")
    return matched


# ============================================================
# VISUAL JSON PROCESSING
# ============================================================

def build_frame_rows(data):
    """Convert the visual-analysis JSON into frame-level rows."""
    frames = data.get("frames", [])

    if not frames:
        raise ValueError("The selected JSON contains no frames.")

    session_id = str(data.get("session_id") or "unknown_session")
    source = str(data.get("source") or "")
    rows = []

    for frame in frames:
        timestamp = to_float(frame.get("timestamp_seconds"))

        if timestamp is None:
            continue

        face = frame.get("face") or {}
        body = frame.get("body") or {}
        hands = frame.get("hands") or {}
        quality = frame.get("quality") or {}
        expression = face.get("expression_estimate") or {}
        blendshapes = face.get("blendshapes") or {}
        measurements = body.get("measurements") or {}

        row = {
            "session_id": session_id,
            "source_video": source,
            "timestamp_seconds": timestamp,
            "frame_index": frame.get("frame_index"),
            "face_detected": face.get("detected", False),
            "pose_detected": body.get("detected", False),
            "hand_count": hands.get("detected_count"),
            "expression_label": expression.get("label"),
            "expression_confidence": expression.get("confidence"),
            "face_quality_detected": quality.get("face_detected"),
            "pose_quality_detected": quality.get("pose_detected"),
            "hands_quality_detected": quality.get("hands_detected"),
        }

        for name, value in blendshapes.items():
            if isinstance(value, (int, float, str, bool)) or value is None:
                row[f"blendshape_{name}"] = value

        row.update(flatten_dict(measurements, "body"))
        rows.append(row)

    if not rows:
        raise ValueError("No frames had valid timestamps.")

    rows.sort(key=lambda row: row["timestamp_seconds"])

    return rows, session_id, source


# ============================================================
# REPORT GENERATION
# ============================================================

def main():
    root = tk.Tk()
    root.withdraw()

    try:
        print("Select the visual-analysis JSON for youtube1.mp4.")

        json_path = choose_file(
            "Select visual-analysis JSON for youtube1.mp4",
            [("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not json_path:
            print("Cancelled: no visual-analysis JSON selected.")
            return

        with open(json_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)

        # Check the chosen recording before integrating other data.
        source = str(data.get("source") or "")
        session_id = str(data.get("session_id") or "")

        print(f"Selected JSON: {json_path}")
        print(f"Session ID: {session_id or 'unknown'}")
        print(f"Source: {source or 'not specified'}")

        if "youtube1" not in (
            Path(json_path).name.lower() + " " + source.lower()
        ):
            confirm = messagebox.askyesno(
                "Confirm recording",
                "The selected JSON filename/source does not clearly "
                "identify youtube1.mp4.\n\n"
                "Continue only if you have verified this is the "
                "correct recording.",
            )

            if not confirm:
                print("Cancelled: recording was not confirmed.")
                return

        metrics_path = choose_file(
            "Optional: matching presentation_metrics CSV "
            "(Cancel to skip)",
            [("CSV files", "*.csv"), ("All files", "*.*")],
        )

        facial_path = choose_file(
            "Select facial_signals.csv for youtube1.mp4 "
            "(Cancel to skip)",
            [("CSV files", "*.csv"), ("All files", "*.*")],
        )

        # Always use the explicit youtube1 head-pose filename.
        head_path = str(HEAD_POSE_FILE) if HEAD_POSE_FILE.exists() else ""

        blink_path = str(BLINK_FILE) if BLINK_FILE.exists() else ""

        print("\nINPUT FILES")
        print("-----------")
        print("Visual JSON:", json_path)
        print("Metrics CSV:", metrics_path or "skipped")
        print("Facial signals CSV:", facial_path or "skipped")
        print("Head-pose CSV:", head_path or "not found")
        print("Blink candidates CSV:", blink_path or "not found")

        if not head_path:
            raise FileNotFoundError(
                "The expected head-pose file was not found:\n"
                f"{HEAD_POSE_FILE}"
            )

        # Do not silently continue with an old or mismatched head-pose file.
        if facial_path and Path(facial_path).name.lower() != "facial_signals.csv":
            print(
                "WARNING: The selected facial CSV has a different "
                "filename. Verify that it belongs to youtube1.mp4."
            )

        rows, session_id, source = build_frame_rows(data)

        # Optional metrics are only integrated if the user explicitly
        # selects the matching file.
        add_nearest_measurements(
            rows,
            read_csv(metrics_path),
            "metrics",
        )

        add_nearest_measurements(
            rows,
            read_csv(facial_path),
            "facial",
        )

        add_nearest_measurements(
            rows,
            read_csv(head_path),
            "head_pose",
        )

        # Blink candidates are events, not frame-level measurements.
        blink_events = read_csv(blink_path)

        # Make every row use the same set of columns.
        columns = sorted({
            key
            for row in rows
            for key in row
        })

        for row in rows:
            for column in columns:
                row.setdefault(column, None)

        safe_session = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            session_id or "youtube1",
        )

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = OUTPUT_DIR / f"{safe_session}_{run_id}"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Main frame-level report.
        report_path = session_dir / "final_analysis_report.csv"
        save_csv(report_path, rows, columns)

        # Separate event-level blink report.
        blink_columns = [
            "start_seconds",
            "end_seconds",
            "duration_seconds",
            "peak_score",
            "status",
            "note",
        ]

        if blink_events:
            blink_columns = list(blink_events[0].keys())

        blink_output = session_dir / "blink_candidates.csv"
        save_csv(blink_output, blink_events, blink_columns)

        # Summary report.
        start_time = rows[0]["timestamp_seconds"]
        end_time = rows[-1]["timestamp_seconds"]

        summary = {
            "session_id": session_id,
            "source_video": source,
            "frame_rows": len(rows),
            "column_count": len(columns),
            "start_seconds": start_time,
            "end_seconds": end_time,
            "duration_seconds": round(end_time - start_time, 3),
            "face_detected_rows": sum(
                str(row.get("face_detected")).lower() == "true"
                for row in rows
            ),
            "pose_detected_rows": sum(
                str(row.get("pose_detected")).lower() == "true"
                for row in rows
            ),
            "blink_candidate_events": len(blink_events),
            "timestamp_match_tolerance_seconds": (
                MATCH_TOLERANCE_SECONDS
            ),
            "metrics_csv_selected": bool(metrics_path),
            "facial_csv_selected": bool(facial_path),
            "head_pose_csv_selected": bool(head_path),
            "audio_analysis_integrated": False,
            "transcript_analysis_integrated": False,
            "slide_analysis_integrated": False,
        }

        summary_path = session_dir / "session_summary.csv"
        save_csv(summary_path, [summary], list(summary.keys()))

        # Data-quality report.
        quality_rows = []

        for column in columns:
            missing = sum(
                row.get(column) is None
                or str(row.get(column)).strip() == ""
                for row in rows
            )

            quality_rows.append({
                "column": column,
                "total_rows": len(rows),
                "missing_rows": missing,
                "missing_fraction": round(missing / len(rows), 4),
            })

        quality_path = session_dir / "data_quality_report.csv"

        save_csv(
            quality_path,
            quality_rows,
            [
                "column",
                "total_rows",
                "missing_rows",
                "missing_fraction",
            ],
        )

        print("\nREPORT GENERATION COMPLETE")
        print("--------------------------")
        print("Session:", session_id)
        print("Source:", source or "not specified")
        print("Frame rows:", len(rows))
        print("Columns:", len(columns))
        print("Blink candidate events:", len(blink_events))
        print("Final report:", report_path)
        print("Session summary:", summary_path)
        print("Data quality:", quality_path)
        print("Blink candidates:", blink_output)
        print(
            "\nNote: audio, transcript, and slide analysis are not "
            "integrated by this script."
        )
        print(
            "Blink events are unvalidated candidates, not confirmed "
            "blink counts."
        )

        messagebox.showinfo(
            "Report generated",
            f"Report created successfully.\n\n{session_dir}",
        )

    except Exception as exc:
        print(f"\nREPORT GENERATION FAILED: {exc}")

        messagebox.showerror(
            "Report generation failed",
            str(exc),
        )

        raise

    finally:
        root.destroy()


if __name__ == "__main__":
    main()
