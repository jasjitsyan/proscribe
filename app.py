import os
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_from_directory
import openai
from docx import Document
import time

# Initialize Flask app
app = Flask(__name__)

# Configuration and paths
AUDIO_DIR = Path("./audio")
OUTPUT_DIR = Path("./text")

# Ensure directories exist
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI API setup
openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

system_prompt = """
You are a helpful assistant for a cardiology doctor...
"""  # Your system prompt here

def generate_corrected_transcript(temperature, system_prompt, transcribed_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcribed_text}
        ]
    )
    return response.choices[0]['message']['content']

def save_to_word(corrected_text, output_path):
    doc = Document()
    lines = corrected_text.split('\n')
    for line in lines:
        if line.startswith('###'):
            doc.add_heading(line[3:].strip(), level=3)
        elif line.startswith('##'):
            doc.add_heading(line[2:].strip(), level=2)
        elif line.startswith('#'):
            doc.add_heading(line[1:].strip(), level=1)
        else:
            doc.add_paragraph(line)
    doc.save(output_path)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    audio_file = request.files['audio_file']
    audio_file_path = AUDIO_DIR / audio_file.filename
    audio_file.save(audio_file_path)

    # Perform transcription using OpenAI's Whisper API
    try:
        with open(audio_file_path, 'rb') as f:
            transcript = openai.Audio.transcribe("whisper-1", f)

        transcribed_text = transcript['text']
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'transcribedText': transcribed_text})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
