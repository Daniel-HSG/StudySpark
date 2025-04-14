"""
Models-Modul für StudySpark
Enthält Datenmodelle und Bloom-Taxonomie-Definitionen
"""
import sqlite3
import random

# Bloom-Taxonomie-Stufen
BLOOM_LEVELS = {
    1: "Erinnern - Fakten abrufen, wiedergeben, erkennen",
    2: "Verstehen - Ideen oder Konzepte erklären",
    3: "Anwenden - Informationen in neuen Situationen nutzen",
    4: "Analysieren - Verbindungen zwischen Ideen herstellen",
    5: "Bewerten - Standpunkte rechtfertigen, beurteilen",
    6: "Erschaffen - Neues kreieren, entwickeln"
}

# Fragetypen mit Gewichtungen
QUESTION_TYPES = {
    "single_choice": {"name": "Single-Choice", "weight": 0.5},
    "multiple_choice": {"name": "Multiple-Choice", "weight": 0.5},
    "open_answer": {"name": "Offene Frage", "weight": 0.0},
    "sorting": {"name": "Sortierung", "weight": 0.0}
}

def select_question_type():
    """Wählt einen Fragetyp basierend auf Gewichtungen aus"""
    weights = [QUESTION_TYPES[qt]["weight"] for qt in QUESTION_TYPES]
    return random.choices(list(QUESTION_TYPES.keys()), weights=weights)[0]

def get_level_description(level):
    """Gibt die Beschreibung für eine Bloom-Stufe zurück"""
    return BLOOM_LEVELS.get(level, "Unbekannte Stufe")

# Datenbankfunktionen
def init_db():
    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            student_id TEXT PRIMARY KEY,
            module TEXT,
            topic TEXT,
            level INTEGER,
            progress INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_progress(student_id):
    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM progress WHERE student_id = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_progress(student_id, module, topic, level, progress):
    """Aktualisiert den Lernfortschritt eines Studierenden."""
    # Stelle sicher, dass der Fortschritt im gültigen Bereich bleibt
    progress = max(0, min(100, progress))
    
    # Überprüfe, ob ein Level-Wechsel erforderlich ist
    if progress >= 100:
        # Level erhöhen, wenn Fortschritt 100% erreicht
        level += 1
        if level > 6:  # Wenn höchstes Bloom-Level erreicht, beginne wieder bei 1
            level = 1
        progress = 0
    elif progress < 0:
        # Level verringern, wenn Fortschritt unter 0% fällt
        level -= 1
        if level < 1:  # Wenn niedrigstes Bloom-Level unterschritten, bleibe bei 1
            level = 1
        progress = 90  # Setze Fortschritt auf 90% des vorherigen Levels
    
    # Aktualisiere die Datenbank
    conn = sqlite3.connect("learning_progress.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO progress (student_id, module, topic, level, progress)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
        module = excluded.module,
        topic = excluded.topic,
        level = excluded.level,
        progress = excluded.progress
    """, (student_id, module, topic, level, progress))
    conn.commit()
    conn.close()
    
    return level, progress
