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
from PIL import Image as PILImage
import io
import json
import sqlite3
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Preformatted,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

styles = getSampleStyleSheet()
code_style = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontName="Courier",
    fontSize=8,
    leftIndent=6,
    rightIndent=6,
    leading=10,
    wordWrap="CJK",
    spaceAfter=6,
    borderPadding=2,
    backColor="#222222",
    textColor="#FFD700",
)


import tempfile
import numpy as np
import socket


import subprocess
import time
import re


# --- NGROK öffentlicher Link ---
def start_ngrok(port=7860):
    # Starte ngrok als Hintergrundprozess
    ngrok = subprocess.Popen(
        # C:\ProgramData\chocolatey\bin
        ["C:\\ProgramData\\chocolatey\\bin\\ngrok.exe", "http", str(port)],
        # ["C:\\ngrok\\ngrok.exe", "http", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Warte kurz, bis ngrok gestartet ist
    time.sleep(2)
    # Hole die öffentliche URL von ngrok
    try:
        import requests

        url = None
        for _ in range(10):
            try:
                tunnel_info = requests.get("http://127.0.0.1:4040/api/tunnels").json()
                url = tunnel_info["tunnels"][0]["public_url"]
                break
            except Exception:
                time.sleep(1)
        if url:
            print(f"\n*** Deine App ist öffentlich erreichbar unter: {url} ***\n")
            print("Diesen Link kannst du teilen, solange dieses Fenster geöffnet ist.")
        else:
            print("ngrok gestartet, aber kein öffentlicher Link gefunden.")
    except Exception as e:
        print("ngrok gestartet, aber konnte keinen Link abrufen.", e)
    return ngrok


# --- 2. Konfiguration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:7b"
DB_PATH = "pro_analyzer_data.db"

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


def image_to_base64(image_pil: PILImage) -> str:
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
    # image_pil = Image.fromarray(image)
    image_pil = PILImage.fromarray(image)
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

    # --- Speicherung in SQLite ---
    save_interaction(
        prompt=question,
        response=api_response,
        image_pil=image_pil,
        model=MODEL_NAME,
        meta={
            "chat_history": chat_history[:-1]
        },  # Verlauf bis vor die aktuelle Antwort
    )

    yield chat_history, gr.update(interactive=True), gr.update(interactive=True)


# --- 0. Service-Check & Modell-Info ---
def check_ollama_service():
    """Prüft, ob der Ollama-Service erreichbar ist und gibt ggf. eine Fehlermeldung zurück."""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": "ping",
                "images": [],
                "stream": False,
            },
            timeout=5,
        )
        if response.status_code == 200:
            return True, None
        else:
            return (
                False,
                f"Ollama-Service antwortet nicht korrekt (Status {response.status_code})",
            )
    except Exception as e:
        return False, f"Ollama-Service nicht erreichbar: {e}"


# --- 0a. SQLite-Setup ---
def init_db():
    """Initialisiert die SQLite-Datenbank und legt die Tabelle an, falls nicht vorhanden."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            prompt TEXT,
            response TEXT,
            image BLOB,
            model TEXT,
            meta TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


def save_interaction(prompt, response, image_pil, model, meta=None):
    """Speichert eine Interaktion (Prompt, Antwort, Bild, Modell, Metadaten) in der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Bild als JPEG-Bytes speichern
    img_bytes = None
    if image_pil is not None:
        buf = io.BytesIO()
        image_pil.save(buf, format="JPEG")
        img_bytes = buf.getvalue()
    c.execute(
        "INSERT INTO interactions (timestamp, prompt, response, image, model, meta) VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.now().isoformat(),
            prompt,
            response,
            img_bytes,
            model,
            json.dumps(meta) if meta else None,
        ),
    )
    conn.commit()
    conn.close()


import tempfile
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_report(chat_history, file_name="pro_analyzer_report.pdf"):
    """
    Erstellt einen PDF-Report aus dem Chatverlauf (inkl. Bilder, Prompts, Antworten, Zeitstempel, Rechnername, IP, Dauer) und gibt den Dateipfad zurück.
    """
    styles = getSampleStyleSheet()
    # Eigener Style für Codeblöcke
    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leftIndent=6,
        rightIndent=6,
        leading=10,
        wordWrap="CJK",
        spaceAfter=6,
        borderPadding=2,
        backColor="#222222",
        textColor="#FFD700",
    )
    story = []
    # Rechnername und IP-Adresse
    hostname = socket.gethostname()
    try:
        ip_addr = socket.gethostbyname(hostname)
    except Exception:
        ip_addr = "unbekannt"
    story.append(Paragraph("<b>PRO ANALYZER Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    story.append(Paragraph(f"Erstellt am: {now}", styles["Normal"]))
    story.append(Paragraph(f"Modell: <b>{MODEL_NAME}</b>", styles["Normal"]))
    story.append(Paragraph(f"Rechnername: {hostname}", styles["Normal"]))
    story.append(Paragraph(f"IP-Adresse: {ip_addr}", styles["Normal"]))
    story.append(Spacer(1, 12))
    # --- Bilder und Dauer ---
    for idx, (prompt, response) in enumerate(chat_history):
        if prompt:
            story.append(
                Paragraph(f"<b>Frage/Prompt {idx+1}:</b> {prompt}", styles["Heading4"])
            )
        else:
            story.append(Paragraph(f"<b>System:</b>", styles["Heading4"]))
        story.append(Spacer(1, 4))
        # Dauer und Bild aus DB holen (falls vorhanden)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT timestamp, image, meta FROM interactions WHERE prompt=? ORDER BY id DESC LIMIT 1",
            (prompt,),
        )
        row = c.fetchone()
        conn.close()
        if row:
            timestamp, img_bytes, meta = row
            # Dauer berechnen, falls im meta enthalten
            dauer = None
            if meta:
                try:
                    meta_dict = json.loads(meta)
                    dauer = meta_dict.get("duration")
                except Exception:
                    dauer = None
            if dauer:
                story.append(
                    Paragraph(f"Antwortdauer: {dauer:.2f} Sekunden", styles["Normal"])
                )
            if img_bytes:
                img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                img_temp.write(img_bytes)
                img_temp.close()
                story.append(RLImage(img_temp.name, width=200, height=200))
                story.append(Spacer(1, 4))
        # Antwort: Codeblöcke als Preformatted, Rest als Paragraph
        if "```" in response:
            # Versuche, nur den Code als Preformatted zu nehmen, Rest als Paragraph
            import re

            code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", response, re.DOTALL)
            if code_blocks:
                # Text vor erstem Codeblock
                first_code = response.find("```")
                if first_code > 0:
                    story.append(
                        Paragraph(
                            f"<b>Antwort:</b> {response[:first_code]}",
                            styles["BodyText"],
                        )
                    )
                for code in code_blocks:
                    story.append(Preformatted(code, code_style))  # <--- eigener Style!
                # Text nach letztem Codeblock
                last_code = response.rfind("```")
                if last_code < len(response):
                    story.append(
                        Paragraph(response[last_code + 3 :], styles["BodyText"])
                    )
            else:
                # Kein Markdown-Codeblock, aber evtl. HTML: alles als Preformatted
                story.append(Preformatted(response, code_style))
        else:
            story.append(Paragraph(f"<b>Antwort:</b> {response}", styles["BodyText"]))
        story.append(Spacer(1, 8))
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp_pdf.name, pagesize=A4)
    doc.build(story)
    return tmp_pdf.name  # <--- Wichtig: Nur den Dateipfad als String zurückgeben!


# --- 5. Aufbau des Gradio Interfaces v2.0 ---

with gr.Blocks(css=css, theme=gr.themes.Base(), title="PRO ANALYZER v2.0") as demo:
    gr.Markdown(
        "**Hinweis:** Die App ist öffentlich erreichbar, solange dieses Fenster geöffnet ist. Den Link findest du in der Konsole."
    )

    # 0. Service-Check
    service_ok, service_error = check_ollama_service()
    if not service_ok:
        gr.Markdown(f"# ❌ Fehler: {service_error}", elem_id="app-title")
        gr.Markdown(
            "Bitte stelle sicher, dass Ollama läuft und das Modell geladen ist."
        )
        gr.Markdown(f"Verwendetes Modell: **{MODEL_NAME}**")
        gr.Markdown("Die App ist gesperrt, bis der Service verfügbar ist.")
    else:
        # 1. Titel & Modell-Info
        gr.Markdown("# PRO ANALYZER v2.0", elem_id="app-title")
        gr.Markdown(
            f"<div style='text-align:center;font-size:20px;'>Verwendetes Modell: <b>{MODEL_NAME}</b></div>",
            elem_id="model-info",
        )

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

                # --- Prompt-Assistent ---
                gr.Markdown("### 🤖 Prompt-Assistent")
                gr.Markdown(
                    """
                Nutze den Prompt-Assistenten, um strukturierte Prompts zu erstellen. Je klarer und strukturierter der Prompt – insbesondere bei multimodalen Aufgaben – desto besser und zuverlässiger sind die Ergebnisse. Gib das gewünschte Format (z.B. JSON, Tabelle, Liste) und eine präzise Aufgabenstellung an.
                """
                )
                prompt_format = gr.Dropdown(
                    ["Freitext", "Tabelle", "Liste", "JSON"],
                    value="Freitext",
                    label="Erwünschtes Antwortformat",
                )
                prompt_task = gr.Textbox(
                    label="Deine Aufgabenstellung",
                    placeholder="Beschreibe hier möglichst präzise, was analysiert werden soll...",
                )
                prompt_example = gr.Markdown(
                    "Beispiel: 'Analysiere die Bildkomposition und gib das Ergebnis als Tabelle mit den Spalten Objekt, Position, Farbe zurück.'"
                )

                def build_prompt(format, aufgabe):
                    if not aufgabe.strip():
                        return ""
                    if format == "Freitext":
                        return aufgabe
                    return f"{aufgabe} Gib das Ergebnis im Format: {format}."

                prompt_output = gr.Textbox(label="Fertiger Prompt", interactive=False)
                prompt_format.change(
                    build_prompt, [prompt_format, prompt_task], prompt_output
                )
                prompt_task.change(
                    build_prompt, [prompt_format, prompt_task], prompt_output
                )
                gr.Markdown(
                    "Du kannst den fertigen Prompt kopieren und unten einfügen oder weiter anpassen."
                )

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
                    elem_id="chatbot-area",
                )

        # 3. Untere Leiste für manuelle Eingabe
        with gr.Row():
            question_input = gr.Textbox(
                label="Eigene Frage oder Anweisung",
                placeholder="Stelle hier eine spezifische Frage oder verfeinere die Analyse...",
                scale=4,
                elem_id="main-question-input",
            )
            submit_button = gr.Button("Analyse starten", variant="primary", scale=1)

        # 4. Profi-Tipps Sektion
        with gr.Accordion(
            "💡 Profi-Tipps für bessere Ergebnisse (hier klicken zum Öffnen)",
            open=False,
        ):
            gr.Markdown(
                f"""
                - **Sei spezifisch:** Statt "Was ist das?" frage "Welche Pflanzenart ist im Vordergrund zu sehen?".
                - **Gib Kontext:** "Dieses Bild stammt aus einem Sicherheitsbericht. Gibt es darauf Anomalien?" funktioniert besser als eine allgemeine Frage.
                - **Fordere ein Format an:** Du kannst die KI bitten, die Antwort als Tabelle, Liste oder JSON auszugeben.
                - **Kombiniere Analysen:** Nutze eine Quick Action und stelle danach eine verfeinernde Frage im Textfeld.
                - **Modell-Tipp:** Je klarer und strukturierter der Prompt – insbesondere bei multimodalen Aufgaben – desto besser und zuverlässiger sind die Ergebnisse. Die explizite Angabe des gewünschten Formats (z.B. JSON) und eine präzise Aufgabenstellung sind für optimale Resultate entscheidend. (Modell: {MODEL_NAME})
                """
            )

        # --- 6. Event-Handler (Verknüpfung der Logik mit der UI) ---

        # Bild-Upload aktualisiert die Vorschau in der Mitte
        image_uploader.upload(
            lambda img: img, inputs=image_uploader, outputs=image_display
        )

        # Manuelle Eingabe per Button oder Enter-Taste
        def scroll_and_focus(chat, *args):
            # Gibt die Chat-Historie zurück, JS scrollt automatisch zum Ende
            return chat

        submit_button.click(
            fn=create_interaction,
            inputs=[image_uploader, question_input, chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )
        question_input.submit(
            fn=create_interaction,
            inputs=[image_uploader, question_input, chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )

        # Quick Actions
        btn_detail.click(
            fn=create_interaction,
            inputs=[image_uploader, gr.State(detailed_prompt), chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )
        btn_list.click(
            fn=create_interaction,
            inputs=[image_uploader, gr.State(list_objects_prompt), chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )
        btn_ocr.click(
            fn=create_interaction,
            inputs=[image_uploader, gr.State(ocr_prompt), chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )
        btn_quality.click(
            fn=create_interaction,
            inputs=[image_uploader, gr.State(quality_prompt), chatbot],
            outputs=[chatbot, question_input, submit_button],
            postprocess=scroll_and_focus,
        )

        # --- Report-Download Button ---
        def download_report(chat):
            pdf_path = generate_pdf_report(chat)
            return pdf_path  # Nur den Dateipfad als String zurückgeben!

        report_btn = gr.Button("Report als PDF herunterladen", variant="secondary")
        report_file = gr.File(label="PDF-Report", file_types=[".pdf"])
        report_btn.click(
            fn=download_report,
            inputs=[chatbot],
            outputs=[report_file],
        )

        # --- Automatisches Scrollen & Fokus per JS ---
        gr.HTML(
            """
        <script>
        function scrollChatToBottom() {
            const chat = document.querySelector('#chatbot-area .wrap, #chatbot-area .gradio-chatbot');
            if (chat) { chat.scrollTop = chat.scrollHeight; }
        }
        function focusInput() {
            const input = document.querySelector('#main-question-input textarea');
            if (input) { input.focus(); }
        }
        // Nach jedem Update scrollen und Fokus setzen
        new MutationObserver(() => { scrollChatToBottom(); focusInput(); }).observe(document.body, {childList:true,subtree:true});
        </script>
        """
        )

# --- 7. Start ---
if __name__ == "__main__":
    # NGROK starten und öffentlichen Link anzeigen
    ngrok_process = start_ngrok(port=7860)
    demo.launch()
    # demo.launch(share=True) # Der shared Link geht nicht.
