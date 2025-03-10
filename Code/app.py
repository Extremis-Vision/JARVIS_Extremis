from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import json
import logging
import traceback
import os
import numpy as np
from openai import OpenAI
import fonction_jarvis
import fonction_jarvis.meteo
import re
from flask import Flask, render_template, request, send_from_directory  # Ajoutez send_from_directory
import uuid
import subprocess

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
VOSK_MODEL_PATH = None
recognizers = {}

# Ajouter après les autres variables globales
AUDIO_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'audio')

def clear_audio_folder():
    if os.path.exists(AUDIO_FOLDER):
        for file_name in os.listdir(AUDIO_FOLDER):
            if file_name.endswith('.wav'):
                file_path = os.path.join(AUDIO_FOLDER, file_name)
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Erreur suppression fichier audio {file_path}: {e}")
    else:
        os.makedirs(AUDIO_FOLDER)

def synthesize_with_piper(text, model_path="./piper/models/fr_FR-siwis-medium.onnx"):
    clear_audio_folder()
    file_name = f"{uuid.uuid4()}.wav"
    output_file = os.path.join(AUDIO_FOLDER, file_name)
    
    command = [
        "./piper/piper",
        "--model", model_path,
        "--output_file", output_file
    ]

    try:
        result = subprocess.run(
            command,
            input=text,
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return file_name
    except Exception as e:
        logger.error(f"Erreur Piper: {e}")
        return None

@app.route("/static/audio/<filename>")
def download_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

def find_vosk_model():
    """Recherche automatique du modèle Vosk"""
    global VOSK_MODEL_PATH
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

def initialize_vosk_model():
    """Initialisation sécurisée du modèle Vosk"""
    global model, VOSK_MODEL_PATH
    
    if model is not None:
        return model
    
    try:
        if VOSK_MODEL_PATH is None:
            VOSK_MODEL_PATH = find_vosk_model()
        
        if not VOSK_MODEL_PATH or not os.path.exists(VOSK_MODEL_PATH):
            logger.error(f"Chemin du modèle invalide : {VOSK_MODEL_PATH}")
            return None
        
        model = Model(VOSK_MODEL_PATH)
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

def remove_think_tags(text):
    """Supprime les balises <think></think> et leur contenu du texte."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)


def appel_llm(transcription):
    """Appel à l'API du modèle LLM pour générer une réponse"""
    try:
        history = [
            {"role": "user", "content": transcription}
        ]

        completion = client.chat.completions.create(
            model="hermes-3-llama-3.2-3b",
            messages=history,
            temperature=0.7,
            stream=True
        )

        response_text = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                chunk_text = chunk.choices[0].delta.content
                response_text += chunk_text

                cleaned_chunk_text = remove_think_tags(chunk_text)
                socketio.emit('assistant_response_stream', {
                    'text': cleaned_chunk_text,
                    'is_final': False
                })
                socketio.sleep(0.05)

        # Générer l'audio après avoir reçu toute la réponse
        audio_file = synthesize_with_piper(response_text)
        if audio_file:
            socketio.emit('audio_ready', {
                'audio_file': f"/static/audio/{audio_file}"
            })

        socketio.emit('assistant_response_stream', {
            'text': '',
            'is_final': True
        })

        return response_text

    except Exception as e:
        logger.error("Erreur lors de l'accès à la réponse: %s", e)
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
    global model
    
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
                
                socketio.emit('stop_recording', room=session_id)

                # Gestion des commandes météo
                if "quelle est la météo à" in text:
                    ville = text.replace("quelle est la météo à", "").strip()
                    temperature = fonction_jarvis.meteo.météo(ville)
                    if temperature is not None:
                        text += f" La température à {ville} est de {temperature['temperature']} en °C (max : {temperature['temp_max']}, min : {temperature['temp_min']}) avec {temperature['humiditer']} % d'humidité à savoir que {temperature['description']}."
                    else:
                        text += " Je n'ai pas pu récupérer les informations météo."

                elif "quelle est la météo" in text:
                    ville = "Seppois-le-Haut"
                    temperature = fonction_jarvis.meteo.météo(ville)
                    if temperature is not None:
                        text += f" La température à {ville} est de {temperature['temperature']} en °C (max : {temperature['temp_max']}, min : {temperature['temp_min']}) avec {temperature['humiditer']} % d'humidité à savoir que {temperature['description']}."
                    else:
                        text += " Je n'ai pas pu récupérer les informations météo."

                socketio.start_background_task(appel_llm, text)
        else:
            partial_result = json.loads(recognizer.PartialResult())
            partial_text = clean_text(partial_result.get('partial', ''))
            if partial_text:
                socketio.emit('transcription', {
                    'text': partial_text,
                    'final': False
                })

    except Exception as e:
        logger.error(f"Erreur de traitement audio globale : {e}")
        logger.error(traceback.format_exc())

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Une erreur est survenue : {e}")
    logger.error(traceback.format_exc())

@socketio.on('text_input')
def handle_text_input(data):
    text = data.get('text', '')
    if text:
        logger.info(f"Texte reçu : {text}")
        socketio.emit('transcription', {
            'text': text, 
            'final': True
        })

        # Gestion des commandes météo
        if "quelle est la météo à" in text:
                    ville = text.replace("quelle est la météo à", "").strip()
                    temperature = fonction_jarvis.meteo.météo(ville)
                    if temperature is not None:
                        text += f" La température à {ville} est de {temperature['temperature']} en °C (max : {temperature['temp_max']}, min : {temperature['temp_min']}) avec {temperature['humiditer']} % d'humidité à savoir que {temperature['description']}."
                    else:
                        text += " Je n'ai pas pu récupérer les informations météo."

        elif "quelle est la météo" in text:
                    ville = "Seppois-le-Haut"
                    temperature = fonction_jarvis.meteo.météo(ville)
                    if temperature is not None:
                        text += f" La température à {ville} est de {temperature['temperature']} en °C (max : {temperature['temp_max']}, min : {temperature['temp_min']}) avec {temperature['humiditer']} % d'humidité à savoir que {temperature['description']}."
                    else:
                        text += " Je n'ai pas pu récupérer les informations météo."

        socketio.start_background_task(appel_llm, text)

if __name__ == '__main__':
    clear_audio_folder()  # Ajouter cette ligne
    model = initialize_vosk_model()
    
    if model:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True
        )
    else:
        logger.error("Impossible de charger le modèle Vosk")