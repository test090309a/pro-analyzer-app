# -*- coding: utf-8 -*-

"""
Ein benutzerfreundliches Chat-Interface für ein lokales Ollama Vision-Modell (qwen-vl).
Erstellt mit Gradio.

Funktionen:
- Hochladen eines Bildes.
- Stellen von textbasierten Fragen zum Bildinhalt.
- Anzeige eines interaktiven Chat-Verlaufs.
- Direkte Anbindung an einen lokalen Ollama-Server.
"""

# --- 1. Import der notwendigen Bibliotheken ---
import gradio as gr
import requests
import base64
from PIL import Image
import io
import json

# --- 2. Konfiguration ---
# Passe diese Werte an, falls dein Ollama-Server anders konfiguriert ist.
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Standard-Endpunkt für Ollama
MODEL_NAME = "qwen2.5vl:7b"  # Das spezifische Modell, das du verwenden möchtest

# --- 3. Kernfunktionen ---


def image_to_base64(image_pil: Image.Image) -> str:
    """
    Konvertiert ein Bild im PIL-Format in einen Base64-kodierten String.
    Ollama benötigt Bilder in diesem Format.

    Args:
        image_pil (PIL.Image.Image): Das zu konvertierende Bild.

    Returns:
        str: Der Base64-kodierte String des Bildes.
    """
    buffered = io.BytesIO()
    # Speichere das Bild im JPEG-Format. PNG wird ebenfalls unterstützt.
    image_pil.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def call_ollama_api(base64_image: str, user_question: str):
    """
    Sendet eine Anfrage an die lokale Ollama API mit dem Bild und der Frage.

    Args:
        base64_image (str): Das Base64-kodierte Bild.
        user_question (str): Die vom Benutzer gestellte Frage.

    Returns:
        str: Die Text-Antwort vom Ollama-Modell.
    """
    headers = {
        "Content-Type": "application/json",
    }

    # Die Datenstruktur (Payload) für die Ollama API
    payload = {
        "model": MODEL_NAME,
        "prompt": user_question,
        "images": [base64_image],
        "stream": False,  # Wir möchten die komplette Antwort auf einmal erhalten
    }

    try:
        # Sende die Anfrage an den Ollama-Server
        response = requests.post(
            OLLAMA_API_URL, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()  # Löst einen Fehler aus, wenn die Antwort einen HTTP-Fehlerstatus hat

        # Die Antwort von Ollama ist ein JSON-String, wir extrahieren das 'response'-Feld
        response_data = response.json()
        return response_data.get(
            "response", "Keine Antwort im 'response'-Feld gefunden."
        )

    except requests.exceptions.RequestException as e:
        # Fehlerbehandlung bei Verbindungsproblemen (z.B. Ollama läuft nicht)
        error_message = (
            f"Fehler bei der API-Anfrage. Läuft der Ollama-Server? Details: {e}"
        )
        print(error_message)
        return error_message
    except json.JSONDecodeError:
        # Fehlerbehandlung für ungültige JSON-Antworten
        error_message = "Fehler: Die Antwort der API war kein gültiges JSON."
        print(error_message)
        return error_message


def process_interaction(image, question, chat_history):
    """
    Diese Funktion wird von der Gradio-Oberfläche aufgerufen, wenn der Benutzer auf "Senden" klickt.
    Sie orchestriert den gesamten Prozess von der Bildverarbeitung bis zur Anzeige der Antwort.

    Args:
        image (numpy.ndarray): Das Bild, das vom Gradio-Image-Komponente kommt.
        question (str): Die Frage aus dem Gradio-Textbox-Komponente.
        chat_history (list): Die bisherige Konversation.

    Returns:
        tuple: Ein Tupel mit dem aktualisierten Chat-Verlauf und einem leeren String für das Textfeld.
    """
    # Prüfen, ob eine Frage gestellt wurde
    if not question.strip():
        chat_history.append((None, "Bitte stelle eine Frage zum Bild."))
        return chat_history, ""

    # Prüfen, ob ein Bild hochgeladen wurde
    if image is None:
        chat_history.append((question, "Fehler: Bitte lade zuerst ein Bild hoch."))
        return chat_history, ""

    # Gib dem Benutzer sofortiges Feedback im Chat
    chat_history.append((question, "🧠 Analysiere das Bild und denke nach..."))
    yield chat_history, ""  # "yield" aktualisiert die UI sofort

    # Verarbeitung
    image_pil = Image.fromarray(image)
    base64_image = image_to_base64(image_pil)
    api_response = call_ollama_api(base64_image, question)

    # Entferne die "denke nach..." Nachricht und füge die echte Antwort hinzu
    chat_history.pop()
    chat_history.append((question, api_response))

    # Gib den finalen Chat-Verlauf zurück und leere das Eingabefeld
    yield chat_history, ""


# --- 4. Gradio UI-Aufbau ---
with gr.Blocks(theme=gr.themes.Soft(), title="Qwen Bild-Analyse") as demo:
    # Titel und Anleitung für den Benutzer
    gr.Markdown(
        """
        # 🖼️ Interaktiver Bild-Analyse-Chat mit Ollama
        
        Willkommen! Dieses Interface ermöglicht es dir, mit einem KI-Modell über den Inhalt von Bildern zu chatten.
        
        **Anleitung:**
        1.  **Bild hochladen:** Ziehe ein Bild in die linke Box oder klicke darauf, um eines auszuwählen.
        2.  **Frage stellen:** Gib deine Frage zum Bild in das Textfeld unten ein.
        3.  **Senden:** Klicke auf "Senden" und warte auf die Antwort der KI im Chatfenster rechts.
        """
    )

    with gr.Row(variant="panel"):
        # Linke Spalte für den Bildupload
        with gr.Column(scale=1):
            image_input = gr.Image(type="numpy", label="Dein Bild")
            gr.Markdown(
                "**Beispiele für Fragen:**\n- Beschreibe das Bild im Detail.\n- Was für ein Tier ist das?\n- Welche Farbe hat das Auto?"
            )

        # Rechte Spalte für den Chat
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Chat-Verlauf",
                bubble_full_width=False,
                height=500,
                avatar_images=("👤", "🤖"),  # Benutzer- und Bot-Avatare
            )

    # Untere Reihe für die Texteingabe und den Senden-Button
    with gr.Row():
        question_input = gr.Textbox(
            label="Stelle eine Frage",
            placeholder="z.B. Was ist das Hauptobjekt auf diesem Bild?",
            scale=4,  # Macht das Textfeld breiter
        )
        submit_button = gr.Button("Senden", variant="primary")

    # Event-Handler: Definiert, was passiert, wenn auf den Button geklickt wird
    submit_button.click(
        fn=process_interaction,
        inputs=[image_input, question_input, chatbot],
        outputs=[chatbot, question_input],
    )

    # Event-Handler für das Senden per Enter-Taste im Textfeld
    question_input.submit(
        fn=process_interaction,
        inputs=[image_input, question_input, chatbot],
        outputs=[chatbot, question_input],
    )


# --- 5. Start der Anwendung ---
if __name__ == "__main__":
    # Startet die Gradio Web-App
    demo.launch()
