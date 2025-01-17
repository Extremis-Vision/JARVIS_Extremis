import subprocess

def synthesize_with_piper(text, model_path = "./piper/models/fr_FR-siwis-medium.onnx", output_file = "speech.wav"):
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

    print("Commande exécutée :", " ".join(command))  # Afficher la commande

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
        print(f"Audio généré avec succès dans '{output_file}'")
        print("Sortie standard :", result.stdout)
        print("Erreurs standard :", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de Piper : {e}")
        print("Erreurs détaillées :", e.stderr)  # Afficher les erreurs

if __name__ == "__main__":
    # Exemple d'utilisation
    text_to_speak = "Jarvice a votre service monsieur. que puis-je faire pour vous"
    model_path = "./piper/models/fr_FR-siwis-medium.onnx"
    output_file = "welcome.wav"

    synthesize_with_piper(text_to_speak)
