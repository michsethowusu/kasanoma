#!/usr/bin/env python3
"""
Kasanoma TTS Server
A local web application for text-to-speech conversion using Piper TTS
"""

import os
import sys
import platform
import subprocess
import tempfile
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash
import threading
import time

app = Flask(__name__)

class PiperTTS:
    def __init__(self):
        self.system = platform.system().lower()
        self.base_path = Path(__file__).parent
        
        if self.system == "windows":
            self.piper_path = self.base_path / "piper-windows" / "piper.exe"
            self.voice_path = self.base_path / "piper-windows" / "voices"
        else:
            self.piper_path = self.base_path / "piper-linux" / "piper"
            self.voice_path = self.base_path / "piper-linux" / "voices"
        
        self.available_voices = self._get_available_voices()
        self.current_voice = None
        self._set_default_voice()
    
    def _get_available_voices(self):
        """Get list of available voice models"""
        voices = []
        if self.voice_path.exists():
            for voice_file in self.voice_path.glob("*.onnx"):
                voice_name = voice_file.stem
                voices.append({
                    'name': voice_name,
                    'path': str(voice_file),
                    'display_name': voice_name.replace('_', ' ').title()
                })
        return voices
    
    def _set_default_voice(self):
        """Set the first available voice as default"""
        if self.available_voices:
            self.current_voice = self.available_voices[0]['path']
    
    def set_voice(self, voice_name):
        """Set the voice to use for TTS"""
        for voice in self.available_voices:
            if voice['name'] == voice_name:
                self.current_voice = voice['path']
                return True
        return False
    
    def text_to_speech(self, text, output_path):
        """Convert text to speech using Piper TTS"""
        if not self.current_voice:
            return False, "No voice selected"
        
        if not self.piper_path.exists():
            return False, f"Piper executable not found at {self.piper_path}"
        
        try:
            # Create temporary output file
            output_file = Path(output_path)
            
            # Build command
            cmd = [
                str(self.piper_path),
                "--model", self.current_voice,
                "--output_file", str(output_file)
            ]
            
            # Run Piper TTS
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and output_file.exists():
                return True, str(output_file)
            else:
                return False, f"TTS failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "TTS operation timed out"
        except Exception as e:
            return False, f"TTS error: {str(e)}"

# Initialize TTS engine
tts_engine = PiperTTS()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', voices=tts_engine.available_voices)

@app.route('/api/voices')
def get_voices():
    """Get available voices"""
    return jsonify(tts_engine.available_voices)

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.get_json()
    text = data.get('text', '').strip()
    voice = data.get('voice', '')
    
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    # Set voice if specified
    if voice:
        if not tts_engine.set_voice(voice):
            return jsonify({'success': False, 'error': 'Invalid voice'}), 400
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Convert text to speech
        success, result = tts_engine.text_to_speech(text, output_path)
        
        if success:
            return jsonify({
                'success': True,
                'audio_file': result,
                'message': 'TTS conversion successful'
            })
        else:
            return jsonify({'success': False, 'error': result}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and convert to speech"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    voice = request.form.get('voice', '')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check file type
    allowed_extensions = {'.txt', '.md', '.doc', '.docx', '.pdf'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': f'File type {file_ext} not supported. Use: {", ".join(allowed_extensions)}'}), 400
    
    try:
        # Read file content
        if file_ext == '.pdf':
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            except ImportError:
                return jsonify({'success': False, 'error': 'PDF support not available. Please install PyPDF2.'}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': f'PDF reading error: {str(e)}'}), 400
        elif file_ext in {'.doc', '.docx'}:
            try:
                import docx
                doc = docx.Document(file)
                content = ""
                for paragraph in doc.paragraphs:
                    content += paragraph.text + "\n"
            except ImportError:
                return jsonify({'success': False, 'error': 'Word document support not available. Please install python-docx.'}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': f'Word document reading error: {str(e)}'}), 400
        else:
            # Text files
            content = file.read().decode('utf-8')
    
        if not content.strip():
            return jsonify({'success': False, 'error': 'File is empty'}), 400
        
        # Set voice if specified
        if voice:
            if not tts_engine.set_voice(voice):
                return jsonify({'success': False, 'error': 'Invalid voice'}), 400
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Convert text to speech
        success, result = tts_engine.text_to_speech(content, output_path)
        
        if success:
            return jsonify({
                'success': True,
                'audio_file': result,
                'message': 'File converted to speech successfully'
            })
        else:
            return jsonify({'success': False, 'error': result}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'File processing error: {str(e)}'}), 500

@app.route('/api/audio/<filename>')
def get_audio(filename):
    """Serve audio files"""
    # Security: only allow .wav files
    if not filename.endswith('.wav'):
        return jsonify({'error': 'Invalid file type'}), 400
    
    file_path = Path(tempfile.gettempdir()) / filename
    if file_path.exists():
        return send_file(str(file_path), mimetype='audio/wav')
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/status')
def status():
    """Get system status"""
    return jsonify({
        'system': platform.system(),
        'piper_path': str(tts_engine.piper_path),
        'piper_exists': tts_engine.piper_path.exists(),
        'voice_count': len(tts_engine.available_voices),
        'current_voice': tts_engine.current_voice
    })

if __name__ == '__main__':
    # Check if Piper is available
    if not tts_engine.piper_path.exists():
        print(f"Warning: Piper executable not found at {tts_engine.piper_path}")
        print("Please ensure Piper is properly installed in the expected directory.")
    
    if not tts_engine.available_voices:
        print("Warning: No voice models found")
        print("Please ensure voice models (.onnx files) are available in the voices directory.")
    
    print(f"Starting Kasanoma TTS Server...")
    print(f"System: {platform.system()}")
    print(f"Piper path: {tts_engine.piper_path}")
    print(f"Available voices: {len(tts_engine.available_voices)}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
