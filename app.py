#!/usr/bin/env python3
"""
Kasanoma TTS Server
A local web application for text-to-speech conversion using Piper TTS
Now with multi-language support
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
import re

app = Flask(__name__)

class PiperTTS:
    def __init__(self, default_language="English"):
        self.system = platform.system().lower()
        self.base_path = Path(__file__).parent
        self.default_language = default_language  # User configurable default language (full name)
        
        if self.system == "windows":
            self.piper_path = self.base_path / "piper-windows" / "piper.exe"
            self.voice_base_path = self.base_path / "piper-windows" / "voices"
        else:
            self.piper_path = self.base_path / "piper-linux" / "piper"
            self.voice_base_path = self.base_path / "piper-linux" / "voices"
        
        self.available_languages = self._get_available_languages()
        self.available_voices = self._get_available_voices()
        self.current_language = None
        self.current_voice = None
        self._set_default_language_and_voice()
    
    def _get_available_languages(self):
        """Get list of available languages from folder structure"""
        languages = {}
        if self.voice_base_path.exists():
            # Look for language folders (using full names)
            for lang_dir in self.voice_base_path.iterdir():
                if lang_dir.is_dir():
                    # Check if directory contains .onnx files
                    onnx_files = list(lang_dir.glob("*.onnx"))
                    if onnx_files:
                        folder_name = lang_dir.name
                        # Normalize folder name for consistent display
                        display_name = folder_name.replace('_', ' ').replace('-', ' ').title()
                        
                        languages[folder_name] = {
                            'folder_name': folder_name,
                            'display_name': display_name,
                            'path': str(lang_dir),
                            'voice_count': len(onnx_files)
                        }
            
            # Also check for voices directly in the voices folder (backward compatibility)
            direct_voices = list(self.voice_base_path.glob("*.onnx"))
            if direct_voices and 'Default' not in languages:
                languages['Default'] = {
                    'folder_name': 'Default',
                    'display_name': 'Default',
                    'path': str(self.voice_base_path),
                    'voice_count': len(direct_voices)
                }
        
        return languages
    
    def _get_language_display_name(self, lang_code):
        """Convert language code to display name"""
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'pl': 'Polish',
            'cs': 'Czech',
            'hu': 'Hungarian',
            'tr': 'Turkish',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'uk': 'Ukrainian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'ro': 'Romanian',
            'el': 'Greek',
            'he': 'Hebrew',
            'fa': 'Persian',
            'ur': 'Urdu',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'gu': 'Gujarati',
            'pa': 'Punjabi',
            'mr': 'Marathi',
            'ne': 'Nepali',
            'si': 'Sinhala',
            'my': 'Myanmar',
            'km': 'Khmer',
            'lo': 'Lao',
            'ka': 'Georgian',
            'am': 'Amharic',
            'sw': 'Swahili',
            'zu': 'Zulu',
            'af': 'Afrikaans',
            'is': 'Icelandic',
            'mt': 'Maltese',
            'cy': 'Welsh',
            'ga': 'Irish',
            'eu': 'Basque',
            'ca': 'Catalan'
        }
        
        # Handle multi-part language codes (e.g., en-us, zh-cn)
        base_code = lang_code.split('-')[0].lower()
        if base_code in language_names:
            base_name = language_names[base_code]
            if '-' in lang_code:
                region = lang_code.split('-')[1].upper()
                return f"{base_name} ({region})"
            return base_name
        
        # If not found, return a formatted version of the code
        return lang_code.replace('-', ' ').replace('_', ' ').title()
    
    def _get_available_voices(self):
        """Get list of available voice models organized by language"""
        voices_by_language = {}
        
        for folder_name, lang_info in self.available_languages.items():
            voice_path = Path(lang_info['path'])
            voices = []
            
            for voice_file in voice_path.glob("*.onnx"):
                voice_name = voice_file.stem
                voices.append({
                    'name': voice_name,
                    'path': str(voice_file),
                    'display_name': voice_name.replace('_', ' ').replace('-', ' ').title(),
                    'language': folder_name
                })
            
            if voices:
                voices_by_language[folder_name] = voices
        
        return voices_by_language
    
    def _set_default_language_and_voice(self):
        """Set the default language and voice"""
        # Try to set the user-specified default language
        if self.default_language in self.available_languages and self.default_language in self.available_voices:
            self.current_language = self.default_language
        # Fallback to English if available
        elif 'English' in self.available_languages and 'English' in self.available_voices:
            self.current_language = 'English'
        # Fallback to first available language
        elif self.available_voices:
            self.current_language = list(self.available_voices.keys())[0]
        
        # Set default voice for the selected language
        if self.current_language and self.current_language in self.available_voices:
            if self.available_voices[self.current_language]:
                self.current_voice = self.available_voices[self.current_language][0]['path']
    
    def set_language(self, language_name):
        """Set the language to use for TTS"""
        if language_name in self.available_voices:
            self.current_language = language_name
            # Set the first voice in the language as current voice
            if self.available_voices[language_name]:
                self.current_voice = self.available_voices[language_name][0]['path']
                return True
        return False
    
    def set_voice(self, voice_name, language_name=None):
        """Set the voice to use for TTS"""
        # If language is specified, look only in that language
        if language_name:
            if language_name in self.available_voices:
                for voice in self.available_voices[language_name]:
                    if voice['name'] == voice_name:
                        self.current_language = language_name
                        self.current_voice = voice['path']
                        return True
        else:
            # Search across all languages
            for lang_name, voices in self.available_voices.items():
                for voice in voices:
                    if voice['name'] == voice_name:
                        self.current_language = lang_name
                        self.current_voice = voice['path']
                        return True
        return False
    
    def get_voices_for_language(self, language_name):
        """Get voices available for a specific language"""
        return self.available_voices.get(language_name, [])
    
    def detect_text_language(self, text):
        """Basic text language detection based on character sets and return folder name"""
        # Simple language detection - can be enhanced with proper language detection libraries
        
        # Count character frequencies for different scripts
        latin_chars = len(re.findall(r'[a-zA-ZÀ-ÿ]', text))
        cyrillic_chars = len(re.findall(r'[а-яё]', text, re.IGNORECASE))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        arabic_chars = len(re.findall(r'[\u0600-\u06ff]', text))
        thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', text))
        
        total_chars = len(re.sub(r'\s+', '', text))
        
        if total_chars == 0:
            return self.current_language or self.default_language
        
        # Determine script based on character frequency and match to available folder names
        detected_script = None
        if chinese_chars / total_chars > 0.3:
            detected_script = 'Chinese'
        elif japanese_chars / total_chars > 0.1:
            detected_script = 'Japanese'
        elif korean_chars / total_chars > 0.3:
            detected_script = 'Korean'
        elif cyrillic_chars / total_chars > 0.3:
            detected_script = 'Russian'
        elif arabic_chars / total_chars > 0.3:
            detected_script = 'Arabic'
        elif thai_chars / total_chars > 0.3:
            detected_script = 'Thai'
        elif latin_chars / total_chars > 0.3:
            detected_script = 'English'  # Default for Latin script
        
        # Check if detected language folder exists
        if detected_script and detected_script in self.available_languages:
            return detected_script
        
        # If no specific script detected or folder doesn't exist, use current language
        return self.current_language or self.default_language
    
    def text_to_speech(self, text, output_path, auto_detect_language=False):
        """Convert text to speech using Piper TTS"""
        if not self.current_voice:
            return False, "No voice selected"
        
        if not self.piper_path.exists():
            return False, f"Piper executable not found at {self.piper_path}"
        
        # Auto-detect language if requested
        if auto_detect_language:
            detected_lang = self.detect_text_language(text)
            if detected_lang != self.current_language and detected_lang in self.available_languages:
                self.set_language(detected_lang)
        
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

# Initialize TTS engine with configurable default language
# Change this to your preferred default language (use full folder name)
DEFAULT_LANGUAGE = "English"  # <-- CHANGE THIS TO SET YOUR DEFAULT LANGUAGE (e.g., "Spanish", "French", "German")
tts_engine = PiperTTS(default_language=DEFAULT_LANGUAGE)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         languages=tts_engine.available_languages,
                         voices=tts_engine.available_voices,
                         current_language=tts_engine.current_language,
                         default_language=tts_engine.default_language)

@app.route('/api/languages')
def get_languages():
    """Get available languages"""
    return jsonify({
        'languages': tts_engine.available_languages,
        'current_language': tts_engine.current_language,
        'default_language': tts_engine.default_language
    })

@app.route('/api/voices')
def get_voices():
    """Get available voices, optionally filtered by language"""
    language = request.args.get('language')
    
    if language:
        voices = tts_engine.get_voices_for_language(language)
        return jsonify(voices)
    else:
        return jsonify(tts_engine.available_voices)

@app.route('/api/set-language', methods=['POST'])
def set_language():
    """Set the current language"""
    data = request.get_json()
    language_name = data.get('language')
    
    if not language_name:
        return jsonify({'success': False, 'error': 'No language provided'}), 400
    
    if tts_engine.set_language(language_name):
        return jsonify({
            'success': True,
            'language': language_name,
            'voices': tts_engine.get_voices_for_language(language_name),
            'current_voice': tts_engine.current_voice
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid language'}), 400

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.get_json()
    text = data.get('text', '').strip()
    voice = data.get('voice', '')
    language = data.get('language', '')
    auto_detect = data.get('auto_detect_language', False)
    
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    # Set language if specified
    if language:
        if not tts_engine.set_language(language):
            return jsonify({'success': False, 'error': 'Invalid language'}), 400
    
    # Set voice if specified
    if voice:
        if not tts_engine.set_voice(voice, language):
            return jsonify({'success': False, 'error': 'Invalid voice'}), 400
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Convert text to speech
        success, result = tts_engine.text_to_speech(text, output_path, auto_detect_language=auto_detect)
        
        if success:
            return jsonify({
                'success': True,
                'audio_file': result,
                'message': 'TTS conversion successful',
                'language_used': tts_engine.current_language,
                'voice_used': tts_engine.current_voice
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
    language = request.form.get('language', '')
    auto_detect = request.form.get('auto_detect_language', 'false').lower() == 'true'
    
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
        
        # Set language if specified
        if language:
            if not tts_engine.set_language(language):
                return jsonify({'success': False, 'error': 'Invalid language'}), 400
        
        # Set voice if specified
        if voice:
            if not tts_engine.set_voice(voice, language):
                return jsonify({'success': False, 'error': 'Invalid voice'}), 400
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Convert text to speech
        success, result = tts_engine.text_to_speech(content, output_path, auto_detect_language=auto_detect)
        
        if success:
            return jsonify({
                'success': True,
                'audio_file': result,
                'message': 'File converted to speech successfully',
                'language_used': tts_engine.current_language,
                'voice_used': tts_engine.current_voice
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
        'language_count': len(tts_engine.available_languages),
        'total_voice_count': sum(len(voices) for voices in tts_engine.available_voices.values()),
        'current_language': tts_engine.current_language,
        'current_voice': tts_engine.current_voice,
        'default_language': tts_engine.default_language,
        'languages': tts_engine.available_languages
    })

if __name__ == '__main__':
    # Check if Piper is available
    if not tts_engine.piper_path.exists():
        print(f"Warning: Piper executable not found at {tts_engine.piper_path}")
        print("Please ensure Piper is properly installed in the expected directory.")
    
    if not tts_engine.available_languages:
        print("Warning: No language folders or voice models found")
        print("Please ensure voice models (.onnx files) are organized in language folders under the voices directory.")
        print("Example structure:")
        print("  voices/")
        print("    English/")
        print("      voice1.onnx")
        print("    Spanish/")
        print("      voice1.onnx")
        print("    French/")
        print("      voice1.onnx")
    
    print(f"Starting Kasanoma TTS Server...")
    print(f"System: {platform.system()}")
    print(f"Piper path: {tts_engine.piper_path}")
    print(f"Default language: {tts_engine.default_language}")
    print(f"Current language: {tts_engine.current_language}")
    print(f"Available languages: {len(tts_engine.available_languages)}")
    for folder_name, lang_info in tts_engine.available_languages.items():
        print(f"  - {lang_info['display_name']} ({folder_name}): {lang_info['voice_count']} voices")
    
    app.run(host='0.0.0.0', port=5000, debug=False)