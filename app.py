from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
from pydub import AudioSegment
import openai
from docx import Document
from docx.shared import Pt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        if not file:
            return "No file uploaded", 400

        # Convert the uploaded file to a format suitable for speech recognition
        audio = AudioSegment.from_file(file)
        audio.export("temp.wav", format="wav")
        
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile("temp.wav")
        with audio_file as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)

        # Your OpenAI API key and organization
        openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
        openai.api_key = "sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS"

        system_prompt = """
        You are a helpful assistant for a cardiology doctor...
        """

        def generate_corrected_transcript(temperature, system_prompt, transcribed_text):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcribed_text}
                ]
            )
            return response.choices[0].message['content']

        corrected_text = generate_corrected_transcript(0.2, system_prompt, text)

        return render_template('result.html', result=corrected_text)

    except Exception as e:
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
