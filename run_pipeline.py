import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_script(script_path, description, args=None):
    """Run a script and report its execution time."""

    script_path = PROJECT_ROOT / script_path

    print("\n" + "=" * 60)
    print(f"STARTING: {description}")
    print(f"Script: {script_path}")
    print("=" * 60, flush=True)

    if not script_path.is_file():
        print(f"ERROR: Required script not found: {script_path}")
        sys.exit(1)

    command = [sys.executable, str(script_path)]

    if args:
        command.extend(args)

    print(f"Command: {' '.join(command)}", flush=True)

    start_time = time.perf_counter()

    try:
        subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True
        )

        elapsed = time.perf_counter() - start_time
        print(
            f"\nSUCCESS: {description} "
            f"completed in {elapsed:.2f} seconds.",
            flush=True
        )
        return elapsed

    except subprocess.CalledProcessError as error:
        elapsed = time.perf_counter() - start_time
        print(f"\nERROR: {description} failed.")
        print(f"Exit code: {error.returncode}")
        print(f"Time before failure: {elapsed:.2f} seconds")
        sys.exit(error.returncode)


def main():
    print("\nASTRA-HUNTERS-2.0 MASTER ANALYSIS PIPELINE")
    print("Beginning automated extraction and analysis...\n")

    pipeline_steps = [
        {
            "script": "src/preprocessing/video_separator.py",
            "desc": "Step 1: Video and Audio Separation",
        },
        {
            "script": "src/audio/audio.py",
            "desc": "Step 2: Audio Feature Extraction",
        },
        {
            "script": "src/audio/detect_accent.py",
            "desc": "Step 3: Accent Classification",
        },
        {
            "script": "src/video/run_all_analysis.py",
            "args": ["data/raw/presentation.mp4"],
            "desc": "Step 4: Video Body Language and Posture Analysis",
        },
    ]

    total_start = time.perf_counter()
    timings = []

    for step in pipeline_steps:
        elapsed = run_script(
            step["script"],
            step["desc"],
            step.get("args"),
        )
        timings.append((step["desc"], elapsed))

    total_elapsed = time.perf_counter() - total_start

    print("\n" + "=" * 60)
    print("PIPELINE TIMING SUMMARY")
    print("=" * 60)

    for description, elapsed in timings:
        print(f"{description}: {elapsed:.2f} seconds")

    print("-" * 60)
    print(f"TOTAL TIME: {total_elapsed:.2f} seconds")
    print("All required pipeline steps completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()