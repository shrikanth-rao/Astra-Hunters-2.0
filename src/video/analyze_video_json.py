
import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
from PIL import Image
from transformers import pipeline


# --------------------------------------------------
# 1. PATHS AND CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "output"

FACE_MODEL = MODEL_DIR / "face_landmarker.task"
POSE_MODEL = MODEL_DIR / "pose_landmarker_lite.task"
HAND_MODEL = MODEL_DIR / "hand_landmarker.task"

EXPRESSION_MODEL = "trpakov/vit-face-expression"

# Run the expression classifier approximately twice per second.
DEFAULT_EXPRESSION_INTERVAL = 0.5

# Below this classifier score, use "uncertain".
MIN_EXPRESSION_SCORE = 0.45


# --------------------------------------------------
# 2. SERIALIZATION HELPERS
# --------------------------------------------------

def rounded(value, digits=5):
    if value is None:
        return None

    value = float(value)

    if not math.isfinite(value):
        return None

    return round(value, digits)


def landmark_to_dict(landmark):
    """Convert a MediaPipe landmark to JSON-compatible values."""
    result = {
        "x": rounded(landmark.x),
        "y": rounded(landmark.y),
        "z": rounded(landmark.z),
    }

    if hasattr(landmark, "visibility"):
        result["visibility"] = rounded(landmark.visibility)

    if hasattr(landmark, "presence"):
        result["presence"] = rounded(landmark.presence)

    return result


def landmarks_to_list(landmarks):
    return [landmark_to_dict(point) for point in landmarks]


def blendshapes_to_dict(categories):
    return {
        item.category_name: rounded(item.score, 6)
        for item in categories
    }


# --------------------------------------------------
# 3. FACIAL EXPRESSION CLASSIFIER
# --------------------------------------------------

def get_face_crop(frame, landmarks):
    """
    Crop the detected face using its normalized landmarks.
    Returns a PIL RGB image, or None if the crop is invalid.
    """
    height, width = frame.shape[:2]

    x_values = [point.x for point in landmarks]
    y_values = [point.y for point in landmarks]

    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)

    padding_x = (x_max - x_min) * 0.15
    padding_y = (y_max - y_min) * 0.15

    x1 = max(0, int((x_min - padding_x) * width))
    y1 = max(0, int((y_min - padding_y) * height))
    x2 = min(width, int((x_max + padding_x) * width))
    y2 = min(height, int((y_max + padding_y) * height))

    if x2 <= x1 or y2 <= y1:
        return None

    face_bgr = frame[y1:y2, x1:x2]

    if face_bgr.size == 0:
        return None

    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(face_rgb)


def classify_expression(classifier, frame, landmarks):
    """
    Estimate a visible facial-expression category.

    This is a model prediction, not a determination of the
    speaker's actual emotional state.
    """
    crop = get_face_crop(frame, landmarks)

    if crop is None:
        return {
            "label": "uncertain",
            "confidence": None,
            "scores": {},
            "method": "vit_face_expression",
            "reason": "Invalid face crop",
        }

    try:
        predictions = classifier(crop, top_k=None)

        if not predictions:
            raise ValueError("Classifier returned no predictions")

        scores = {
            str(item["label"]).lower(): float(item["score"])
            for item in predictions
        }

        best_label = max(scores, key=scores.get)
        best_score = scores[best_label]

        if best_score < MIN_EXPRESSION_SCORE:
            label = "uncertain"
            reason = "Prediction score below configured threshold"
        else:
            label = best_label
            reason = None

        return {
            "label": label,
            "confidence": rounded(best_score, 6),
            "scores": {
                key: rounded(value, 6)
                for key, value in scores.items()
            },
            "method": "vit_face_expression",
            "reason": reason,
        }

    except Exception as error:
        return {
            "label": "uncertain",
            "confidence": None,
            "scores": {},
            "method": "vit_face_expression",
            "reason": f"Classification failed: {str(error)}",
        }


# --------------------------------------------------
# 4. EYES, MOUTH AND HEAD SIGNALS
# --------------------------------------------------

def get_facial_signals(blendshapes):
    """
    Return model-provided facial movement scores.
    These are not direct measurements of internal emotions.
    """
    if not blendshapes:
        return {
            "eyes": None,
            "mouth": None,
            "expression_features": None,
        }

    def select(prefixes):
        return {
            key: value
            for key, value in blendshapes.items()
            if any(key.startswith(prefix) for prefix in prefixes)
        }

    eye_features = select([
        "eyeBlink",
        "eyeLook",
        "eyeWide",
        "eyeSquint",
    ])

    mouth_features = select([
        "jawOpen",
        "mouth",
        "cheekSquint",
    ])

    expression_features = select([
        "browDown",
        "browInnerUp",
        "browOuterUp",
        "noseSneer",
    ])

    return {
        "eyes": {
            "blendshape_scores": eye_features,
            "gaze_direction_estimate": "not_calculated",
        },
        "mouth": {
            "blendshape_scores": mouth_features,
        },
        "expression_features": expression_features,
        "head_orientation": {
            "yaw_degrees": None,
            "pitch_degrees": None,
            "roll_degrees": None,
            "status": "not_calculated",
        },
    }


# --------------------------------------------------
# 5. BODY MEASUREMENTS
# --------------------------------------------------

def calculate_pose_metrics(landmarks):
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_hip = landmarks[23]
    right_hip = landmarks[24]

    shoulders_visible = (
        left_shoulder.visibility >= 0.5
        and right_shoulder.visibility >= 0.5
    )

    hips_visible = (
        left_hip.visibility >= 0.5
        and right_hip.visibility >= 0.5
    )

    shoulder_tilt = None
    torso_offset = None

    if shoulders_visible:
        shoulder_tilt = abs(
            left_shoulder.y - right_shoulder.y
        )

    if shoulders_visible and hips_visible:
        shoulder_mid_x = (
            left_shoulder.x + right_shoulder.x
        ) / 2

        hip_mid_x = (
            left_hip.x + right_hip.x
        ) / 2

        torso_offset = shoulder_mid_x - hip_mid_x

    return {
        "shoulder_tilt_normalized": rounded(shoulder_tilt),
        "torso_offset_normalized": rounded(torso_offset),
    }


# --------------------------------------------------
# 6. FINGER EXTENSION ESTIMATES
# --------------------------------------------------

def angle_at_joint(point_a, joint, point_b):
    """Calculate a 3D joint angle in degrees."""
    a = [
        point_a.x - joint.x,
        point_a.y - joint.y,
        point_a.z - joint.z,
    ]
    b = [
        point_b.x - joint.x,
        point_b.y - joint.y,
        point_b.z - joint.z,
    ]

    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))

    if mag_a == 0 or mag_b == 0:
        return None

    cosine = max(-1.0, min(1.0, dot / (mag_a * mag_b)))
    return math.degrees(math.acos(cosine))


def get_finger_states(landmarks):
    """
    Estimate whether fingers appear extended or curled.
    These angle thresholds are heuristic and need validation.
    """
    definitions = {
        "thumb": (1, 2, 4),
        "index": (5, 6, 8),
        "middle": (9, 10, 12),
        "ring": (13, 14, 16),
        "pinky": (17, 18, 20),
    }

    result = {}

    for finger, (base, joint_index, tip) in definitions.items():
        angle = angle_at_joint(
            landmarks[base],
            landmarks[joint_index],
            landmarks[tip],
        )

        if angle is None:
            state = "unknown"
        elif angle >= 150:
            state = "extended_estimate"
        elif angle <= 120:
            state = "curled_estimate"
        else:
            state = "intermediate"

        result[finger] = {
            "joint_angle_degrees": rounded(angle, 2),
            "state_estimate": state,
        }

    return result


# --------------------------------------------------
# 7. TIMESTAMPED EXPRESSION INTERVALS
# --------------------------------------------------

def build_expression_timeline(samples, duration):
    """
    Merge adjacent sampled predictions with the same label.
    Intervals represent model estimates, not continuous certainty.
    """
    if not samples:
        return []

    timeline = []

    for index, sample in enumerate(samples):
        start = sample["timestamp_seconds"]

        if index + 1 < len(samples):
            end = samples[index + 1]["timestamp_seconds"]
        else:
            end = duration

        end = max(start, min(end, duration))
        label = sample["label"]

        if (
            timeline
            and timeline[-1]["label"] == label
            and abs(
                timeline[-1]["end_seconds"] - start
            ) < 0.001
        ):
            timeline[-1]["end_seconds"] = rounded(end, 3)
            timeline[-1]["sample_count"] += 1

            confidence = sample.get("confidence")
            if confidence is not None:
                timeline[-1]["confidence_values"].append(
                    confidence
                )
        else:
            timeline.append({
                "start_seconds": rounded(start, 3),
                "end_seconds": rounded(end, 3),
                "label": label,
                "method": sample.get("method"),
                "sample_count": 1,
                "confidence_values": (
                    [sample["confidence"]]
                    if sample.get("confidence") is not None
                    else []
                ),
            })

    for interval in timeline:
        values = interval.pop("confidence_values")
        interval["mean_confidence"] = (
            rounded(sum(values) / len(values), 6)
            if values else None
        )
        interval["duration_seconds"] = rounded(
            interval["end_seconds"] - interval["start_seconds"],
            3,
        )
        interval["interpretation"] = (
            "Estimated visible facial expression; "
            "not proof of internal emotional state."
        )

    return timeline


# --------------------------------------------------
# 8. MAIN VIDEO ANALYZER
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export presentation video analysis to JSON."
    )
    parser.add_argument(
        "video",
        help="Path to a prerecorded presentation video",
    )
    parser.add_argument(
        "--expression-interval",
        type=float,
        default=DEFAULT_EXPRESSION_INTERVAL,
        help="Seconds between expression classifier samples",
    )
    args = parser.parse_args()

    video_path = Path(args.video).expanduser()

    if not video_path.is_file():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    if args.expression_interval <= 0:
        raise ValueError("--expression-interval must be positive")

    for model_path in (FACE_MODEL, POSE_MODEL, HAND_MODEL):
        if not model_path.exists():
            raise FileNotFoundError(
                f"Required MediaPipe model is missing: {model_path}"
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading facial-expression classifier...")
    print("The first run may download model files.")

    expression_classifier = pipeline(
        "image-classification",
        model=EXPRESSION_MODEL,
        device=-1,
    )

    print("Loading MediaPipe face, pose and hand models...")

    face_options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(FACE_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    pose_options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(POSE_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hand_options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(HAND_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    fps = video.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        video.release()
        raise RuntimeError(
            "Could not determine video FPS. Please check the video file."
        )

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if frame_count > 0 else 0.0

    session_id = datetime.now().strftime(
        "presentation_%Y%m%d_%H%M%S"
    )
    json_path = OUTPUT_DIR / f"{session_id}_visual_analysis.json"

    frames = []
    expression_samples = []

    frame_index = 0
    next_expression_sample = 0.0
    latest_expression = None

    try:
        with (
            mp.tasks.vision.FaceLandmarker.create_from_options(
                face_options
            ) as face_detector,
            mp.tasks.vision.PoseLandmarker.create_from_options(
                pose_options
            ) as pose_detector,
            mp.tasks.vision.HandLandmarker.create_from_options(
                hand_options
            ) as hand_detector,
        ):
            while True:
                success, frame = video.read()

                if not success:
                    break

                timestamp = frame_index / fps
                timestamp_ms = int(timestamp * 1000)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb,
                )

                face_result = face_detector.detect_for_video(
                    mp_image, timestamp_ms
                )
                pose_result = pose_detector.detect_for_video(
                    mp_image, timestamp_ms
                )
                hand_result = hand_detector.detect_for_video(
                    mp_image, timestamp_ms
                )

                face_detected = bool(face_result.face_landmarks)
                pose_detected = bool(pose_result.pose_landmarks)

                face_data = {
                    "detected": face_detected,
                    "landmarks": [],
                    "blendshapes": {},
                    "expression_estimate": {
                        "label": "uncertain",
                        "confidence": None,
                        "prediction_timestamp_seconds": None,
                        "method": "vit_face_expression",
                    },
                    "signals": None,
                }

                if face_detected:
                    face_landmarks = face_result.face_landmarks[0]
                    face_data["landmarks"] = landmarks_to_list(
                        face_landmarks
                    )

                    blendshapes = {}

                    if face_result.face_blendshapes:
                        blendshapes = blendshapes_to_dict(
                            face_result.face_blendshapes[0]
                        )

                    face_data["blendshapes"] = blendshapes
                    face_data["signals"] = get_facial_signals(
                        blendshapes
                    )

                # Classify at the configured interval rather than
                # running the heavier classifier on every video frame.
                should_sample = (
                    timestamp + 0.000001 >= next_expression_sample
                )

                if should_sample:
                    if face_detected:
                        prediction = classify_expression(
                            expression_classifier,
                            frame,
                            face_result.face_landmarks[0],
                        )
                    else:
                        prediction = {
                            "label": "uncertain",
                            "confidence": None,
                            "scores": {},
                            "method": "vit_face_expression",
                            "reason": "Face not detected at sample time",
                        }

                    sample = {
                        "timestamp_seconds": rounded(timestamp, 3),
                        **prediction,
                    }
                    expression_samples.append(sample)
                    latest_expression = sample

                    # Advance by intervals, even if a frame is delayed.
                    while next_expression_sample <= timestamp:
                        next_expression_sample += (
                            args.expression_interval
                        )

                if latest_expression is not None:
                    face_data["expression_estimate"] = {
                        "label": latest_expression["label"],
                        "confidence": latest_expression.get("confidence"),
                        "prediction_timestamp_seconds": (
                            latest_expression["timestamp_seconds"]
                        ),
                        "method": latest_expression["method"],
                        "scores": latest_expression.get("scores", {}),
                    }

                body_data = {
                    "detected": pose_detected,
                    "landmarks": [],
                    "measurements": None,
                }

                if pose_detected:
                    body_landmarks = pose_result.pose_landmarks[0]
                    body_data["landmarks"] = landmarks_to_list(
                        body_landmarks
                    )
                    body_data["measurements"] = (
                        calculate_pose_metrics(body_landmarks)
                    )

                hands_data = []
                hand_landmark_groups = hand_result.hand_landmarks
                handedness_groups = hand_result.handedness

                for hand_index, hand_landmarks in enumerate(
                    hand_landmark_groups
                ):
                    handedness = "unknown"

                    if (
                        hand_index < len(handedness_groups)
                        and handedness_groups[hand_index]
                    ):
                        handedness = (
                            handedness_groups[hand_index][0].category_name
                        )

                    hands_data.append({
                        "handedness": handedness,
                        "landmarks": landmarks_to_list(hand_landmarks),
                        "finger_states": get_finger_states(
                            hand_landmarks
                        ),
                        "gesture_estimate": "not_classified",
                    })

                frames.append({
                    "timestamp_seconds": rounded(timestamp, 4),
                    "frame_index": frame_index,
                    "face": face_data,
                    "body": body_data,
                    "hands": {
                        "detected_count": len(hands_data),
                        "items": hands_data,
                    },
                    "quality": {
                        "face_detected": face_detected,
                        "pose_detected": pose_detected,
                        "hands_detected": len(hands_data),
                    },
                })

                frame_index += 1

                if frame_index % 100 == 0:
                    print(f"Processed {frame_index} frames...")

    finally:
        video.release()

    if frame_count <= 0:
        duration = frame_index / fps

    # Use the actual processed duration rather than relying only
    # on the container's reported frame count.
    duration = frame_index / fps if frame_index > 0 else 0.0

    expression_timeline = build_expression_timeline(
        expression_samples,
        duration,
    )

    label_counts = {}
    for sample in expression_samples:
        label = sample["label"]
        label_counts[label] = label_counts.get(label, 0) + 1

    summary = {
        "frames_processed": frame_index,
        "face_detection_percentage": rounded(
            100 * sum(f["face"]["detected"] for f in frames)
            / len(frames), 2
        ) if frames else 0,
        "pose_detection_percentage": rounded(
            100 * sum(f["body"]["detected"] for f in frames)
            / len(frames), 2
        ) if frames else 0,
        "expression_sample_count": len(expression_samples),
        "expression_sample_counts": label_counts,
        "expression_intervals": len(expression_timeline),
        "limitations": [
            "Facial-expression labels are model estimates, not verified internal emotions.",
            "The expression model is not validated specifically for presentation coaching.",
            "Head orientation and gaze direction are not calculated in this version.",
            "Finger states are geometric heuristics, not validated gesture recognition.",
            "Gesture classification is not implemented yet.",
            "Missing detections must not be interpreted as absence of movement.",
        ],
    }

    output = {
        "schema_version": "1.0",
        "session_id": session_id,
        "source": {
            "video_file": video_path.name,
            "fps": rounded(fps, 3),
            "duration_seconds": rounded(duration, 3),
            "frame_count_reported": frame_count,
            "frame_count_processed": frame_index,
        },
        "models": {
            "face": "MediaPipe FaceLandmarker",
            "body": "MediaPipe PoseLandmarker Lite",
            "hands": "MediaPipe HandLandmarker",
            "expression": EXPRESSION_MODEL,
            "expression_sample_interval_seconds": (
                args.expression_interval
            ),
            "minimum_expression_score": MIN_EXPRESSION_SCORE,
        },
        "frames": frames,
        "expression_samples": expression_samples,
        "expression_timeline": expression_timeline,
        "session_summary": summary,
    }

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, indent=2, ensure_ascii=False)

    print("\nVIDEO ANALYSIS COMPLETED")
    print("------------------------")
    print(f"Frames processed: {frame_index}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Expression intervals: {len(expression_timeline)}")
    print(f"JSON saved to: {json_path}")


if __name__ == "__main__":
    main()
