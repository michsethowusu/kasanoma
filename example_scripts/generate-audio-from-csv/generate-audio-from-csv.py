import csv
import subprocess
from pathlib import Path

# ===== CONFIGURATION =====
MODEL = "model.onnx"  # name of your model file in MODEL_DIR
MODEL_DIR = Path("./models")  # where your .onnx and .onnx.json live
OUTPUT_DIR = Path("./wavs")
OUTPUT_DIR.mkdir(exist_ok=True)
METADATA_FILE = Path("metadata.csv")

# Path to Piper binary (change if needed)
PIPER_BIN = "piper"  # or "./piper" if compiled locally

def synthesize(text, output_file):
    """Run Piper CLI to synthesize speech using default parameters."""
    model_path = MODEL_DIR / MODEL
    cmd = [
        PIPER_BIN,
        "--model", str(model_path),
        "--output_file", str(output_file),
        "--text", text
    ]
    subprocess.run(cmd, check=True)

def batch_from_csv(csv_path):
    """
    Synthesizes audio from a CSV file and creates a metadata.csv file.
    The output is stored in the configured OUTPUT_DIR.
    """
    metadata = []
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, start=1):
            text = row["sentence"]
            # Create a file name based on the original row index
            wav_filename = f"audio_{i}.wav"
            output_file = OUTPUT_DIR / wav_filename
            print(f"[{i}] Synthesizing: {text[:40]}... -> {output_file}")
            synthesize(text, output_file)
            
            # Store metadata for the new CSV
            metadata.append({
                "wav_filename": str(output_file),
                "text": text
            })
    
    # Write the collected metadata to a new CSV file
    if metadata:
        with open(METADATA_FILE, 'w', newline='', encoding="utf-8") as meta_csvfile:
            fieldnames = ["wav_filename", "text"]
            writer = csv.DictWriter(meta_csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metadata)
        print(f"\nMetadata has been written to {METADATA_FILE}")

if __name__ == "__main__":
    batch_from_csv("input.csv")
