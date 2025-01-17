from openai import OpenAI
import queue
import sys
import time
import sounddevice as sd
import subprocess
import pygame


from vosk import Model, KaldiRecognizer

q = queue.Queue()
pygame.mixer.init()


# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

history = [
    {"role": "system", "content": "En tant que Jarvis, un assistant vocal intelligent français, tu dois répondre en français avec des phrases courtes et précises adaptées à une sortie vocale. Tes réponses doivent être naturelles et faciles à comprendre."}
]


def appel_llm(history):
    """Appel à l'API du modèle LLM pour générer une réponse."""
    # Désactivation du streaming pour récupérer la réponse complète immédiatement
    completion = client.chat.completions.create(
        model="lmstudio-community/Llama-3.2-1B-Instruct-GGUF",
        messages=history,
        temperature=0.7,
        stream=False,  # Désactive le streaming pour récupérer directement la réponse complète
    )

    # Affichage de la structure complète de la réponse pour inspection
    print("Structure complète de la réponse:")
    print(completion)  # Afficher l'ensemble de la réponse de l'API

    # Essayons d'accéder aux données et de les afficher correctement
    try:
        # Accès correct à la réponse en utilisant l'attribut 'choices'
        if hasattr(completion, 'choices') and len(completion.choices) > 0:
            # Accéder au contenu du message dans le premier choix
            response_text = completion.choices[0].message.content
            print("Réponse du modèle:", response_text)

            tts_speech(response_text)  # Synthétiser la réponse en audio
            pygame.mixer.music.load("speech.wav")  # Charger l'audio généré

            # Jouer l'audio
            pygame.mixer.music.play()

            # Attendre que l'audio finisse
            while pygame.mixer.music.get_busy(): 
                pygame.time.Clock().tick(10)
        else:
            print("Aucun choix trouvé dans la réponse.")
    except Exception as e:
        print("Erreur lors de l'accès à la réponse:", e)



def callback(indata, frames, time, status):
    """Callback pour la capture audio."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def tts_speech(text, model_path = "./piper/models/fr_FR-siwis-medium.onnx", output_file = "speech.wav"):
    """
    Synthétise un texte en audio avec Piper, avec une commande compatible stdin.

    :param text: Le texte à convertir en voix.
    :param model_path: Chemin du modèle vocal.
    :param output_file: Fichier de sortie audio.
    """
    # Chemin complet vers l'exécutable Piper
    piper_executable = "./piper/piper"

    # Construire la commande Piper (utilisant stdin pour le texte)
    command = [
        piper_executable,
        "--model", model_path,
        "--output_file", output_file,
        "--verbose"
    ]

    # Exécuter la commande avec le texte passé via stdin
    try:
        result = subprocess.run(
            command,
            input=text,          # Texte passé via stdin
            text=True,           # Spécifier que le texte est une chaîne
            check=True,          # Générer une exception en cas d'erreur
            stdout=subprocess.PIPE,  # Capturer la sortie standard
            stderr=subprocess.PIPE   # Capturer la sortie d'erreur
        )

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de Piper : {e}")
        print("Erreurs détaillées :", e.stderr)  # Afficher les erreurs


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
