
import sys
import subprocess
from pathlib import Path


# ============================================================
# PROJECT PATHS
# This file is located in: src/video/run_all_analysis.py
# ============================================================

VIDEO_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = VIDEO_DIR.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


# ============================================================
# ANALYSIS PIPELINE
# Scripts run in the order listed below.
# ============================================================

PIPELINE_STEPS = [
    {
        "name": "Combined face, pose, and hand analysis",
        "script": "combined_pipeline.py",
        "video_argument": True,
    },
    {
        "name": "Detailed visual-analysis JSON",
        "script": "analyze_video_json.py",
        "video_argument": True,
    },
    {
        "name": "Session summary, cleaned CSV, and charts",
        "script": "analyze_session.py",
        "video_argument": False,
    },
    {
        "name": "Candidate blink detection",
        "script": "detect_blinks.py",
        "video_argument": False,
    },
    {
        "name": "Facial-signal report",
        "script": "analyze_facial_signals.py",
        "video_argument": False,
    },
    {
        "name": "Blink-review contact sheet",
        "script": "create_blink_review_sheet.py",
        "video_argument": False,
    },
]


# ============================================================
# RUN ONE ANALYSIS STEP
# ============================================================

def run_step(step, video_path, step_number, total_steps):

    script_path = VIDEO_DIR / step["script"]

    print("\n" + "=" * 70)
    print(f"STEP {step_number}/{total_steps}: {step['name']}")
    print("=" * 70)

    # Check that the script exists.
    if not script_path.is_file():
        print(f"ERROR: Script not found:\n{script_path}")
        return False

    # Use the Python interpreter from the active environment.
    command = [sys.executable, str(script_path)]

    # Pass the video path only to scripts configured to accept it.
    if step["video_argument"]:
        command.append(str(video_path))

    print(f"Script: {script_path.name}")
    print(f"Python: {sys.executable}")
    print("-" * 70)

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            check=False,
        )

    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
        return False

    except OSError as error:
        print(f"\nERROR: Could not start {script_path.name}")
        print(error)
        return False

    # Stop the pipeline if a script fails.
    if result.returncode != 0:
        print(f"\nFAILED: {script_path.name}")
        print(f"Exit code: {result.returncode}")
        print("The remaining steps will not run.")
        return False

    print(f"\nCOMPLETED: {step['name']}")
    return True


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    # Require one input video path.
    if len(sys.argv) != 2:
        print("\nUsage:")
        print(
            'python src\\video\\run_all_analysis.py '
            '"data\\raw\\presentation.mp4"'
        )
        print("\nReplace the example path with your actual video path.")
        sys.exit(1)

    # Resolve the input video path.
    video_path = Path(sys.argv[1])

    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path

    video_path = video_path.resolve()

    # Validate the video.
    if not video_path.is_file():
        print("\nERROR: Input video not found:")
        print(video_path)
        sys.exit(1)

    # Create the main output directory if necessary.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Display pipeline information.
    print("\n" + "=" * 70)
    print("ASTRA HUNTERS - COMPLETE VIDEO ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Video folder : {VIDEO_DIR}")
    print(f"Input video  : {video_path}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Total steps  : {len(PIPELINE_STEPS)}")

    # Run every analysis step in order.
    for index, step in enumerate(PIPELINE_STEPS, start=1):

        success = run_step(
            step=step,
            video_path=video_path,
            step_number=index,
            total_steps=len(PIPELINE_STEPS),
        )

        if not success:
            print("\n" + "=" * 70)
            print("PIPELINE STOPPED")
            print("Fix the error above and run the pipeline again.")
            print("=" * 70)
            sys.exit(1)

    # All steps completed successfully.
    print("\n" + "=" * 70)
    print("ALL ANALYSIS STEPS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Input video: {video_path}")
    print(f"Output directory: {OUTPUT_DIR}")

    print("\nFiles and folders currently in the main output directory:")

    for path in sorted(OUTPUT_DIR.iterdir()):
        item_type = "DIR " if path.is_dir() else "FILE"
        print(f"  [{item_type}] {path.name}")

    print("\nPipeline finished.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
