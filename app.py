from flask import Flask, request, send_file, render_template
import os
from transcribe import transcribe_audio, save_to_word

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    text = transcribe_audio(file_path)
    output_path = os.path.join("uploads", "output.docx")
    save_to_word(text, output_path)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
