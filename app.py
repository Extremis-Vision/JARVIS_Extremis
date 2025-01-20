from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json
import logging
import traceback
import numpy as np

# Configuration des logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)

app = Flask(__name__)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True, 
    engineio_logger=True
)

# Variables globales
model = None
recognizers = {}

def initialize_vosk_model(model_path):
    """Initialisation s�curis�e du mod�le Vosk"""
    global model
    try:
        model = Model(model_path)
        logging.info("Mod�le Vosk charg� avec succ�s")
    except Exception as e:
        logging.error(f"Erreur de chargement du mod�le Vosk : {e}")
        model = None

def clean_text(text):
    """Nettoyage et normalisation du texte"""
    try:
        # Suppression des caract�res sp�ciaux et normalisation
        text = text.strip()
        text = ''.join(char for char in text if char.isprintable())
        return text.lower()
    except Exception as e:
        logging.error(f"Erreur de nettoyage du texte : {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    if model is None:
        logging.warning("Mod�le Vosk non initialis�")
        return False
    
    session_id = request.sid
    try:
        # Cr�ation d'un nouveau recognizer par session
        recognizer = KaldiRecognizer(model, 16000)
        recognizers[session_id] = recognizer
        logging.info(f"Nouvelle connexion : {session_id}")
    except Exception as e:
        logging.error(f"Erreur de cr�ation du recognizer : {e}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in recognizers:
        del recognizers[session_id]
    logging.info(f"D�connexion : {session_id}")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    session_id = request.sid
    recognizer = recognizers.get(session_id)
    
    if recognizer is None:
        logging.warning("Pas de recognizer pour cette session")
        return

    try:
        # Conversion s�curis�e des donn�es
        if isinstance(data, dict) and '_placeholder' in data:
            return
        
        # V�rification de la taille des donn�es
        if len(data) < 1024:
            logging.warning("Donn�es audio insuffisantes")
            return

        # Traitement des donn�es audio
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = clean_text(result.get('text', ''))
            
            if text:
                logging.info(f"R�sultat final : {text}")
                socketio.emit('transcription', {
                    'text': text, 
                    'final': True
                })
        else:
            partial_result = json.loads(recognizer.PartialResult())
            text = clean_text(partial_result.get('partial', ''))
            
            if text:
                logging.info(f"R�sultat partiel : {text}")
                socketio.emit('transcription', {
                    'text': text, 
                    'final': False
                })
    
    except Exception as e:
        logging.error(f"Erreur de traitement audio : {e}")
        logging.error(traceback.format_exc())

if __name__ == '__main__':
    # Initialisation du mod�le Vosk
    initialize_vosk_model("./model")
    
    if model:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        logging.error("Impossible de d�marrer l'application : mod�le Vosk non charg�")
