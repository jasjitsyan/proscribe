from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
import os
from pydub import AudioSegment
import openai
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        if file:
            uploads_dir = 'uploads'
            os.makedirs(uploads_dir, exist_ok=True)  # Ensure the directory exists

            file_path = os.path.join(uploads_dir, file.filename)
            file.save(file_path)

            # Convert .m4a to .wav
            wav_path = file_path.replace('.m4a', '.wav')
            audio = AudioSegment.from_file(file_path)
            audio.export(wav_path, format='wav')

            # Speech-to-text
            recognizer = sr.Recognizer()
            audio_file = sr.AudioFile(wav_path)
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
        else:
            return jsonify({"error": "No file uploaded"}), 400
    except Exception as e:
        logging.exception("Error processing the file")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
