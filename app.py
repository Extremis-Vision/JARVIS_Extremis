from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Charger le mod�le Vosk (assurez-vous que le chemin est correct)
model = Model("./model")

# Utiliser un dictionnaire pour stocker les reconnaisseurs par session
recognizers = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    recognizers[session_id] = KaldiRecognizer(model, 16000)
    print(f"New connection: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in recognizers:
        del recognizers[session_id]
    print(f"Disconnected: {session_id}")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    session_id = request.sid
    recognizer = recognizers.get(session_id)
    
    if recognizer is None:
        return
    
    try:
        # V�rifiez que les donn�es audio ne sont pas vides
        if len(data) == 0:
            print("Warning: Received empty audio data")
            return

        # Assurez-vous que les donn�es sont au format correct
        if not isinstance(data, bytes):
            print("Warning: Audio data is not in bytes format")
            return

        # Traitez les donn�es audio avec Vosk
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            print(f"Final result: {result}")
            emit('transcription', {'text': result.get('text', ''), 'final': True})
        else:
            partial_result = json.loads(recognizer.PartialResult())
            print(f"Partial result: {partial_result}")
            emit('transcription', {'text': partial_result.get('partial', ''), 'final': False})
    except Exception as e:
        print(f"Error processing audio stream: {e}")

@socketio.on_error_default
def default_error_handler(e):
    print(f"An error occurred: {e}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
