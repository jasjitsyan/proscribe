from flask import Flask, request, jsonify, make_response, render_template, send_from_directory
import openai
import os
from pathlib import Path
from psycopg2 import pool
import psycopg2.extras

# Initialize Flask app
app = Flask(__name__)

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Start the app
if __name__ == '__main__':
    app.run(debug=True)

# PostgreSQL connection setup
DATABASE_URL = os.getenv("DATABASE_URL")
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL, sslmode="require")

# OpenAI Whisper API setup
openai.organization = 'org-yRlfrdqdXMIAYGfdaIqbyL28'
openai.api_key = os.getenv("OPENAI_API_KEY")

# Directory paths for saving audio files
AUDIO_DIR = Path("./audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Route to handle audio transcription
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['audio_file']
    audio_path = AUDIO_DIR / audio_file.filename
    audio_file.save(audio_path)

    # Transcription with OpenAI Whisper
    try:
        with open(audio_path, 'rb') as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
        transcribed_text = transcript['text']

        # Get audio metadata
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        # Save transcription metadata in PostgreSQL
        save_transcription(transcribed_text, ip_address, user_agent)

        return jsonify({'transcribedText': transcribed_text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Function to save the transcription and metadata to PostgreSQL
def save_transcription(transcription, ip_address, user_agent):
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
            INSERT INTO transcriptions (transcription, ip_address, user_agent)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (transcription, ip_address, user_agent)
        )
        conn.commit()
        cursor.close()
    finally:
        if conn:
            connection_pool.putconn(conn)

# Start the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
