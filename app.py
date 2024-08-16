from flask import Flask, request, render_template, send_file
import openai
from docx import Document
from docx.shared import Pt
from werkzeug.utils import secure_filename
import os
import torch
import numpy as np
import warnings
from whisper import Whisper  # Assuming you have a Whisper module or class defined

# Configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Temporary storage for uploaded files

# Initialize OpenAI client with the API key and organization
client = openai.OpenAI(
    api_key="sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS",
    organization="org-yRlfrdqdXMIAYGfdaIqbyL28"
)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def transcribe_audio(audio_file_path):
    # Load the Whisper model
    model = Whisper.load_model("your-model-path-or-name")  # Replace with actual model loading code
    
    with open(audio_file_path, 'rb') as audio_file:
        audio = np.frombuffer(audio_file.read(), dtype=np.float32)  # Assuming the audio is in a suitable format

    transcription = transcribe(
        model=model,
        audio=audio,
        verbose=True,  # Set to True for more detailed output
        temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),  # Multiple temperature values
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
        condition_on_previous_text=True,
        word_timestamps=True,  # Include word-level timestamps
        prepend_punctuations="\"'“¿([{-",
        append_punctuations="\"'.。,，!！?？:：”)]}、"
    )

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
        # For example, you could create a Word document with the transcription:
        doc = Document()
        doc.add_paragraph(transcribed_text)
        doc_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.docx")
        doc.save(doc_path)

        return send_file(doc_path, as_attachment=True)

    return render_template('upload.html')

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
