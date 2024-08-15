from flask import Flask, request, render_template, send_file
import openai
from docx import Document
from docx.shared import Pt
from werkzeug.utils import secure_filename
import os

# Configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Temporary storage for uploaded files

# Initialize OpenAI client with the API key and organization
openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
openai.api_key = "sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS"

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def transcribe_audio(audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        transcription = client.audio.transcriptions.create("whisper-1", audio_file)
    return transcription['text']

@app.route("/", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Save uploaded file
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Transcribe audio file
        transcribed_text = transcribe_audio(filepath)

        # Process the transcription or create a document, etc.
        # ...

        return "File uploaded and transcribed successfully!"

    return render_template('upload.html')

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
