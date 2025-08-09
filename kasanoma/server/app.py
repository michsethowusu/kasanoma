import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_DIR = Path(__file__).parent
# Default to a bind-mounted data dir for models
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
MODEL_DIR = DATA_DIR / "model"
DEFAULT_MODEL = MODEL_DIR / "model.onnx"
DEFAULT_CONFIG = MODEL_DIR / "model.onnx.json"
OUTPUT_DIR = APP_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Kasanoma TTS Server")
app.mount("/out", StaticFiles(directory=str(OUTPUT_DIR)), name="out")


class SynthesizeRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    text: str
    model_path: Optional[str] = None
    config_path: Optional[str] = None
    output_basename: Optional[str] = "output.wav"
    piper_path: Optional[str] = None
    length_scale: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8
    sentence_silence: float = 0.5


def _find_piper(p: Optional[str]) -> str:
    if p:
        return p
    # Prefer absolute path to avoid PATH issues and permissions
    default = "/opt/piper/piper"
    if os.path.isfile(default) and os.access(default, os.X_OK):
        return default
    return os.environ.get("PIPER_PATH") or "piper"


def _run_piper(
    text: str,
    model: str,
    config: Optional[str],
    out_wav: str,
    piper: str,
    ls: float,
    ns: float,
    nw: float,
    ss: float,
) -> None:
    cmd = [
        piper,
        "--model", str(model),
        "--output_file", str(out_wav),
        "--length_scale", str(ls),
        "--noise_scale", str(ns),
        "--noise_w", str(nw),
        "--sentence_silence", str(ss),
    ]
    if config:
        cmd.extend(["--config", str(config)])

    try:
        subprocess.run(cmd, input=text, text=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"Piper failed: {detail}")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (
        """
        <!doctype html>
        <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>Kasanoma TTS Server</title>
        <style>
          body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:16px}
          label{font-weight:600;display:block;margin:8px 0 4px}
          input,textarea{width:100%;padding:8px;border:1px solid #ccc;border-radius:6px}
          .row{margin:8px 0}
          .buttons{display:flex;gap:12px;align-items:center;margin:12px 0}
          .muted{color:#666}
        </style>
        </head><body>
        <h1>Kasanoma Piper TTS</h1>

        <h2>Enter Text</h2>
        <div class='row'>
          <textarea id='text' rows='6' placeholder='Enter text...'></textarea>
        </div>
        <div class='buttons'>
          <button id='btn_text'>Synthesize Text</button>
          <span id='status_text' class='muted'>Idle</span>
        </div>

        <h2>Upload Text File</h2>
        <div class='row'>
          <input id='file' type='file' accept='.txt,text/plain' />
        </div>
        <div class='buttons'>
          <button id='btn_file'>Synthesize File</button>
          <span id='status_file' class='muted'>Idle</span>
        </div>

        <h2>Result</h2>
        <div class='row'>
          <audio id='player' controls></audio>
        </div>
        <div class='row'>
          <a id='download' href='#' download style='display:none'>Download WAV</a>
        </div>

        <script>
        async function synthesize(endpoint, formData, statusEl) {
          statusEl.textContent = 'Synthesizing…';
          try {
            const res = await fetch(endpoint, { method: 'POST', body: formData });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            const audioUrl = data.url;
            const player = document.getElementById('player');
            const download = document.getElementById('download');
            player.src = audioUrl;
            download.href = audioUrl;
            download.style.display = 'inline-block';
            statusEl.textContent = 'Done';
            try { await player.play(); } catch (e) {}
          } catch (e) {
            console.error(e);
            statusEl.textContent = 'Error: ' + e;
            alert('Synthesis failed: ' + e);
          }
        }

        document.getElementById('btn_text').addEventListener('click', async () => {
          const fd = new FormData();
          fd.append('text', document.getElementById('text').value || '');
          fd.append('length_scale', '1.0');
          fd.append('noise_scale', '0.667');
          fd.append('noise_w', '0.8');
          fd.append('sentence_silence', '0.5');
          await synthesize('/synthesize', fd, document.getElementById('status_text'));
        });

        document.getElementById('btn_file').addEventListener('click', async () => {
          const fileInput = document.getElementById('file');
          if (!fileInput.files || !fileInput.files[0]) { alert('Select a text file first'); return; }
          const fd = new FormData();
          fd.append('file', fileInput.files[0]);
          fd.append('length_scale', '1.0');
          fd.append('noise_scale', '0.667');
          fd.append('noise_w', '0.8');
          fd.append('sentence_silence', '0.5');
          await synthesize('/synthesize_file', fd, document.getElementById('status_file'));
        });
        </script>
        </body></html>
        """
    )


def _finalize_output_name(name: Optional[str]) -> str:
    base = (name or "output.wav").strip() or "output.wav"
    if not base.lower().endswith(".wav"):
        base += ".wav"
    # add timestamp to avoid overwrite
    stem = Path(base).stem
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"{stem}-{ts}.wav"


@app.post("/synthesize")
async def synthesize(
    text: str = Form(...),
    length_scale: float = Form(1.0),
    noise_scale: float = Form(0.667),
    noise_w: float = Form(0.8),
    sentence_silence: float = Form(0.5),
):
    model = str(DEFAULT_MODEL)
    config: Optional[str] = str(DEFAULT_CONFIG)

    if not Path(model).is_file():
        raise HTTPException(status_code=400, detail=f"Model not found: {model}")
    if config is not None and not Path(config).is_file():
        raise HTTPException(status_code=400, detail=f"Config not found: {config}")

    out_name = _finalize_output_name("output.wav")
    out_wav = OUTPUT_DIR / out_name
    piper = _find_piper(None)
    _run_piper(text, model, config, str(out_wav), piper, length_scale, noise_scale, noise_w, sentence_silence)
    return JSONResponse({"url": f"/out/{out_name}", "filename": out_name})


@app.post("/synthesize_file")
async def synthesize_file(
    file: UploadFile = File(...),
    length_scale: float = Form(1.0),
    noise_scale: float = Form(0.667),
    noise_w: float = Form(0.8),
    sentence_silence: float = Form(0.5),
):
    model = str(DEFAULT_MODEL)
    config: Optional[str] = str(DEFAULT_CONFIG)

    if not Path(model).is_file():
        raise HTTPException(status_code=400, detail=f"Model not found: {model}")
    if config is not None and not Path(config).is_file():
        raise HTTPException(status_code=400, detail=f"Config not found: {config}")

    content_bytes = await file.read()
    try:
        text = content_bytes.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file must be UTF-8 text")

    out_name = _finalize_output_name("output.wav")
    out_wav = OUTPUT_DIR / out_name
    piper = _find_piper(None)
    _run_piper(text, model, config, str(out_wav), piper, length_scale, noise_scale, noise_w, sentence_silence)
    return JSONResponse({"url": f"/out/{out_name}", "filename": out_name})
