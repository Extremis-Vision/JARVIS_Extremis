from flask import Flask, request, jsonify, render_template
from vosk import Model, KaldiRecognizer
import json
import tempfile
import os
import wave


app = Flask(__name__)

# Assurez-vous que ce chemin pointe vers votre mod�le Vosk
model = Model("./model")

@app.route('/')
def index():
    return render_template('index.html')


from pydub import AudioSegment

@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "Aucun fichier audio trouv�"}), 400
    
    audio_file = request.files['audio']
    
    # Sauvegarder temporairement le fichier audio
    temp_input = "temp_input.webm"
    temp_output = "temp_output.wav"
    audio_file.save(temp_input)
    
    # Convertir en WAV PCM 16 kHz mono
    sound = AudioSegment.from_file(temp_input)
    sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    sound.export(temp_output, format="wav")
    
    # Cr�er un reconnaisseur Kaldi
    rec = KaldiRecognizer(model, 16000)
    
    # Lire et traiter l'audio converti
    with open(temp_output, 'rb') as wf:
        while True:
            data = wf.read(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
    
    # Obtenir le r�sultat final
    final_result = json.loads(rec.FinalResult())
    
    os.remove(temp_input)  # Supprimer les fichiers temporaires
    os.remove(temp_output)
    
    return jsonify({"transcription": final_result.get("text", "")})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
