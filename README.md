# Multimodal AI-Based Presentation Performance Analysis and Personalized Feedback System

A Python-based project for analyzing presentation videos using computer vision and facial/head-pose signals. The project extracts visual measurements, analyzes facial signals, estimates head orientation, and combines available results into timestamped reports for further presentation-performance analysis.

## Overview

Effective presentation analysis involves more than speech recognition. Visible presenter behavior—such as facial landmarks, posture, and head movement—can provide additional signals for understanding how a presentation is delivered.

This project implements separate analysis modules and a report-generation pipeline for processing prerecorded presentation videos.

## Features

- **Video analysis:** Processes video frames and extracts available visual features.
- **Facial landmark analysis:** Uses MediaPipe face landmarks and blendshapes.
- **Body and pose analysis:** Uses MediaPipe pose landmarks to extract body-related measurements.
- **Hand landmark analysis:** Supports hand landmark extraction using MediaPipe.
- **Facial-signal analysis:** Generates timestamped facial-signal measurements and visualizations.
- **Head-pose estimation:** Uses 6DRepNet to estimate pitch, yaw, and roll.
- **Blink-candidate analysis:** Provides a preliminary blink-detection output for further validation.
- **Integrated reporting:** Combines available frame-level measurements and timestamped analysis results into CSV reports.
- **Data-quality reporting:** Records matching and data-quality information for the integrated analysis.

> Note: These modules produce measurements and candidate signals. They should not be treated as definitive measurements of confidence, emotion, or presentation quality without appropriate validation.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| OpenCV | Video reading and image processing |
| MediaPipe | Face, pose, and hand landmark analysis |
| 6DRepNet | Head-pose estimation |
| NumPy | Numerical operations |
| Pandas | Timestamp alignment and report generation |
| Matplotlib | Data visualization |

## Project Structure

```text
speaker-analysis-standalone/
├── models/
│   ├── face_landmarker.task
│   ├── hand_landmarker.task
│   └── pose_landmarker_lite.task
├── src/
│   └── analyze_video_json.py
├── tests/
│   ├── analyze_facial_signals.py
│   ├── detect_blinks.py
│   └── test_6drepnet_video.py
├── build_final_report.py
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

The exact contents of `src/` and `tests/` may include additional helper modules. Generated reports, local recordings, and virtual environments are not intended to be committed.

## Prerequisites

- Python installed on your system
- Git
- A prerecorded video file for analysis
- The required Python packages and model files

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/shrikanth-rao/Astra-Hunters-2.0.git
cd Astra-Hunters-2.0/speaker-analysis-standalone
```

Create and activate a virtual environment on Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If a module requires a dependency not listed in `requirements.txt`, add the verified package and version to that file before using the module.

## Running the Analysis

### 1. Extract video-based visual features

From the project root, run:

```bat
python src\analyze_video_json.py "C:\path\to\your\presentation.mp4"
```

Replace the example path with the actual path to your video.

The script generates a timestamped visual-analysis JSON file under `output/`.

### 2. Analyze facial signals

```bat
python tests\analyze_facial_signals.py
```

This module generates facial-signal measurements and a visualization under `output/facial_signal_reports/`.

### 3. Detect candidate blinks

```bat
python tests\detect_blinks.py
```

This generates a preliminary blink-candidate report. Detection thresholds and results should be evaluated against sample videos before drawing conclusions.

### 4. Estimate head pose

Run this module using an environment in which 6DRepNet and its dependencies are installed:

```bat
python tests\test_6drepnet_video.py "C:\path\to\your\presentation.mp4"
```

The script estimates head orientation and saves timestamped samples under `output/head_pose_reports/`.

### 5. Build the integrated report

```bat
python build_final_report.py
```

Follow the file-selection prompts where applicable. The report generator combines compatible timestamped analysis results and creates a session-specific output directory under `output/integrated_reports/`.

Typical report files include:

- `final_analysis_report.csv` — combined frame-level measurements
- `session_summary.csv` — session-level summary
- `data_quality_report.csv` — data-matching and quality information
- `blink_candidates.csv` — blink-candidate events

The exact output depends on which source files are selected and successfully matched.

## How the Pipeline Works

1. Load a prerecorded presentation video.
2. Extract frame-level visual features.
3. Generate facial-signal measurements.
4. Estimate head-pose angles using 6DRepNet.
5. Align compatible measurements by timestamp.
6. Export integrated CSV reports and data-quality information.
7. Inspect the measurements and validate detection results before using them for feedback.

## Current Scope and Limitations

- The current workflow focuses on prerecorded-video analysis.
- The report generator combines only the available and compatible data sources.
- A timestamp match does not guarantee that a measurement is valid; some frames may not contain a detectable face.
- Blink detection is preliminary and requires further validation.
- Audio transcription, speech analysis, slide-content analysis, and personalized coaching are not represented as completed features by this visual-analysis pipeline.
- Results may vary with lighting, camera angle, video quality, occlusion, and model limitations.

## Future Improvements

- Integrate speech transcription and delivery metrics.
- Analyze slide content and alignment with spoken material.
- Add evidence-linked feedback with timestamps.
- Improve detection validation and data-quality checks.
- Develop a unified interface for running and reviewing all analysis modules.
- Evaluate performance across a broader range of presentation videos.

## Research and Project Goal

This implementation is part of a broader project exploring multimodal presentation-performance analysis and personalized feedback. The long-term goal is to combine visual, vocal, and presentation-content evidence to produce useful, interpretable coaching suggestions.

## Responsible Use

Use recordings only when you have the appropriate rights and consent. Avoid interpreting facial movements or head pose as definitive evidence of a person's emotional state, confidence, or abilities.

## License

No license has been specified for this project yet. Check the licenses and redistribution terms for third-party libraries and model files before publishing or redistributing them.
