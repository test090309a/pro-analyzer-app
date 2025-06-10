# -*- coding: utf-8 -*-

"""
PRO ANALYZER v2.0
Ein fortschrittliches Analyse-Tool für visuelle Daten mit direktem Draht
zu einem lokalen Ollama Vision-Modell.

Features:
- Professionelles Dark-Theme mit Gradienten und moderner Typografie.
- 3-Spalten-Layout für maximale Übersichtlichkeit.
- "Quick Actions" für standardisierte, hochwertige Analysen.
- Integrierte "Profi-Tipps" zur Nutzerführung.
"""

# --- 1. Importe ---
import gradio as gr
import requests
import base64
from PIL import Image
import io
import json

# --- 2. Konfiguration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:7b"

# --- 3. CSS für das "FETZIGE" Design ---
# Hier definieren wir das komplette Aussehen der App.
css = """
/* Import der Google Font 'Poppins' */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

/* Allgemeines Styling & Dark Theme */
body, .gradio-container {
    font-family: 'Poppins', sans-serif;
    background-color: #1A1A1A; /* Dunkler Hintergrund */
    color: #E0E0E0; /* Heller Text */
    font-size: 18px; /* Alles wird riesig! */
}

/* Die Gradienten-Headline */
#app-title {
    font-size: 48px !important;
    font-weight: 700 !important;
    background: linear-gradient(90deg, #FF8C00, #FFD700); /* Knalliger Gradient */
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    padding: 10px 0;
}

/* Styling der Buttons */
.gradio-button {
    font-size: 16px !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    border: 2px solid #FF8C00 !important;
    background: transparent !important;
    color: #FF8C00 !important;
    transition: all 0.2s ease-in-out;
}
.gradio-button:hover {
    background: #FF8C00 !important;
    color: #1A1A1A !important;
    box-shadow: 0 0 15px #FF8C00;
}
.gradio-button.primary {
    background: #FF8C00 !important;
    color: #1A1A1A !important;
}

/* Block-Styling für einen modernen Look */
.gradio-panel, .gradio-row, .gradio-group {
    border: 1px solid #333 !important;
    border-radius: 16px !important;
    background-color: #242424 !important; /* Etwas hellerer Block-Hintergrund */
    padding: 20px !important;
}

/* Styling für Textfelder und Chat */
.gradio-textbox, .gradio-chatbot {
    border-radius: 8px !important;
    border: 1px solid #444 !important;
    background-color: #2F2F2F !important;
}
.gradio-chatbot .message {
    border-radius: 12px !important;
    box-shadow: none !important;
}
.gradio-chatbot .user-message { background-color: #3a3a3a !important; }
.gradio-chatbot .bot-message { background-color: #2c3e50 !important; }

/* Styling für den Akkordion-Bereich (Profi-Tipps) */
.gradio-accordion {
    border-radius: 12px !important;
    background-color: #2F2F2F !important;
    border: none !important;
}
"""

# --- 4. Kernlogik (unverändert zur v1, aber besser dokumentiert) ---


def image_to_base64(image_pil: Image.Image) -> str:
    buffered = io.BytesIO()
    image_pil.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def call_ollama_api(base64_image: str, user_question: str):
    payload = {
        "model": MODEL_NAME,
        "prompt": user_question,
        "images": [base64_image],
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get(
            "response", "Fehler: 'response'-Feld in API-Antwort nicht gefunden."
        )
    except requests.exceptions.RequestException as e:
        return f"Kommunikationsfehler mit Ollama. Ist der Server aktiv? Details: {e}"
    except json.JSONDecodeError:
        return "Fehler: Ungültige JSON-Antwort von der API erhalten."


def create_interaction(image, question, chat_history):
    # Validierung: Bild muss vorhanden sein
    if image is None:
        chat_history.append(
            (None, "⚠️ Bitte zuerst ein Bild in die linke Spalte hochladen!")
        )
        return chat_history, gr.update(interactive=True)

    # Validierung: Frage darf nicht leer sein
    if not question.strip():
        chat_history.append(
            (None, "⚠️ Bitte eine Frage stellen oder eine Quick Action verwenden.")
        )
        return chat_history, gr.update(interactive=True)

    # UI für den Benutzer sperren und Feedback geben
    yield chat_history + [(question, "🧠 Analysiere... Bitte warten.")], gr.update(
        interactive=False
    ), gr.update(interactive=False)

    # Verarbeitung
    image_pil = Image.fromarray(image)
    base64_image = image_to_base64(image_pil)
    api_response = call_ollama_api(base64_image, question)

    # Ergebnis anzeigen und UI wieder freigeben
    # Entfernt gezielt die "Analysiere..."-Nachricht, falls vorhanden
    if (
        len(chat_history) >= 1
        and chat_history[-1][1] == "🧠 Analysiere... Bitte warten."
    ):
        chat_history.pop(-1)
    elif (
        len(chat_history) >= 2
        and chat_history[-2][1] == "🧠 Analysiere... Bitte warten."
    ):
        chat_history.pop(-2)
    chat_history.append((question, api_response))

    yield chat_history, gr.update(interactive=True), gr.update(interactive=True)


# --- 5. Aufbau des Gradio Interfaces v2.0 ---

with gr.Blocks(css=css, theme=gr.themes.Base(), title="PRO ANALYZER v2.0") as demo:
    # 1. Titel
    gr.Markdown("# PRO ANALYZER v2.0", elem_id="app-title")

    # 2. Hauptlayout (3 Spalten)
    with gr.Row(equal_height=True):

        # LINKE SPALTE: Steuerung & Werkzeuge
        with gr.Column(scale=1, min_width=350):
            gr.Markdown("## 1. Steuerung")
            image_uploader = gr.Image(type="numpy", label="Bild hier hochladen")

            gr.Markdown("### ⚡ Quick Actions")
            gr.Markdown("Klicke, um eine vordefinierte Analyse zu starten.")

            # Vordefinierte Prompts für hohe Ergebnisqualität
            detailed_prompt = "Erstelle eine extrem detaillierte, tabellarische Beschreibung dieses Bildes. Gehe auf Hauptobjekte, Hintergrund, Lichtverhältnisse, Farben und Komposition ein."
            list_objects_prompt = "Liste alle erkennbaren Objekte, Personen und Tiere auf diesem Bild in einer nummerierten Liste auf."
            ocr_prompt = "Extrahiere allen sichtbaren Text aus diesem Bild. Gib nur den extrahierten Text zurück. Wenn kein Text vorhanden ist, schreibe 'Kein Text gefunden'."
            quality_prompt = "Bewerte die technische Qualität dieses Bildes auf einer Skala von 1-10. Begründe deine Bewertung anhand von Schärfe, Belichtung, Bildrauschen und Komposition."

            # Quick Action Buttons
            btn_detail = gr.Button("Detaillierte Beschreibung")
            btn_list = gr.Button("Objekte auflisten")
            btn_ocr = gr.Button("Text extrahieren (OCR)")
            btn_quality = gr.Button("Qualität bewerten")

        # MITTLERE SPALTE: Bild-Vorschau
        with gr.Column(scale=2, min_width=500):
            gr.Markdown("## 2. Bild-Vorschau")
            image_display = gr.Image(
                label="Aktuelles Bild", interactive=False, height=600
            )

        # RECHTE SPALTE: Analyse-Chat
        with gr.Column(scale=2, min_width=500):
            gr.Markdown("## 3. Analyse-Chat")
            chatbot = gr.Chatbot(
                label="Protokoll",
                height=600,
                bubble_full_width=False,
                avatar_images=("👤", "🤖"),
            )

    # 3. Untere Leiste für manuelle Eingabe
    with gr.Row():
        question_input = gr.Textbox(
            label="Eigene Frage oder Anweisung",
            placeholder="Stelle hier eine spezifische Frage oder verfeinere die Analyse...",
            scale=4,
        )
        submit_button = gr.Button("Analyse starten", variant="primary", scale=1)

    # 4. Profi-Tipps Sektion
    with gr.Accordion(
        "💡 Profi-Tipps für bessere Ergebnisse (hier klicken zum Öffnen)", open=False
    ):
        gr.Markdown(
            """
            - **Sei spezifisch:** Statt "Was ist das?" frage "Welche Pflanzenart ist im Vordergrund zu sehen?".
            - **Gib Kontext:** "Dieses Bild stammt aus einem Sicherheitsbericht. Gibt es darauf Anomalien?" funktioniert besser als eine allgemeine Frage.
            - **Fordere ein Format an:** Du kannst die KI bitten, die Antwort als Tabelle, Liste oder JSON auszugeben.
            - **Kombiniere Analysen:** Nutze eine Quick Action und stelle danach eine verfeinernde Frage im Textfeld.
            """
        )

    # --- 6. Event-Handler (Verknüpfung der Logik mit der UI) ---

    # Bild-Upload aktualisiert die Vorschau in der Mitte
    image_uploader.upload(lambda img: img, inputs=image_uploader, outputs=image_display)

    # Manuelle Eingabe per Button oder Enter-Taste
    submit_button.click(
        fn=create_interaction,
        inputs=[image_uploader, question_input, chatbot],
        outputs=[chatbot, question_input, submit_button],
    )
    question_input.submit(
        fn=create_interaction,
        inputs=[image_uploader, question_input, chatbot],
        outputs=[chatbot, question_input, submit_button],
    )

    # Quick Actions
    btn_detail.click(
        fn=create_interaction,
        inputs=[image_uploader, gr.State(detailed_prompt), chatbot],
        outputs=[chatbot, question_input, submit_button],
    )
    btn_list.click(
        fn=create_interaction,
        inputs=[image_uploader, gr.State(list_objects_prompt), chatbot],
        outputs=[chatbot, question_input, submit_button],
    )
    btn_ocr.click(
        fn=create_interaction,
        inputs=[image_uploader, gr.State(ocr_prompt), chatbot],
        outputs=[chatbot, question_input, submit_button],
    )
    btn_quality.click(
        fn=create_interaction,
        inputs=[image_uploader, gr.State(quality_prompt), chatbot],
        outputs=[chatbot, question_input, submit_button],
    )

# --- 7. Start ---
if __name__ == "__main__":
    demo.launch()
