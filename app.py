from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json
import logging
import traceback
import os

# Configuration des logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

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
        # V�rification du chemin du mod�le
        if not os.path.exists(model_path):
            logger.error(f"Chemin du mod�le invalide : {model_path}")
            return None
        
        model = Model(model_path)
        logger.info("Mod�le Vosk charg� avec succ�s")
        return model
    except Exception as e:
        logger.error(f"Erreur de chargement du mod�le Vosk : {e}")
        logger.error(traceback.format_exc())
        return None

def clean_text(text):
    """Nettoyage et normalisation du texte"""
    try:
        # Suppression des caract�res sp�ciaux et normalisation
        text = text.strip()
        text = ''.join(char for char in text if char.isprintable())
        return text.lower()
    except Exception as e:
        logger.error(f"Erreur de nettoyage du texte : {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    if model is None:
        logger.warning("Mod�le Vosk non initialis�")
        return False
    
    session_id = request.sid
    try:
        # Cr�ation d'un nouveau recognizer par session
        recognizer = KaldiRecognizer(model, 16000)
        recognizers[session_id] = recognizer
        logger.info(f"Nouvelle connexion : {session_id}")
    except Exception as e:
        logger.error(f"Erreur de cr�ation du recognizer : {e}")
        logger.error(traceback.format_exc())
        return False

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in recognizers:
        del recognizers[session_id]
    logger.info(f"D�connexion : {session_id}")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    session_id = request.sid
    recognizer = recognizers.get(session_id)
    
    if recognizer is None:
        logger.warning("Pas de recognizer pour cette session")
        return

    try:
        # Conversion s�curis�e des donn�es
        if isinstance(data, dict) and '_placeholder' in data:
            return
        
        # V�rification de la taille des donn�es
        if len(data) < 2048:
            logger.warning("Donn�es audio insuffisantes")
            return

        # Traitement des donn�es audio avec gestion des erreurs
        try:
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = clean_text(result.get('text', ''))
                
                if text:
                    logger.info(f"R�sultat final : {text}")
                    socketio.emit('transcription', {
                        'text': text, 
                        'final': True
                    })
            else:
                partial_result = json.loads(recognizer.PartialResult())
                text = clean_text(partial_result.get('partial', ''))
                
                if text:
                    logger.info(f"R�sultat partiel : {text}")
                    socketio.emit('transcription', {
                        'text': text, 
                        'final': False
                    })
        except Exception as vosk_error:
            logger.error(f"Erreur Vosk lors du traitement audio : {vosk_error}")
            logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Erreur de traitement audio globale : {e}")
        logger.error(traceback.format_exc())

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Une erreur est survenue : {e}")
    logger.error(traceback.format_exc())

def find_vosk_model():
    """Recherche automatique du mod�le Vosk"""
    possible_paths = [
        "./model",  # R�pertoire local
        "./vosk-model-fr",  # Mod�le fran�ais
        os.path.expanduser("~/vosk-model-fr"),  # R�pertoire utilisateur
        "/usr/local/share/vosk-model-fr",  # R�pertoire syst�me
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Mod�le Vosk trouv� : {path}")
            return path
    
    logger.error("Aucun mod�le Vosk trouv�")
    return None

if __name__ == '__main__':
    # Recherche et initialisation du mod�le Vosk
    model_path = find_vosk_model()
    
    if model_path:
        model = initialize_vosk_model(model_path)
        
        if model:
            socketio.run(
                app, 
                host='0.0.0.0', 
                port=5000, 
                debug=True
            )
        else:
            logger.error("Impossible de charger le mod�le Vosk")
    else:
        logger.error("Aucun mod�le Vosk disponible")
