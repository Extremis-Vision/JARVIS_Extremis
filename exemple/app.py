from flask import Flask, render_template, request, send_from_directory
import subprocess
import os
import uuid
import shutil

app = Flask(__name__)

AUDIO_FOLDER = os.path.join(app.root_path, 'static', 'audio')

def clear_audio_folder():
    """
    Vide le dossier audio au démarrage de l'application.
    """
    if os.path.exists(AUDIO_FOLDER):
        # Supprime tous les fichiers .wav existants
        for file_name in os.listdir(AUDIO_FOLDER):
            if file_name.endswith('.wav'):
                file_path = os.path.join(AUDIO_FOLDER, file_name)
                os.remove(file_path)
        print("Ancien(s) fichier(s) audio supprimé(s).")
    else:
        os.makedirs(AUDIO_FOLDER)  # Recrée le dossier s'il n'existe pas

def synthesize_with_piper(text, model_path="./piper/models/fr_FR-siwis-medium.onnx", output_file=AUDIO_FOLDER):
    """
    Synthétise un texte en audio avec Piper et génère un fichier .wav unique à chaque fois.
    """
    # Créer un nom de fichier unique basé sur UUID
    file_name = f"{uuid.uuid4()}.wav"
    output_file = os.path.join(output_file, file_name)

    piper_executable = "./piper/piper"

    command = [
        piper_executable,
        "--model", model_path,
        "--output_file", output_file,
        "--verbose"
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
        print(f"Audio généré avec succès dans '{output_file}'")
        print("Sortie standard :", result.stdout)
        print("Erreurs standard :", result.stderr)
        return file_name  # Retourne le nom du fichier généré
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de Piper : {e}")
        print("Erreurs détaillées :", e.stderr)
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form["text"]

        # Supprime tous les anciens fichiers audio avant de créer un nouveau
        clear_audio_folder()

        # Générer le nouveau fichier audio avec un nom unique
        audio_file = synthesize_with_piper(text)
        if audio_file:
            return render_template("index.html", text=text, audio_file=f"/static/audio/{audio_file}")
        else:
            return render_template("index.html", text=text, error="Erreur lors de la génération de l'audio.")
    return render_template("index.html", text=None)

@app.route("/static/audio/<filename>")
def download_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    # Vide le dossier audio au démarrage
    clear_audio_folder()
    app.run(debug=True, host='0.0.0.0', port=5000)
