from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json
import unicodedata
import re
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')

app = Flask(__name__)
socketio = SocketIO(app, 
                    cors_allowed_origins="*", 
                    logger=True, 
                    engineio_logger=True)

# Charger le mod�le Vosk 
try:
    model = Model("./model")
except Exception as e:
    logging.error(f"Erreur de chargement du mod�le Vosk : {e}")
    model = None

# Utiliser un dictionnaire pour stocker les reconnaisseurs par session
recognizers = {}

def safe_decode(text):
    """
    D�code le texte de mani�re s�curis�e en g�rant diff�rents encodages
    """
    encodings = ['utf-8', 'latin1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            return text.encode('latin1').decode(encoding)
        except UnicodeDecodeError:
            continue
    
    return text

def clean_text(text):
    """
    Nettoie et normalise le texte
    """
    try:
        # D�code le texte de mani�re s�curis�e
        text = safe_decode(text)
        
        # Normalise les caract�res accentu�s
        text = unicodedata.normalize('NFKD', text)
        
        # Supprime les caract�res non imprimables et non alphab�tiques
        text = re.sub(r'[^a-zA-Z�-�\s\']', '', text)
        
        # Convertit en minuscules
        text = text.lower().strip()
        
        return text
    except Exception as e:
        logging.error(f"Erreur de nettoyage du texte : {e}")
        return text

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    if model is None:
        logging.error("Mod�le Vosk non charg�")
        return False
    
    session_id = request.sid
    try:
        recognizers[session_id] = KaldiRecognizer(model, 16000)
        logging.info(f"Nouvelle connexion : {session_id}")
    except Exception as e:
        logging.error(f"Erreur de cr�ation du reconnaisseur : {e}")
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
        logging.warning("Pas de reconnaisseur pour cette session")
        return

    try:
        # V�rifications des donn�es audio
        if not data or len(data) < 1024:
            logging.warning("Donn�es audio insuffisantes")
            return

        # Traitement des donn�es audio
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = clean_text(result.get('text', ''))
            
            if text:
                logging.info(f"R�sultat final : {text}")
                emit('transcription', {
                    'text': text, 
                    'final': True
                })
        else:
            partial_result = json.loads(recognizer.PartialResult())
            text = clean_text(partial_result.get('partial', ''))
            
            if text:
                logging.info(f"R�sultat partiel : {text}")
                emit('transcription', {
                    'text': text, 
                    'final': False
                })
    
    except Exception as e:
        logging.error(f"Erreur de traitement audio : {e}")

@socketio.on_error_default
def default_error_handler(e):
    logging.error(f"Une erreur est survenue : {e}")

if __name__ == '__main__':
    if model:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        logging.error("Impossible de d�marrer l'application : mod�le Vosk non charg�")
