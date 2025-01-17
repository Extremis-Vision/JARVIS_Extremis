import queue
import sys
import time
import sounddevice as sd

from vosk import Model, KaldiRecognizer

q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback pour la capture audio."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def main():
    # Charger le modèle depuis le dossier `model`
    model = Model("model")
    samplerate = 16000  # Taux d'échantillonnage
    rec = KaldiRecognizer(model, samplerate)

    # Créer un flux audio
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        print("### Reconnaissance vocale en temps réel ###")
        print("Parlez dans votre micro. Appuyez sur Ctrl+C pour quitter.")
        print("##########################################\n")

        phrase_complete = ""
        last_time = time.time()

        while True:
            # Récupérer les données audio
            data = q.get()
            if rec.AcceptWaveform(data):
                # Une phrase complète est détectée (silence détecté)
                result = rec.Result()
                phrase = result.split('"text" : "')[1].split('"')[0]
                if phrase.strip():
                    print(f"Phrase complète : {phrase}")
                    phrase_complete += phrase + " "
            else:
                # Résultat partiel en cours de reconnaissance
                partial_result = rec.PartialResult()
                partial_phrase = partial_result.split('"partial" : "')[1].split('"')[0]
                if partial_phrase.strip():
                    print(f"Résultat partiel : {partial_phrase}", end="\r")

            # Ajouter une légère latence si aucun nouveau son n'est détecté
            current_time = time.time()
            if current_time - last_time > 1.5:  # 1.5 secondes de silence
                if phrase_complete.strip():
                    print("\n### Fin de phrase détectée ###")
                    print(f"Phrase complète accumulée : {phrase_complete.strip()}")

                    phrase_complete = ""
                last_time = current_time

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReconnaissance vocale arrêtée.")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur : {str(e)}")
        sys.exit(1)
