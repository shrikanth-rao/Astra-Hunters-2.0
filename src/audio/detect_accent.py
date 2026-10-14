import torchaudio
from speechbrain.pretrained.interfaces import foreign_class
from pathlib import Path

def detect_accent():
    audio_path = Path("data/processed/presentation.wav") 
    output_dir = Path("output/audio_out")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_txt = output_dir / f"{audio_path.stem}_accent.txt"

    if not audio_path.exists():
        print(f"Error: Could not find audio file at {audio_path.resolve()}")
        return

    print("Loading the SpeechBrain accent classifier model...")
    classifier = foreign_class(
        source="bookbot/english-accent-classifier", 
        pymodule_file="custom_interface.py", 
        classname="CustomEncoderWav2vec2Classifier"
    )

    print(f"\nAnalyzing accent for: {audio_path.name}")
    try:
        # Run classification
        _, score, _, text_lab = classifier.classify_file(str(audio_path))
        
        # 1. Get the accent text
        detected_accent = text_lab[0]
        
        # 2. Get the confidence score (multiply by 100 to get a standard percentage)
        raw_score = score.item() if hasattr(score, 'item') else score[0]
        confidence_percentage = raw_score * 100

        print(f"-> Detected Accent: {detected_accent.upper()} ({confidence_percentage:.2f}%)")

        # 3. Save exactly the three requested lines
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(f"Audio File: {audio_path.name}\n")
            f.write(f"Detected Accent: {detected_accent}\n")
            f.write(f"Confidence (score): {confidence_percentage:.2f}%\n")
            
        print(f"Results saved to: {output_txt.resolve()}")

    except Exception as e:
        print(f"An error occurred during classification: {e}")

if __name__ == "__main__":
    detect_accent()