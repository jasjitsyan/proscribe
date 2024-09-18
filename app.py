import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
import openai
from docx import Document

app = Flask(__name__)

# Ensure the OpenAI API key is available
openai.api_key = os.getenv('sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS')

# Directories for uploads and output
AUDIO_DIR = Path('./audio')
DOCX_DIR = Path('./docs')
AUDIO_DIR.mkdir(exist_ok=True)
DOCX_DIR.mkdir(exist_ok=True)

# System prompt for OpenAI's GPT model
system_prompt = """
You are a helpful assistant for a cardiology doctor. Your task is to take the text and convert the points provided into prose. Correct any spelling and grammar discrepancies, using English UK, in the transcribed text. Maintain accuracy of the transcription and use only context provided. Format the output into a medical letter under the following headings: '###Reason for Referral/Diagnosis', '###Medications', '###Clinical Review', '###Diagnostic Tests', '###Plan', and '###Actions for GP' The "Reason for Referral/Diagnosis should be a numbered list. The 'Medications' should be in a sentence, capitalise the first letter of the drug name and seperate them by commas. Format the 'Clinical Review' in paragraphs for readibility. Always leave the 'Diagnostic Tests' blank. Do not add any address options at the begining or any signatures at the end.
Important not to redact the plan from the clinical review. Keep the accurate prose plan in the clinical review, and also create a list of points for the 'Plan' and 'Actions for GP'.
Always start the 'Clinical Review' with 'It was a pleasure reviewing [patient's name] in the Arrhythmia clinic on behalf of Dr. today. [He/She] is a [age] year old patient...'
At the end of the letter always finish with:
'###Signature'
Dr. Jasjit Syan
Cardiology Registrar
\n
Cardiology Department: Telephone: 020 8321 5336/Email: caw-tr.westmidadmin7@nhs.net
Appointments: 020 8321 5610 Email: caw-tr.wm-bookingenquiries@nhs.net
\n
Disclaimer: This document has been transcribed from dictation; we apologize for any unintentional spelling mistakes/errors due to the voice recognition software.
"""

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio_file']
    file_path = AUDIO_DIR / audio_file.filename
    audio_file.save(file_path)

    try:
        # Transcribe using OpenAI Whisper API
        with open(file_path, 'rb') as f:
            transcription = openai.Audio.transcribe('whisper-1', f)
            transcribed_text = transcription['text']

        # Use GPT to format transcribed text into a medical letter
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcribed_text}
            ]
        )
        formatted_text = response['choices'][0]['message']['content']

        # Create a DOCX file
        doc = Document()
        doc.add_heading('Transcribed Medical Letter', 0)
        doc.add_paragraph(formatted_text)

        # Save the DOCX file
        docx_filename = f"{audio_file.filename.rsplit('.', 1)[0]}.docx"
        docx_path = DOCX_DIR / docx_filename
        doc.save(docx_path)

        return jsonify({'docxFile': docx_filename})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    file_path = DOCX_DIR / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
