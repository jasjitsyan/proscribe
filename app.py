import os
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_from_directory
import openai
from docx import Document

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
openai_api_key = os.getenv("sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS")
openai.api_key = openai_api_key

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

def generate_corrected_transcript(temperature, system_prompt, transcribed_text):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcribed_text}
        ]
    )
    return response.choices[0]['message']['content']

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

    # Use OpenAI Whisper to transcribe the audio
    with open(audio_file_path, 'rb') as f:
        transcription = openai.Audio.transcribe("whisper-1", f)
    
    # Now use GPT to format the transcription
    transcribed_text = transcription['text']
    corrected_text = generate_corrected_transcript(0.2, system_prompt, transcribed_text)

    return jsonify({'transcribedText': corrected_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
