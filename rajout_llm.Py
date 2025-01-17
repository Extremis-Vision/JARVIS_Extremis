from openai import OpenAI
import queue
import sys
import time
import sounddevice as sd

from vosk import Model, KaldiRecognizer

q = queue.Queue()


# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

history = [
    {"role": "system", "content": "As Jarvis an AI voice assistant, you will be provided with various data in JSON format. Your job is to interpret the data and respond with a short, precise sentence suitable for voice output. The response should be natural and easy to understand.Always respond with short sentences in french."}
]


def appel_llm(history):
        completion = client.chat.completions.create(
            model="lmstudio-community/Llama-3.2-1B-Instruct-GGUF",
            messages=history,
            temperature=0.7,
            stream=True,
        )

        new_message = {"role": "assistant", "content": ""}
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                new_message["content"] += chunk.choices[0].delta.content


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
                    global history  # pour accéder à la variable globale
                    print("Commande envoyer")
                    history = [{"role": "user", "content": phrase_complete}]  # nouveau message ajouté
                    appel_llm(history)
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
