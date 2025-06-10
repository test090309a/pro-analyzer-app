# PRO ANALYZER v2.0

Ein modernes, KI-gestütztes Analyse-Tool für visuelle Daten mit direkter Anbindung an ein lokales Ollama Vision-Modell (z. B. qwen2.5vl:7b).

## Features
- **Professionelles Dark-Theme** mit moderner Typografie und 3-Spalten-Layout
- **Quick Actions** für sofortige, hochwertige Analysen (z. B. Objekterkennung, OCR, Qualitätsbewertung)
- **Interaktiver Prompt-Assistent** für strukturierte, effektive Prompts
- **Analyse-Chat**: Protokoll aller Fragen und Antworten, inkl. Bildvorschau
- **PDF-Report**: Exportiere den gesamten Chatverlauf inkl. Bilder, Antwortzeiten, Rechnername und IP als schön formatiertes PDF
- **Datenbank**: Alle Analysen werden in einer SQLite-Datenbank gespeichert
- **Service-Check**: Automatische Prüfung, ob Ollama läuft
- **Abbrechen-Funktion**: Möglichkeit, laufende Analysen zu stoppen (in Entwicklung)

## Voraussetzungen
- Python 3.9+
- [Ollama](https://ollama.com/) lokal installiert und Modell geladen (z. B. qwen2.5vl:7b)
- Abhängigkeiten aus `requirements.txt` (z. B. gradio, reportlab, pillow, numpy, requests)

## Starten der App
```powershell
python pro_analyzer_app.py
```
Die App läuft dann lokal unter http://127.0.0.1:7860

## Version mit ngrok (Remote-Zugriff)
Mit der Datei `pro_analyzer_app_ngrok.py` kannst du die App per [ngrok](https://ngrok.com/) sicher über das Internet zugänglich machen. Damit kannst du die Bildanalyse auch remote nutzen oder mit anderen teilen.

**Beispiel:**
```powershell
python pro_analyzer_app_ngrok.py
```
Die ngrok-URL wird im Terminal angezeigt.

## Hinweise
- Die SQLite-Datenbank (`pro_analyzer_data.db`) speichert alle Interaktionen inkl. Bilder, Prompts, Antworten und Metadaten.
- Die PDF-Exportfunktion ist besonders nützlich für Dokumentation, Berichte oder Nachweise.
- Für produktiven Einsatz empfiehlt sich ein sicheres Hosting und ggf. Authentifizierung.

## Lizenz
MIT License

---
**Made with ❤️ and Ollama Vision AI**
