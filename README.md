# StudySpark

## Überblick
StudySpark ist ein adaptiver Lernassistent, der sich an das individuelle Lerntempo der Nutzer anpasst und interaktives Lernen durch verschiedene Fragetypen und sofortiges Feedback ermöglicht. Die Anwendung basiert auf der Bloom-Taxonomie und passt die Schwierigkeit der Fragen automatisch an den Lernfortschritt an.

## Funktionen
- **Adaptive Lernumgebung**: Passt sich automatisch an das Niveau des Lernenden an
- **Verschiedene Fragetypen**: Single-Choice, Multiple-Choice, Sortierung und offene Fragen
- **Sofortiges Feedback**: Detaillierte Rückmeldungen zu Antworten mit Erklärungen
- **Nachfrage-Funktion**: Möglichkeit, Fragen zum erhaltenen Feedback zu stellen
- **Fortschrittsverfolgung**: Visualisierung des Lernfortschritts mit Level-System
- **Leaderboard**: Vergleich mit anderen Lernenden

## Technische Architektur
Das Projekt ist in Python implementiert und nutzt folgende Hauptkomponenten:

### Frontend
- **Streamlit**: Webbasierte Benutzeroberfläche
- **Konsolenfrontend**: Alternative Textschnittstelle für die Nutzung ohne Browser

### Backend
- **LangChain**: Framework für die Verarbeitung natürlicher Sprache
- **OpenAI API**: Generierung von Fragen, Bewertung von Antworten und Feedback
- **SQLite**: Lokale Datenbank zur Speicherung des Lernfortschritts
- **FAISS**: Vektordatenbank für effiziente Inhaltssuche
