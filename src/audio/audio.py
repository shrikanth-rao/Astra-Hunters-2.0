import os
import re
import json
from pathlib import Path
from collections import Counter

import imageio_ffmpeg
import whisper
import whisper.audio
import librosa
import numpy as np
import pandas as pd


# ============================================================
# 1. FFMPEG CONFIGURATION
# ============================================================

# Obtain the FFmpeg executable installed by imageio-ffmpeg.
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
FFMPEG_DIR = os.path.dirname(FFMPEG_EXE)

# Make FFmpeg available to other subprocess calls.
os.environ["PATH"] = (
    FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
)

# IMPORTANT:
# Whisper internally uses whisper.audio.FFMPEG when loading
# audio for transcription. Point it directly to the executable.
whisper.audio.FFMPEG = FFMPEG_EXE

if not os.path.isfile(FFMPEG_EXE):
    raise FileNotFoundError(
        f"FFmpeg executable not found: {FFMPEG_EXE}"
    )

print(f"FFmpeg executable: {FFMPEG_EXE}")


# ============================================================
# 2. IMPORTED PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIO_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "presentation.wav"
)

MODEL_NAME = "base"
PAUSE_THRESHOLD = 0.30

OUTPUT_DIR = PROJECT_ROOT / "output" / "audio_out"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3. FILLER WORD CONFIGURATION
# ============================================================

FILLERS = [
    "you know",
    "i mean",
    "i guess",
    "kind of",
    "sort of",
    "um",
    "uh",
    "uhh",
    "umm",
    "erm",
    "er",
    "hmm",
    "hm",
    "ah",
    "actually",
    "basically",
    "literally",
]

FILLER_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(
        re.escape(filler)
        for filler in sorted(FILLERS, key=len, reverse=True)
    )
    + r")\b",
    re.IGNORECASE,
)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def rounded(value, digits=3):
    """Round a numeric value while preserving missing values."""
    if value is None:
        return None

    try:
        if not np.isfinite(value):
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def count_fillers(text):
    """Count recognized filler phrases."""
    return Counter(
        match.group(0).lower()
        for match in FILLER_PATTERN.finditer(text)
    )


def get_pitch(audio_clip, sample_rate):
    """
    Estimate pitch using the YIN algorithm.

    Returns fundamental frequency statistics in Hz.
    """
    empty = {
        "pitch_mean_hz": None,
        "pitch_median_hz": None,
        "pitch_min_hz": None,
        "pitch_max_hz": None,
        "pitch_std_hz": None,
        "voiced_pitch_frame_count": 0,
    }

    if len(audio_clip) < int(0.10 * sample_rate):
        return empty

    clip = audio_clip - np.mean(audio_clip)

    if np.sqrt(np.mean(clip ** 2)) < 1e-4:
        return empty

    try:
        f0 = librosa.yin(
            clip,
            fmin=65,
            fmax=500,
            sr=sample_rate,
            frame_length=2048,
            hop_length=256,
        )

        valid = f0[
            np.isfinite(f0)
            & (f0 >= 65)
            & (f0 <= 500)
        ]

        if len(valid) == 0:
            return empty

        return {
            "pitch_mean_hz": rounded(np.mean(valid), 2),
            "pitch_median_hz": rounded(np.median(valid), 2),
            "pitch_min_hz": rounded(np.min(valid), 2),
            "pitch_max_hz": rounded(np.max(valid), 2),
            "pitch_std_hz": rounded(np.std(valid), 2),
            "voiced_pitch_frame_count": int(len(valid)),
        }

    except Exception as error:
        print(f"Warning: pitch estimation failed: {error}")
        return empty


# ============================================================
# 5. VALIDATE AND LOAD AUDIO
# ============================================================

audio_path = Path(AUDIO_FILE)

if not audio_path.exists():
    raise FileNotFoundError(
        f"Audio file not found: {audio_path.resolve()}\n"
        "Ensure presentation.wav exists in data/processed/."
    )

print("\n" + "=" * 60)
print("SPEECH ANALYSIS PIPELINE")
print("=" * 60)

print(f"Audio file: {audio_path}")
print("Loading audio for pitch and timing analysis...")

audio, sample_rate = librosa.load(
    str(audio_path),
    sr=16000,
    mono=True,
)

duration = len(audio) / sample_rate

if duration <= 0:
    raise ValueError("The input audio is empty.")

print(f"Audio duration: {duration:.2f} seconds")
print(f"Sample rate: {sample_rate} Hz")

print(f"\nLoading Whisper model: {MODEL_NAME}")
model = whisper.load_model(MODEL_NAME)


# ============================================================
# 6. TRANSCRIBE AUDIO
# ============================================================

print("\nTranscribing audio with Whisper...")

# whisper.audio.FFMPEG was configured above.
# Passing the WAV file here preserves the extracted audio source.
result = model.transcribe(
    audio,
    language="en",
    fp16=False,
    temperature=0,
    word_timestamps=True,
    initial_prompt=(
        "Transcribe the speech as accurately as possible. "
        "Preserve filler words, hesitations, repetitions, "
        "false starts, and disfluencies. Do not intentionally "
        "remove words such as um, uh, hmm, you know, like, "
        "actually, basically, and I mean."
    ),
)

transcript = result.get("text", "").strip()

transcript_path = OUTPUT_DIR / "transcription.txt"
transcript_path.write_text(transcript, encoding="utf-8")

print("Transcription saved.")
print(f"Transcript: {transcript_path}")


# ============================================================
# 7. EXTRACT WORD TIMESTAMPS
# ============================================================

words = []

for segment in result.get("segments", []):
    segment_start = float(segment.get("start", 0.0))
    segment_end = float(segment.get("end", segment_start))

    for item in segment.get("words", []):
        word_text = item.get("word", "").strip()

        if not word_text:
            continue

        start = max(
            0.0,
            min(float(item.get("start", segment_start)), duration),
        )

        end = max(
            start,
            min(float(item.get("end", segment_end)), duration),
        )

        words.append({
            "word": word_text,
            "start": start,
            "end": end,
        })

words.sort(key=lambda item: (item["start"], item["end"]))


# ============================================================
# 8. DETECT PAUSES BETWEEN WORDS
# ============================================================

pauses = []

for previous, current in zip(words, words[1:]):
    gap = current["start"] - previous["end"]

    if gap >= PAUSE_THRESHOLD:
        pauses.append({
            "pause_start_seconds": rounded(previous["end"]),
            "pause_end_seconds": rounded(current["start"]),
            "pause_duration_seconds": rounded(gap),
            "word_before_pause": previous["word"],
            "word_after_pause": current["word"],
        })

total_pause_duration = sum(
    pause["pause_duration_seconds"]
    for pause in pauses
)

speech_active_duration = max(
    0.0,
    duration - total_pause_duration,
)


# ============================================================
# 9. OVERALL RECORDING FEATURES
# ============================================================

total_words = len(words)
overall_fillers = count_fillers(transcript)
total_fillers = sum(overall_fillers.values())

overall_wpm = (
    total_words / duration * 60
    if duration > 0 else 0.0
)

active_wpm = (
    total_words / speech_active_duration * 60
    if speech_active_duration > 0 else 0.0
)

filler_frequency = (
    total_fillers / total_words * 100
    if total_words > 0 else 0.0
)

most_used_filler = (
    overall_fillers.most_common(1)[0][0]
    if overall_fillers else "None"
)

all_pauses_json = json.dumps(
    pauses,
    ensure_ascii=False,
)

filler_counts_json = json.dumps(
    dict(overall_fillers),
    ensure_ascii=False,
)


# ============================================================
# 10. SPLIT ALIGNED WORDS INTO SENTENCES
# ============================================================

sentences = []
current_words = []

for word in words:
    current_words.append(word)

    if re.search(r"""[.!?]["')\]]*$""", word["word"]):
        sentences.append(current_words)
        current_words = []

if current_words:
    sentences.append(current_words)

# Fallback if no word-level alignment was returned.
if not sentences and result.get("segments"):
    for segment in result["segments"]:
        segment_text = segment.get("text", "").strip()

        if segment_text:
            sentences.append([{
                "word": segment_text,
                "start": float(segment["start"]),
                "end": float(segment["end"]),
            }])


# ============================================================
# 11. BUILD SENTENCE-LEVEL DATASET
# ============================================================

rows = []

for sentence_number, sentence_words in enumerate(sentences, start=1):

    sentence_text = " ".join(
        item["word"] for item in sentence_words
    ).strip()

    sentence_start = sentence_words[0]["start"]
    sentence_end = sentence_words[-1]["end"]

    sentence_duration = max(
        0.0,
        sentence_end - sentence_start,
    )

    sentence_word_count = sum(
        len(re.findall(r"\b[\w'-]+\b", item["word"]))
        for item in sentence_words
    )

    sentence_wpm = (
        sentence_word_count / sentence_duration * 60
        if sentence_duration > 0 else 0.0
    )

    # Sentence-level filler statistics.
    sentence_fillers = count_fillers(sentence_text)
    sentence_filler_total = sum(sentence_fillers.values())

    # Pauses occurring within this sentence.
    sentence_pauses = []

    for previous, current in zip(
        sentence_words,
        sentence_words[1:],
    ):
        gap = current["start"] - previous["end"]

        if gap >= PAUSE_THRESHOLD:
            sentence_pauses.append({
                "start_seconds": rounded(previous["end"]),
                "end_seconds": rounded(current["start"]),
                "duration_seconds": rounded(gap),
                "word_before": previous["word"],
                "word_after": current["word"],
            })

    sentence_pause_durations = [
        pause["duration_seconds"]
        for pause in sentence_pauses
    ]

    sentence_pause_total = sum(sentence_pause_durations)

    # Estimate pitch for the sentence audio segment.
    start_sample = max(
        0,
        int(sentence_start * sample_rate),
    )

    end_sample = min(
        len(audio),
        int(sentence_end * sample_rate),
    )

    pitch = get_pitch(
        audio[start_sample:end_sample],
        sample_rate,
    )

    # Locate pauses immediately before and after this sentence.
    preceding_pauses = [
        pause for pause in pauses
        if abs(
            pause["pause_end_seconds"] - sentence_start
        ) <= 0.10
    ]

    following_pauses = [
        pause for pause in pauses
        if abs(
            pause["pause_start_seconds"] - sentence_end
        ) <= 0.10
    ]

    pause_before = (
        preceding_pauses[-1]["pause_duration_seconds"]
        if preceding_pauses else 0.0
    )

    pause_after = (
        following_pauses[0]["pause_duration_seconds"]
        if following_pauses else 0.0
    )

    row = {
        # Recording identification
        "audio_file": audio_path.name,
        "sentence_number": sentence_number,

        # Overall recording features
        "audio_duration_seconds": rounded(duration),
        "audio_duration_minutes": rounded(duration / 60),
        "recording_total_words": total_words,
        "recording_overall_wpm": rounded(overall_wpm, 2),
        "recording_active_wpm": rounded(active_wpm, 2),
        "recording_total_fillers": total_fillers,
        "recording_filler_frequency_percent": rounded(
            filler_frequency, 2
        ),
        "recording_most_used_filler": most_used_filler,
        "recording_filler_counts_json": filler_counts_json,
        "recording_total_pauses": len(pauses),
        "recording_total_pause_seconds": rounded(
            total_pause_duration
        ),
        "recording_active_seconds_estimate": rounded(
            speech_active_duration
        ),
        "pause_threshold_seconds": PAUSE_THRESHOLD,

        # Sentence text and timing
        "sentence_text": sentence_text,
        "sentence_start_seconds": rounded(sentence_start),
        "sentence_end_seconds": rounded(sentence_end),
        "sentence_duration_seconds": rounded(sentence_duration),
        "sentence_word_count": sentence_word_count,
        "sentence_wpm": rounded(sentence_wpm, 2),

        # Sentence-level fillers
        "sentence_total_fillers": sentence_filler_total,
        "sentence_filler_counts_json": json.dumps(
            dict(sentence_fillers),
            ensure_ascii=False,
        ),

        # Sentence-level pauses
        "sentence_pause_count": len(sentence_pauses),
        "sentence_total_pause_seconds": rounded(
            sentence_pause_total
        ),
        "sentence_mean_pause_seconds": rounded(
            np.mean(sentence_pause_durations)
            if sentence_pause_durations else 0.0
        ),
        "sentence_longest_pause_seconds": rounded(
            max(sentence_pause_durations)
            if sentence_pause_durations else 0.0
        ),
        "pause_before_sentence_seconds": rounded(pause_before),
        "pause_after_sentence_seconds": rounded(pause_after),
        "sentence_pause_events_json": json.dumps(
            sentence_pauses,
            ensure_ascii=False,
        ),

        # Recording-level pause events
        "recording_pause_events_json": all_pauses_json,

        # Sentence-level pitch features
        **pitch,
    }

    rows.append(row)


# ============================================================
# 12. SAVE THE CONSOLIDATED ML DATASET
# ============================================================

csv_path = OUTPUT_DIR / "speech_ml_dataset.csv"

columns = [
    "audio_file",
    "sentence_number",
    "audio_duration_seconds",
    "audio_duration_minutes",
    "recording_total_words",
    "recording_overall_wpm",
    "recording_active_wpm",
    "recording_total_fillers",
    "recording_filler_frequency_percent",
    "recording_most_used_filler",
    "recording_filler_counts_json",
    "recording_total_pauses",
    "recording_total_pause_seconds",
    "recording_active_seconds_estimate",
    "pause_threshold_seconds",
    "sentence_text",
    "sentence_start_seconds",
    "sentence_end_seconds",
    "sentence_duration_seconds",
    "sentence_word_count",
    "sentence_wpm",
    "sentence_total_fillers",
    "sentence_filler_counts_json",
    "sentence_pause_count",
    "sentence_total_pause_seconds",
    "sentence_mean_pause_seconds",
    "sentence_longest_pause_seconds",
    "pause_before_sentence_seconds",
    "pause_after_sentence_seconds",
    "sentence_pause_events_json",
    "recording_pause_events_json",
    "pitch_mean_hz",
    "pitch_median_hz",
    "pitch_min_hz",
    "pitch_max_hz",
    "pitch_std_hz",
    "voiced_pitch_frame_count",
]

df = pd.DataFrame(rows, columns=columns)

df.to_csv(
    csv_path,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 13. PRINT SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("SPEECH ANALYSIS COMPLETED")
print("=" * 60)

print(f"Duration:             {duration:.2f} seconds")
print(f"Words:                {total_words}")
print(f"Overall WPM:          {overall_wpm:.2f}")
print(f"Estimated active WPM: {active_wpm:.2f}")
print(f"Total fillers:        {total_fillers}")
print(f"Most-used filler:     {most_used_filler}")
print(f"Total pauses:         {len(pauses)}")
print(f"Sentence count:       {len(rows)}")
print(f"CSV columns:          {len(columns)}")

print("\nFiller breakdown:")
for filler, count in overall_fillers.most_common():
    print(f"  {filler}: {count}")

print("\nSaved files:")
print(f"  ML dataset:    {csv_path.resolve()}")
print(f"  Transcription: {transcript_path.resolve()}")

print(f"\nCSV rows: {len(df)}")
print(f"CSV columns: {len(df.columns)}")
print("=" * 60)