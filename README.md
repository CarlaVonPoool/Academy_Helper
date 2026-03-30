# 📚 Poool Academy Helper

Ein intelligenter RAG-basierter Chat-Assistent für die Poool Academy Dokumentation.

## 🚀 Features

- **Intelligenter Chat**: Beantwortet Fragen basierend auf der kompletten Poool Academy
- **RAG-System**: Retrieval-Augmented Generation für präzise Antworten
- **347 Dokumente**: Vollständige Academy-Dokumentation indexiert
- **N8N Integration**: Automatisches Feedback-Logging für kontinuierliche Verbesserung
- **Modular**: Saubere Architektur, bereit für Integration in consulting-helper
- **Caching**: Intelligentes Embedding-Caching für bessere Performance

## 🛠️ Installation

1. **Repository klonen:**
```bash
git clone <repository-url>
cd Academy_Helper
```

2. **Virtual Environment erstellen:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

4. **Environment-Variablen konfigurieren:**
```bash
cp .env.example .env
# .env bearbeiten und API-Keys eintragen
```

## 🔑 Erforderliche API-Keys

- **ANTHROPIC_API_KEY**: Für Claude AI Integration
- **N8N_WEBHOOK_URL**: Für Feedback-Logging (optional)

## 🚀 Verwendung

```bash
streamlit run app.py
```

Die App läuft dann auf `http://localhost:8501`

## 📁 Struktur

```
Academy_Helper/
├── app.py                    # Haupt-App mit Navigation
├── sites/
│   ├── home.py              # Übersichtsseite
│   └── academy_chat.py      # RAG-Chat Interface
├── src/
│   ├── components/          # UI-Komponenten
│   │   ├── common/          # Gemeinsame Komponenten (Sidebar)
│   │   └── academy_chat/    # Chat-spezifische UI
│   └── helpers/             # Core-Logik
│       └── academy/         # RAG-System
│           ├── document_processing.py  # Embedding & Caching
│           └── search_and_qa.py       # Suche & Antwortgenerierung
├── documents/               # Academy-Dokumentation (347 .md Dateien)
├── n8n_webhook_logger.py    # N8N Feedback-Integration
└── requirements.txt         # Python-Dependencies
```

## 🎯 Hauptfunktionen

### 📚 Academy Chat
- Intelligente Beantwortung von Fragen zur Poool Software
- Automatische Quellenangaben
- Kontext-bewusste Antworten
- Feedback-System für kontinuierliche Verbesserung

### 🧠 RAG-System
- Sentence Transformers für Embedding-Generierung
- Cosine Similarity für relevante Dokumenten-Suche  
- Claude Sonnet für natürliche Antwortgenerierung
- Intelligentes Caching für bessere Performance

### 📊 Analytics & Feedback
- N8N Integration für Feedback-Sammlung
- Interaktions-Logging
- Performance-Tracking
- Kontinuierliche Verbesserung

## 🔧 Konfiguration

### Embedding-Cache
Das System erstellt automatisch einen Cache der Dokument-Embeddings:
- Pfad: `./embeddings_store/`
- Automatische Erkennung von Dokumentänderungen
- Manuelles Cache-Management über die UI

### N8N Integration
Optional für Feedback-Sammlung und Analytics:
```env
N8N_WEBHOOK_URL=http://your-n8n-instance.com/webhook/feedback
```

## 🚀 Deployment

### Streamlit Cloud
1. Repository zu GitHub pushen
2. Streamlit Cloud Account erstellen
3. App verbinden und deployen
4. Environment-Variablen in den Settings konfigurieren

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

## 🤝 Integration mit consulting-helper

Das Academy Helper System wurde so entwickelt, dass es nahtlos in das consulting-helper System integriert werden kann:

- Gleiche Architektur-Patterns
- Kompatible Sidebar-Komponenten  
- Modulare Struktur
- Einheitliches Styling

## 📝 Development

### Code-Struktur
- **Modular**: Klare Trennung zwischen UI und Logik
- **Erweiterbar**: Einfach neue Academy-Tools hinzufügbar
- **Testbar**: Isolierte Komponenten für Unit-Tests
- **Dokumentiert**: Ausführliche Code-Dokumentation

### Neue Features hinzufügen
1. UI-Komponente in `src/components/` erstellen
2. Business-Logik in `src/helpers/` implementieren
3. Route in `sites/` hinzufügen
4. Navigation in `app.py` erweitern

## 📄 Lizenz

[Lizenz-Information hier einfügen]

## 🐛 Support

Bei Fragen oder Problemen:
- Issues im GitHub Repository erstellen
- E-Mail: [fabian.kainz@poool.cc](mailto:fabian.kainz@poool.cc)