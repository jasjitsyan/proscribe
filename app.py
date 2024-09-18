import os
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import openai
from docx import Document
from docx.shared import Pt

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
        return 'No file part', 400
    
    audio_file = request.files['audio_file']
    supported_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']
    
    if audio_file.filename.split('.')[-1] not in supported_formats:
        return 'Unsupported file format', 400
    
    # Save the audio file
    audio_file_path = AUDIO_DIR / audio_file.filename
    audio_file.save(audio_file_path)

    # Open the most recent audio file and transcribe it
    with open(audio_file_path, "rb") as f:
        transcription = openai.Audio.transcribe("whisper-1", f)

    # Generate corrected transcript
    corrected_text = generate_corrected_transcript(0.2, system_prompt, transcription['text'])

    # Save to Word file
    output_file = OUTPUT_DIR / f"corrected_transcript_{audio_file.filename.split('.')[0]}.docx"
    save_to_word(corrected_text, output_file)

    # Provide the download link for the generated Word document
    return redirect(url_for('download_file', filename=output_file.name))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
