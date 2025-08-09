# Kasanoma TTS Server

An offline text‑to‑speech app specifically built for African languages that runs fully offline on your computer with no internet access during synthesis. The app supports generating speech from short text or documents.


## Quick start (offline)

1. Download, install and run Docker Desktop for your PC (Windows, Linux or Mac)

2. Unzip the downloaded archive to any location on your computer

3. Open the extracted folder and run the file run-prebuilt.ps1 (for Windows) or run-prebuilt.sh (for Linux/macOS)

4. You should see a message in your terminal or powershell saying "Running kasanoma-piper:latest on http://localhost:8000"

5. Go to `http://localhost:8000` in your browser and start coverting text to speech.


## Troubleshooting
- “Model not found”: verify `model/model.onnx` exists.
- “Config not found”: verify `model/model.onnx.json` exists.
- Port already in use: run with a different `PORT`. Eg. Windows: ./run-prebuilt.ps1 -Port 9000 or Linux/MacOS: PORT=9000 ./run-prebuilt.sh 
- Docker not found: ensure to download, install and run the Docker desktop app before running the script.

## How it works (high level)
- The Docker image contains:
  - Piper binary and espeak‑ng data
  - A small FastAPI app (`server/app.py`) that invokes Piper with your model
- Your model stays on your machine and is mounted into the container at `/data/model`
- The web UI is served locally at `http://localhost:<PORT>`

If you encounter any challenges or have feedback or would like to contribute, please send me an email - michsethowusu@gmail.com. The best way to contribute to the development is to share feedback so we can improve it.
