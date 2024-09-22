# Voice-to-Text Transcription Webapp

This webapp allows users to transcribe voice recordings to text, specifically tailored for medical professionals to create clinic letters.

## Features

- Record audio directly in the browser
- Upload audio files
- Transcribe audio to text
- Generate formatted medical letters as Word documents

## Setup

### Frontend

1. Install dependencies:
   ```
   npm install
   ```

2. Run the development server:
   ```
   npm run dev
   ```

### Backend

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Run the Flask server:
   ```
   python app.py
   ```

## Usage

1. Open the webapp in your browser.
2. Record audio or upload an audio file.
3. Click "Transcribe Audio" to process the audio.
4. Review the transcribed text.
5. Click "Download as Word File" to get the formatted medical letter.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
