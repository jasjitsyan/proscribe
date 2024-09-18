import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import openai
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.organization = os.getenv('OPENAI_ORGANIZATION')
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {
    'flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm'
}

# Ensure that the directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        if line.startswith('###'):  # Heading level 3
            add_bold_underline_heading(doc, line[3:].strip(), level=3)
        elif line.startswith('##'):  # Heading level 2
            add_bold_underline_heading(doc, line[2:].strip(), level=2)
        elif line.startswith('#'):  # Heading level 1
            add_bold_underline_heading(doc, line[1:].strip(), level=1)
        elif line.startswith('- '):  # Bullet points
            paragraph = doc.add_paragraph(line, style='ListBullet')
            set_paragraph_format(paragraph)
        else:
            paragraph = doc.add_paragraph(line)
            set_paragraph_format(paragraph)
    doc.save(output_path)

def generate_corrected_transcript(temperature, system_prompt, transcribed_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcribed_text
            }
        ]
    )
    return response.choices[0].message['content']

# System prompt
SYSTEM_PROMPT = """
You are a helpful assistant for a cardiology doctor. Your task is to take the text and convert the points provided into prose. Correct any spelling and grammar discrepancies, using English UK, in the transcribed text. Maintain accuracy of the transcription and use only context provided. Format the output into a medical letter under the following headings: '###Reason for Referral/Diagnosis', '###Medications', '###Clinical Review', '###Diagnostic Tests', '###Plan', and '###Actions for GP' The "Reason for Referral/Diagnosis should be a numbered list. The 'Medications' should be in a sentence, capitalise the first letter of the drug name and separate them by commas. Format the 'Clinical Review' in paragraphs for readability. Always leave the 'Diagnostic Tests' blank. Do not add any address options at the beginning or any signatures at the end.
Important not to redact the plan from the clinical review. Keep the accurate prose plan in the clinical review, and also create a list of points for the 'Plan' and 'Actions for GP'.
Always start the 'Clinical Review' with 'It was a pleasure reviewing [patient's name] in the Arrhythmia clinic on behalf of Dr. today. [He/She] is a [age] year old patient...'
At the end of the letter always finish with:
'###Signature'
Dr. Jasjit Syan
Cardiology Registrar

Cardiology Department: Telephone: 020 8321 5336/Email: caw-tr.westmidadmin7@nhs.net
Appointments: 020 8321 5610 Email: caw-tr.wm-bookingenquiries@nhs.net

Disclaimer: This document has been transcribed from dictation; we apologize for any unintentional spelling mistakes/errors due to the voice recognition software.
"""

@app.route('/')
def upload_form():
    return render_template('index.html', title='Proscribe')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audiofile' not in request.files:
        return 'No file part'
    file = request.files['audiofile']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Transcribe audio using the updated OpenAI Whisper API
        audio_file = open(upload_path, "rb")
        transcription = openai.Audio.create_transcription(
            file=audio_file,
            model="whisper-1"
        )
        transcribed_text = transcription['text']

        # Generate corrected transcript using ChatGPT
        corrected_text = generate_corrected_transcript(
            temperature=0.2,
            system_prompt=SYSTEM_PROMPT,
            transcribed_text=transcribed_text
        )

        # Save the corrected text to a Word document
        output_filename = os.path.splitext(filename)[0] + '.docx'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        save_to_word(corrected_text, output_path)

        return render_template('result.html', filename=output_filename)
    else:
        return 'Invalid file type'

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run()  # Remove debug=True for production
