#!/usr/bin/env python3
"""
Voice-Only Health Diagnostic App with Piper TTS Integration
"""

import os
import platform
import subprocess
import tempfile
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Health diagnostic questions
QUESTIONS = [
    'Woho ayɛ hyehyeehye anaa? ',
    'Ɛyɛ a wobɔ ɛwa anaa?',
    'Woyɛm ɛyɛ wo ya anaa?',
    'Woti ɛyɛ wo ya anaa?',
    'Woyɛm ehwie anaa?'
]

WELCOME_TEXT = "Me ma wo akwaaba ɛba apomuden nsɛmmisa afidie no so."
READY_CHECK_TEXT = "Nsɛmmisa ennum a etoatoaso no fa wapomuden ho. Sɛ mebusa asem no na ɛyɛ nokorɛ a, mia ahabanmono no so, na sɛ ɛnyɛ nokore a mia kɔkɔɔ no so. Sɛ woayɛ krado sɛ wobɛhyɛ aseɛ a, mia ahabanmono no so."
SUMMARY_TEXT = "Y'afa wommuayɛ no nyinaa."
END_TEXT = "Yeda wo ase."

class PiperTTS:
    def __init__(self):
        self.system = platform.system().lower()
        self.base_path = Path(__file__).parent
        
        if self.system == "windows":
            self.piper_path = self.base_path / "piper" / "piper.exe"
            self.voice_path = self.base_path / "piper" / "voices" / "Twi" / "model.onnx"
        else:
            self.piper_path = self.base_path / "piper" / "piper"
            self.voice_path = self.base_path / "piper" / "voices" / "Twi" / "model.onnx"
        
        # Create voice directory if it doesn't exist
        if not self.voice_path.parent.exists():
            self.voice_path.parent.mkdir(parents=True, exist_ok=True)
        
    def text_to_speech(self, text, output_path):
        """Convert text to speech using Piper TTS"""
        if not self.piper_path.exists():
            return False, f"Piper executable not found at {self.piper_path}"
        
        if not self.voice_path.exists():
            return False, f"Voice model not found at {self.voice_path}"
        
        try:
            cmd = [
                str(self.piper_path),
                "--model", str(self.voice_path),
                "--output_file", str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                return True, str(output_path)
            else:
                return False, f"TTS failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "TTS operation timed out"
        except Exception as e:
            return False, f"TTS error: {str(e)}"

# Initialize TTS engine
tts_engine = PiperTTS()

def generate_audio_files():
    """Pre-generate audio files for all states"""
    audio_files = {}
    
    # Generate welcome message
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    success, result = tts_engine.text_to_speech(WELCOME_TEXT, output_path)
    if success:
        audio_files['welcome'] = result
    
    # Generate ready check message
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    success, result = tts_engine.text_to_speech(READY_CHECK_TEXT, output_path)
    if success:
        audio_files['ready_check'] = result
    
    # Generate question audio
    for i, question in enumerate(QUESTIONS):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        success, result = tts_engine.text_to_speech(question, output_path)
        if success:
            audio_files[f'question_{i}'] = result
    
    # Generate summary audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    success, result = tts_engine.text_to_speech(SUMMARY_TEXT, output_path)
    if success:
        audio_files['summary'] = result

    # Generate end audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    success, result = tts_engine.text_to_speech(END_TEXT, output_path)
    if success:
        audio_files['end'] = result
    
    return audio_files

# Pre-generate audio files at startup
AUDIO_FILES = generate_audio_files()

@app.route('/')
def index():
    """Main application page"""
    # Initialize session state
    session['current_state'] = 'welcome'
    session['current_question_index'] = 0
    session['responses'] = []
    return render_template('index.html')

@app.route('/audio/<audio_key>')
def get_audio(audio_key):
    """Serve audio files"""
    if audio_key in AUDIO_FILES:
        return send_file(AUDIO_FILES[audio_key], mimetype='audio/wav')
    return jsonify({'error': 'Audio not found'}), 404

@app.route('/next_state')
def next_state():
    """Get the next state based on the current session state"""
    state = session.get('current_state', 'welcome')
    idx = session.get('current_question_index', 0)
    
    if state == 'welcome':
        # After welcome, move to ready check
        session['current_state'] = 'ready_check'
        session.modified = True
        return jsonify({
            'type': 'welcome',
            'text': WELCOME_TEXT,
            'audio_key': 'welcome'
        })
    elif state == 'ready_check':
        return jsonify({
            'type': 'ready_check',
            'text': READY_CHECK_TEXT,
            'audio_key': 'ready_check'
        })
    elif state == 'questions':
        if idx < len(QUESTIONS):
            # Return current question
            return jsonify({
                'type': 'question',
                'text': QUESTIONS[idx],
                'audio_key': f'question_{idx}'
            })
        else:
            # All questions answered, move to summary
            session['current_state'] = 'summary'
            session.modified = True
            return jsonify({
                'type': 'summary',
                'text': SUMMARY_TEXT,
                'audio_key': 'summary'
            })
    elif state == 'summary':
        # After summary, move to end state
        session['current_state'] = 'end'
        session.modified = True
        return jsonify({
            'type': 'summary',
            'text': SUMMARY_TEXT,
            'audio_key': 'summary'
        })
    elif state == 'end':
        return jsonify({
            'type': 'end',
            'text': END_TEXT,
            'audio_key': 'end'
        })
    
    return jsonify({
        'type': 'end',
        'text': 'An error occurred. The app has ended.',
        'audio_key': 'end'
    })

@app.route('/answer', methods=['POST'])
def record_answer():
    """Record user answer and move to next state"""
    data = request.get_json()
    answer = data.get('answer')
    state = session.get('current_state')
    idx = session.get('current_question_index', 0)
    
    if state == 'ready_check':
        if answer == 'Yes':
            # Add a 2-second delay here before sending the response
            time.sleep(2)
            session['current_state'] = 'questions'
            session['current_question_index'] = 0
            session.modified = True
        else: # Answer is 'No'
            session['current_state'] = 'end'
            session.modified = True
    
    elif state == 'questions':
        if idx < len(QUESTIONS):
            # Record response
            session['responses'].append({
                'question': QUESTIONS[idx],
                'answer': answer
            })
            session['current_question_index'] = idx + 1
            session.modified = True
        else:
            # This case should not be reached due to logic in next_state
            session['current_state'] = 'summary'
            session.modified = True
    
    return jsonify({'status': 'success'})

@app.route('/responses')
def get_responses():
    """Get all recorded responses"""
    return jsonify(session.get('responses', []))

if __name__ == '__main__':
    # Check if files exist
    if not tts_engine.piper_path.exists():
        print(f"Error: Piper executable not found at {tts_engine.piper_path}")
        print("Please download Piper and place it in the 'piper' directory")
        print("See: https://github.com/rhasspy/piper")
    
    if not tts_engine.voice_path.exists():
        print(f"Error: Voice model not found at {tts_engine.voice_path}")
        print("Please download a voice model and place it in the 'piper/voices/en' directory")
        print("See: https://huggingface.co/rhasspy/piper-voices/tree/main/en")
    
    print("Starting Health Diagnostic App...")
    print(f"System: {platform.system()}")
    print(f"Piper path: {tts_engine.piper_path}")
    print(f"Voice path: {tts_engine.voice_path}")
    print(f"Pre-generated audio files: {len(AUDIO_FILES)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
