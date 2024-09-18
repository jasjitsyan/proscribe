import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
import openai
from docx import Document
from docx.shared import Pt

# Initialize Flask app
app = Flask(__name__)

# Configuration and paths
AUDIO_DIR = Path("./audio")
OUTPUT_DIR = Path("./text")

@app.route('/')
def index():
    return "Welcome to the transcription app."

# Ensure directories exist
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI API setup
openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
openai_api_key = os.getenv("sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS")
openai.api_key = openai_api_key

system_prompt = """
You are a helpful assistant for a cardiology doctor...
"""  # Your system prompt here

def find_most_recent_file(directory, supported_formats):
    """Find the most recent file in the given directory with a supported format."""
    files = list(directory.glob('*'))
    files = [f for f in files if f.is_file() and f.suffix[1:] in supported_formats]
    if not files:
        raise FileNotFoundError("No supported audio files found in the directory.")
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file

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

def set_paragraph_format(paragraph):
    """Remove space after paragraph."""
    p_format = paragraph.paragraph_format
    p_format.space_after = Pt(0)

def add_bold_underline_heading(doc, text, level):
    """Add a bold and underlined heading."""
    heading = doc.add_heading(level=level)
    run = heading.add_run(text)
    run.bold = True
    run.underline = True
    set_paragraph_format(heading)

def save_to_word(corrected_text, output_path):
    doc = Document()
    lines = corrected_text.split('\n')
    for line in lines:
        if line.startswith('###'):
            add_bold_underline_heading(doc, line[3:].strip(), level=3)
        elif line.startswith('##'):
            add_bold_underline_heading(doc, line[2:].strip(), level=2)
        elif line.startswith('#'):
            add_bold_underline_heading(doc, line[1:].strip(), level=1)
        else:
            paragraph = doc.add_paragraph(line)
            set_paragraph_format(paragraph)
    doc.save(output_path)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    audio_file = request.files['audio_file']
    supported_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']
    
    if audio_file.filename.split('.')[-1] not in supported_formats:
        return jsonify({'error': 'Unsupported file format'}), 400
    
    # Save the audio file
    audio_file_path = AUDIO_DIR / audio_file.filename
    audio_file.save(audio_file_path)

    # Open the most recent audio file and transcribe it
    with open(audio_file_path, "rb") as f:
        transcription = openai.Audio.transcribe("whisper-1", f)

    # Generate corrected transcript
    corrected_text = generate_corrected_transcript(0.2, system_prompt, transcription['text'])

    # Save to Word file
    output_file = OUTPUT_DIR / f"corrected_transcript_{audio_file_path.stem}.docx"
    save_to_word(corrected_text, output_file)

    # Send back the corrected transcript in the response
    return send_from_directory(OUTPUT_DIR, output_file.name, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
