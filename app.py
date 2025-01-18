import sys
import time
import queue
import sounddevice as sd
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer

# Initialisation de l'application Flask
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialisation de la queue et du mod�le Vosk
q = queue.Queue()

# Liste pour stocker l'historique de la conversation
conversation_history = []

# Afficher un message pour indiquer que le mod�le Vosk est en train de se charger
print("Chargement du modèle Vosk...")
model = Model("model")  # Mod�le Vosk situ� dans le dossier 'model' dans la racine
print("Modèle Vosk chargé avec succès.")
samplerate = 16000  # Taux d'�chantillonnage
recognizer = KaldiRecognizer(model, samplerate)

def callback(indata, frames, time, status):
    """Callback pour la capture audio."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_transcription')
def start_transcription():
    global conversation_history
    print("Transcription démarrée !")
    phrase_complete = ""
    last_time = time.time()

    # Cr�er un flux audio
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16", channels=1, callback=callback):
        print("### Reconnaissance vocale en temps réel ###")
        print("Parlez dans votre micro. Appuyez sur Ctrl+C pour quitter.")
        print("##########################################\n")
        
        while True:
            data = q.get()  # R�cup�rer les donn�es audio
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                phrase = result.split('"text" : "')[1].split('"')[0]
                if phrase.strip():
                    phrase_complete += phrase + " "
                    print(f"Phrase complète : {phrase}")
                    conversation_history.append(f"Utilisateur: {phrase}")
                    socketio.emit('transcription', {'text': phrase_complete.strip(), 'history': conversation_history})
            else:
                partial_result = recognizer.PartialResult()
                partial_phrase = partial_result.split('"partial" : "')[1].split('"')[0]
                if partial_phrase.strip():
                    print(f"Résultat partiel : {partial_phrase}", end="\r")
                    socketio.emit('transcription', {'text': partial_phrase, 'history': conversation_history})

            # V�rifier s'il y a eu une pause (silence d�tect�)
            current_time = time.time()
            if current_time - last_time > 1.5:  # 1.5 secondes de silence
                if phrase_complete.strip():
                    print("\n### Fin de phrase détectée ###")
                    print(f"Phrase complète accumulée : {phrase_complete.strip()}")
                    conversation_history.append(f"Utilisateur: {phrase_complete.strip()}")
                    socketio.emit('transcription', {'text': phrase_complete.strip(), 'history': conversation_history})
                    phrase_complete = ""
                last_time = current_time

if __name__ == "__main__":
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nReconnaissance vocale arrêtée.")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur : {str(e)}")
        sys.exit(1)
