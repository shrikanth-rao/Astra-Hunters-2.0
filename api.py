import os
import sys
import shutil
import json
import re
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
PPT_OUTPUT_DIR = PROJECT_ROOT / "output" / "ppt_analysed"

# Ensure directories exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PPT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Add project root to sys.path so src modules can be imported smoothly
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load PPT Analyzer directly from src/ppt_analysis/ppt_analyser.py
try:
    from src.ppt_analysis.ppt_analyser import analyze_presentation, analyze_pptx
    PPT_ANALYZER_AVAILABLE = True
    print("[Astra-API] Successfully loaded PPT Analyzer from src/ppt_analysis/ppt_analyser.py")
except Exception as e:
    print(f"[Astra-API] Warning: Could not load PPT analyzer from src/ppt_analysis/ppt_analyser.py: {e}")
# Load PDF Report Generator from src/report_pdf.py
try:
    from src.report_pdf import create_speech_report_pdf
    PDF_GENERATOR_AVAILABLE = True
    print("[Astra-API] Successfully loaded PDF Generator from src/report_pdf.py")
except Exception as e:
    print(f"[Astra-API] Warning: Could not load PDF generator from src/report_pdf.py: {e}")
    PDF_GENERATOR_AVAILABLE = False

app = FastAPI(
    title="Astra-Hunters-2.0 API",
    version="2.0.0",
    description="Multimodal AI Public Speaking & Presentation Evaluation Platform Backend",
)

# CORS configuration to allow requests from Vite dev server and frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Astra-Hunters-2.0 Evaluation Platform",
        "ppt_analyzer_loaded": PPT_ANALYZER_AVAILABLE,
        "endpoints": [
            "/analyze-video",
            "/api/analyze-ppt",
            "/api/ppt-report",
            "/api/presentation-accent",
        ],
    }


def parse_accent_file(accent_text: str):
    """Extract detected accent and confidence percentage from presentation_accent.txt."""
    accent = "Unknown"
    confidence = ""
    for line in accent_text.splitlines():
        if "detected accent:" in line.lower():
            parts = line.split(":", 1)
            if len(parts) > 1:
                accent = parts[1].strip().capitalize()
        elif "confidence" in line.lower():
            parts = line.split(":", 1)
            if len(parts) > 1:
                confidence = parts[1].strip()
    return accent, confidence


@app.get("/api/accent")
@app.get("/api/presentation-accent")
def get_presentation_accent():
    """Returns the latest analyzed accent from output/audio_out/presentation_accent.txt."""
    accent_candidates = [
        OUTPUT_DIR / "audio_out" / "presentation_accent.txt",
        OUTPUT_DIR / "presentation_accent.txt",
    ]
    for cand in accent_candidates:
        if cand.exists():
            try:
                raw = cand.read_text(encoding="utf-8", errors="replace").strip()
                accent, conf = parse_accent_file(raw)
                return {
                    "status": "success",
                    "detected_accent": accent,
                    "confidence": conf,
                    "raw_text": raw,
                    "file_path": str(cand),
                }
            except Exception as e:
                pass

    return {
        "status": "not_found",
        "detected_accent": "Standard English",
        "confidence": "",
        "raw_text": "",
        "message": "Accent analysis file not found in output/audio_out/.",
    }


@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Accepts an .mp4 file via multipart/form-data.
    1. Saves video to data/raw/presentation.mp4
    2. Executes run_pipeline.py via subprocess
    3. Reads final_predicted_scores.json, coaching_report.txt,
       transcription.txt, presentation_accent.txt
    4. Returns a consolidated JSON payload.
    """
    # 1. Validate file format
    filename = file.filename or "presentation.mp4"
    file_ext = Path(filename).suffix.lower()
    if file_ext not in [".mp4", ".webm", ".mov", ".m4v"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: '{file_ext}'. Please upload an .mp4, .webm, or .mov file.",
        )

    # 2. Prepare target upload directory
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    target_video_path = DATA_RAW / "presentation.mp4"

    # Clean existing .mp4 files in data/raw to ensure presentation.mp4 is unambiguous
    for existing_video in DATA_RAW.glob("*.mp4"):
        try:
            existing_video.unlink(missing_ok=True)
        except Exception:
            pass

    # Save uploaded video
    try:
        with open(target_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded video file: {str(e)}"
        )
    finally:
        await file.close()

    print(f"\n[Astra-API] Saved presentation video to: {target_video_path.resolve()}")
    print("[Astra-API] Executing ML Pipeline via run_pipeline.py...")

    # 3. Execute python run_pipeline.py via subprocess with UTF-8 IO encoding
    run_pipeline_script = PROJECT_ROOT / "run_pipeline.py"
    if not run_pipeline_script.exists():
        raise HTTPException(
            status_code=500, detail="Pipeline runner 'run_pipeline.py' not found."
        )

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        pipeline_process = subprocess.run(
            [sys.executable, str(run_pipeline_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline subprocess: {str(e)}",
        )

    if pipeline_process.returncode != 0:
        error_msg = pipeline_process.stderr.strip() or pipeline_process.stdout.strip()
        print(f"[Astra-API] Pipeline failed with returncode {pipeline_process.returncode}:\n{error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"ML Pipeline execution failed (code {pipeline_process.returncode}). Error: {error_msg[-800:]}",
        )

    print("[Astra-API] Pipeline execution successful! Collecting output files...")

    # 4. Read output files

    # 4a. final_predicted_scores.json
    scores_path = OUTPUT_DIR / "final_predicted_scores.json"
    predicted_scores = {}
    delivery_score = 0.0
    vocal_score = 0.0
    body_language_score = 0.0
    overall_score = 0.0

    if scores_path.exists():
        try:
            with open(scores_path, "r", encoding="utf-8") as f:
                scores_data = json.load(f)
                predicted_scores = scores_data.get("predicted_scores", {})
                delivery_score = float(predicted_scores.get("Delivery Score", 0.0))
                vocal_score = float(predicted_scores.get("Vocal Expression", 0.0))
                body_language_score = float(predicted_scores.get("Body Language", 0.0))
                overall_score = round(
                    (delivery_score + vocal_score + body_language_score) / 3.0, 1
                )
        except Exception as e:
            print(f"[Astra-API] Warning: Failed to parse final_predicted_scores.json: {e}")
    else:
        print("[Astra-API] Warning: final_predicted_scores.json not found in output/")

    # 4b. coaching_report.txt (UTF-8 encoded Groq LLM feedback)
    coaching_report_path = OUTPUT_DIR / "coaching_report.txt"
    coaching_report = ""
    if coaching_report_path.exists():
        try:
            coaching_report = coaching_report_path.read_text(
                encoding="utf-8", errors="replace"
            ).strip()
        except Exception as e:
            print(f"[Astra-API] Warning: Failed to read coaching_report.txt: {e}")
    if not coaching_report:
        coaching_report = "Coaching report could not be generated for this session."

    # 4c. transcription.txt (handle gracefully if missing)
    transcription_candidates = [
        OUTPUT_DIR / "transcription.txt",
        OUTPUT_DIR / "audio_out" / "transcription.txt",
    ]
    transcription = ""
    for cand in transcription_candidates:
        if cand.exists():
            try:
                transcription = cand.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                if transcription:
                    break
            except Exception as e:
                print(f"[Astra-API] Warning: Error reading {cand}: {e}")
    if not transcription:
        transcription = "No speech transcription was detected in this recording."

    # 4d. presentation_accent.txt (handle gracefully if missing)
    accent_candidates = [
        OUTPUT_DIR / "audio_out" / "presentation_accent.txt",
        OUTPUT_DIR / "presentation_accent.txt",
    ]
    presentation_accent_raw = ""
    detected_accent = "Standard English"
    accent_confidence = ""
    for cand in accent_candidates:
        if cand.exists():
            try:
                presentation_accent_raw = cand.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                if presentation_accent_raw:
                    detected_accent, accent_confidence = parse_accent_file(
                        presentation_accent_raw
                    )
                    break
            except Exception as e:
                print(f"[Astra-API] Warning: Error reading {cand}: {e}")

    # 4e. Extract extra speech metrics (Pace/WPM, Pauses, Fillers, Pitch) if available
    metrics = {
        "duration": 0,
        "pace": 0,
        "fillerCount": 0,
        "pauseCount": 0,
        "averagePitch": 0,
        "pitchVariation": "Moderate",
    }
    audio_metrics_file = (
        OUTPUT_DIR / "audio_ml_dataset" / "flattened_audio_dataset.csv"
    )
    if audio_metrics_file.exists():
        try:
            import pandas as pd

            df_audio = pd.read_csv(audio_metrics_file)
            if not df_audio.empty:
                last_row = df_audio.iloc[-1]
                wpm = round(float(last_row.get("recording_overall_wpm", 0)))
                fillers = int(last_row.get("recording_total_fillers", 0))
                pauses = int(last_row.get("recording_total_pauses", 0))
                mean_pitch = round(float(last_row.get("pitch_mean_hz", 0)))
                pitch_std = float(last_row.get("pitch_std_hz", 0))
                pitch_var_text = (
                    "High" if pitch_std > 80 else "Moderate" if pitch_std > 40 else "Low"
                )

                metrics["pace"] = wpm
                metrics["fillerCount"] = fillers
                metrics["pauseCount"] = pauses
                metrics["averagePitch"] = mean_pitch
                metrics["pitchVariation"] = pitch_var_text
        except Exception as e:
            print(f"[Astra-API] Non-critical: Could not parse audio metrics CSV: {e}")

    # Get video duration from video_metadata.json if available
    video_meta_path = DATA_PROCESSED / "video_metadata.json"
    if video_meta_path.exists():
        try:
            with open(video_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                metrics["duration"] = round(float(meta.get("duration_seconds", 0)))
        except Exception:
            pass

    # 5. Build consolidated response payload
    response_payload = {
        "status": "success",
        "video_name": filename,
        "scores": {
            "overall": overall_score if overall_score > 0 else delivery_score,
            "delivery": delivery_score,
            "vocal": vocal_score,
            "body_language": body_language_score,
        },
        "predicted_scores": predicted_scores,
        "coaching_report": coaching_report,
        "transcription": transcription,
        "detected_accent": detected_accent,
        "accent_confidence": accent_confidence,
        "presentation_accent": presentation_accent_raw,
        "metrics": metrics,
    }

    return JSONResponse(status_code=200, content=response_payload)


# PowerPoint Analysis endpoints connected to src/ppt_analysis/ppt_analyser.py
@app.post("/api/analyze-ppt")
@app.post("/analyze-ppt")
async def analyze_ppt(file: UploadFile = File(...)):
    """
    Analyze a PowerPoint (.pptx) file using the engine in src/ppt_analysis/ppt_analyser.py.
    Saves the presentation and generates output/ppt_analysed/pptanalysis.json & pptanalysis.txt in the backend.
    """
    if not PPT_ANALYZER_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PPT Analyzer module (src/ppt_analysis/ppt_analyser.py) is not loaded.",
        )

    filename = file.filename or "presentation.pptx"
    if not filename.lower().endswith(".pptx"):
        raise HTTPException(
            status_code=400, detail="Only PowerPoint .pptx files are supported."
        )

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    PPT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target_ppt_path = DATA_RAW / filename

    try:
        with open(target_ppt_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save PowerPoint file: {str(e)}"
        )
    finally:
        await file.close()

    print(f"\n[Astra-API] Saved PowerPoint file to: {target_ppt_path.resolve()}")
    print("[Astra-API] Executing PPT analysis via src/ppt_analysis/ppt_analyser.py...")

    try:
        # Runs analysis and produces backend reports in output/ppt_analysed/
        report = analyze_presentation(target_ppt_path, PPT_OUTPUT_DIR)
        report["file_name"] = filename
        print(
            f"[Astra-API] PPT analysis finished for '{filename}'! Score: {report.get('average_basic_structure_score')}/100"
        )
        return {"success": True, "report": report}
    except Exception as exc:
        print(f"[Astra-API] Error analyzing PowerPoint: {exc}")
        raise HTTPException(
            status_code=400, detail=f"Could not analyze PowerPoint file: {str(exc)}"
        )


@app.get("/api/ppt-report")
@app.get("/api/ppt-analysis")
def get_ppt_report():
    """Returns the latest PowerPoint analysis report saved in the backend."""
    json_path = PPT_OUTPUT_DIR / "pptanalysis.json"
    txt_path = PPT_OUTPUT_DIR / "pptanalysis.txt"

    if not json_path.exists():
        raise HTTPException(
            status_code=404, detail="No PowerPoint analysis report found in output/ppt_analysed/."
        )

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        text_content = ""
        if txt_path.exists():
            text_content = txt_path.read_text(encoding="utf-8", errors="replace")
        return {"success": True, "report": report_data, "text_report": text_content}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load PPT report: {str(exc)}"
        )


@app.post("/api/report/pdf")
async def generate_speech_report_pdf(request: Request):
    """
    Generates and streams a downloadable PDF speech performance report.
    Compatible with the Progress / Analyzing page.
    """
    try:
        speech_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload provided.")

    if not PDF_GENERATOR_AVAILABLE:
        raise HTTPException(
            status_code=500, detail="PDF generator module is not available on the backend."
        )

    try:
        pdf_bytes = create_speech_report_pdf(speech_data)
        safe_title = (
            re.sub(r"[^a-zA-Z0-9_\- ]+", "", speech_data.get("title", "speech_report")).strip()
            or "speech_report"
        )
        safe_filename = f"{safe_title.replace(' ', '_')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as exc:
        print(f"[Astra-API] Error generating report PDF: {exc}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PDF report: {str(exc)}"
        )



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
