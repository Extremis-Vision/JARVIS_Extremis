from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json
import logging
import traceback
import os
import numpy as np
from openai import OpenAI

# Configuration des logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration OpenAI
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

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
    """Initialisation sécurisée du modèle Vosk"""
    global model
    try:
        if not os.path.exists(model_path):
            logger.error(f"Chemin du modèle invalide : {model_path}")
            return None
        
        model = Model(model_path)
        logger.info("Modèle Vosk chargé avec succès")
        return model
    except Exception as e:
        logger.error(f"Erreur de chargement du modèle Vosk : {e}")
        logger.error(traceback.format_exc())
        return None

def clean_text(text):
    """Nettoyage et normalisation du texte"""
    try:
        text = text.strip()
        text = ''.join(char for char in text if char.isprintable())
        return text.lower()
    except Exception as e:
        logger.error(f"Erreur de nettoyage du texte : {e}")
        return ""

def appel_llm(transcription):
    """Appel � l'API du mod�le LLM pour g�n�rer une r�ponse"""
    try:
        history = [
            {"role": "user", "content": transcription}
        ]

        completion = client.chat.completions.create(
            model="lmstudio-community/Llama-3.2-1B-Instruct-GGUF",
            messages=history,
            temperature=0.7,
            stream=True
        )

        response_text = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                chunk_text = chunk.choices[0].delta.content
                response_text += chunk_text
                
                socketio.emit('assistant_response_stream', {
                    'text': chunk_text,
                    'is_final': False
                })
                socketio.sleep(0.05)  # Petit d�lai pour fluidifier l'affichage

        # �mettre la fin de la r�ponse
        socketio.emit('assistant_response_stream', {
            'text': '',
            'is_final': True
        })

        return response_text

    except Exception as e:
        logger.error("Erreur lors de l'acc�s � la r�ponse: %s", e)
        socketio.emit('assistant_response_stream', {
            'text': "Une erreur s'est produite.",
            'is_final': True
        })
        return "Une erreur s'est produite."


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    if model is None:
        logger.warning("Modèle Vosk non initialisé")
        return False
    
    session_id = request.sid
    try:
        recognizer = KaldiRecognizer(model, 16000)
        recognizers[session_id] = {
            'recognizer': recognizer,
            'transcription': ''
        }
        logger.info(f"Nouvelle connexion : {session_id}")
    except Exception as e:
        logger.error(f"Erreur de création du recognizer : {e}")
        logger.error(traceback.format_exc())
        return False

@socketio.on('audio_stream')
def handle_audio_stream(data):
    session_id = request.sid
    session_data = recognizers.get(session_id)
    
    if session_data is None:
        logger.warning("Pas de recognizer pour cette session")
        return

    recognizer = session_data['recognizer']
    
    try:
        if isinstance(data, dict) and '_placeholder' in data:
            return
        
        audio_data = np.frombuffer(data, dtype=np.int16)

        if len(audio_data) < 2048:
            logger.warning("Données audio insuffisantes")
            return

        if recognizer.AcceptWaveform(audio_data.tobytes()):
            result = json.loads(recognizer.Result())
            text = clean_text(result.get('text', ''))
            
            if text:
                logger.info(f"Résultat final : {text}")
                socketio.emit('transcription', {
                    'text': text, 
                    'final': True
                })
                
                socketio.start_background_task(appel_llm, text)
                socketio.emit('stop_recording', room=session_id)

    except Exception as e:
        logger.error(f"Erreur de traitement audio globale : {e}")
        logger.error(traceback.format_exc())

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Une erreur est survenue : {e}")
    logger.error(traceback.format_exc())

def find_vosk_model():
    """Recherche automatique du modèle Vosk"""
    possible_paths = [
        "./model",
        "./vosk-model-fr",
        os.path.expanduser("~/vosk-model-fr"),
        "/usr/local/share/vosk-model-fr",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Modèle Vosk trouvé : {path}")
            return path
    
    logger.error("Aucun modèle Vosk trouvé")
    return None

if __name__ == '__main__':
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
            logger.error("Impossible de charger le modèle Vosk")
    else:
        logger.error("Aucun modèle Vosk disponible")
