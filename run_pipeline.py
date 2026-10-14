import subprocess
import sys
from pathlib import Path

def run_script(script_path, description, args=None):
    """Runs a Python script with optional arguments and stops if an error occurs."""
    print(f"\n{'='*60}")
    print(f"🚀 STARTING: {description}")
    
    # Build the terminal command
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
        
    print(f"▶ Executing: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ SUCCESS: {description} completed.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {description} failed with exit code {e.returncode}.")
        print("Stopping the pipeline to prevent cascading errors.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERROR: Could not find script at '{script_path}'.")
        print("Check the file path and try again.")
        sys.exit(1)

def main():
    print("\n🌟 ASTRA-HUNTERS-2.0 MASTER ANALYSIS PIPELINE 🌟")
    print("Beginning automated extraction and analysis...")
    
    # Define the exact sequence of scripts and their arguments
    pipeline_steps = [
        {
            "script": "src/preprocessing/video_separator.py", 
            "desc": "Step 1: Video & Audio Separation"
        },
        {
            "script": "src/audio/audio.py", 
            "desc": "Step 2: Audio Feature Extraction (Pitch, Pauses, WPM)"
        },
        {
            "script": "src/audio/detect_accent.py",
            "desc": "Step 3: Accent Classification"
        },
        {
            "script": "src/video/run_all_analysis.py",
            "args": ["data/raw/presentation.mp4"], # <-- Added the file path argument here!
            "desc": "Step 4: Video Body Language & Posture Analysis"
        }
    ]
    
    # Run each step sequentially
    for step in pipeline_steps:
        script_path = Path(step["script"])
        if not script_path.exists():
            print(f"\n⚠️ WARNING: Script '{script_path}' not found. Skipping...")
            continue
            
        run_script(str(script_path), step["desc"], step.get("args"))
        
    print("\n" + "="*60)
    print("🎉 ALL PIPELINE STEPS COMPLETED SUCCESSFULLY! 🎉")
    print("Check your 'output/' folder for all the generated reports.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()