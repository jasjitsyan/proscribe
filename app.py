from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
import os
from pathlib import Path
import openai

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        file_path = os.path.join("uploads", file.filename)
        file.save(file_path)

        # Speech-to-text
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(file_path)
        with audio_file as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)

        # Configuration and paths
        openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
        openai.api_key = "sk-proj-iXpA1QzCyeOwS9ORRxACT3BlbkFJgZm1iSBO3S8S64bGddlS"

        # Open the most recent audio file and transcribe it
        with open(file_path, "rb") as f:
            transcription = openai.Audio.transcribe("whisper-1", f)

        # System prompt
        system_prompt = """
        You are a helpful assistant for a cardiology doctor. Your task is to take the text and convert the points provided into prose...
        (the rest of your system prompt)
        """

        def generate_corrected_transcript(temperature, system_prompt, transcribed_text):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                temperature=0.2,
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

        # Generate corrected transcript
        corrected_text = generate_corrected_transcript(0.2, system_prompt, transcription['text'])

        # Format the text to display as HTML
        formatted_text = corrected_text.replace('\n', '<br>')

        return jsonify({"formatted_text": formatted_text})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
