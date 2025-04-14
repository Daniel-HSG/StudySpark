# Prompts für die Fragengenerierung
QUESTION_PROMPTS = {
    "multiple_choice": """
    Erstelle eine Multiple-Choice-Frage auf Bloom-Stufe {level} ({level_description}) 
    zum folgenden Inhalt:
    
    {content}
    
    Formatiere die Ausgabe GENAU wie folgt:
    FRAGE: [Deine Frage hier]
    
    ANTWORTMÖGLICHKEITEN:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    
    RICHTIGE ANTWORTEN: [z.B. A, C]
    
    ERKLÄRUNG: [Eine kurze, präzise Erklärung (2-3 Sätze), warum diese Antworten richtig sind]
    """,
    
    "single_choice": """
    Erstelle eine Single-Choice-Frage auf Bloom-Stufe {level} ({level_description}) 
    zum folgenden Inhalt:
    
    {content}
    
    Formatiere die Ausgabe GENAU wie folgt:
    FRAGE: [Deine Frage hier]
    
    ANTWORTMÖGLICHKEITEN:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    
    RICHTIGE ANTWORT: [z.B. B]
    
    ERKLÄRUNG: [Eine kurze, präzise Erklärung (2-3 Sätze), warum diese Antwort richtig ist]
    """,
    
    "sorting": """
    Erstelle eine Sortierungsfrage auf Bloom-Stufe {level} ({level_description}) 
    zum folgenden Inhalt:
    
    {content}
    
    Formatiere die Ausgabe GENAU wie folgt:
    FRAGE: [Deine Sortierungsanweisung]
    
    ELEMENTE:
    1. [Element 1]
    2. [Element 2]
    3. [Element 3]
    4. [Element 4]
    
    RICHTIGE REIHENFOLGE: [z.B. 3, 1, 4, 2]
    
    ERKLÄRUNG: [Eine kurze, präzise Erklärung (2-3 Sätze), warum diese Reihenfolge richtig ist]
    """,
    
    "open_answer": """
    Erstelle eine offene Frage auf Bloom-Stufe {level} ({level_description}) 
    zum folgenden Inhalt:
    
    {content}
    
    Formatiere die Ausgabe GENAU wie folgt:
    FRAGE: [Deine Frage hier]
    
    MUSTERANTWORT: [Eine beispielhafte korrekte Antwort]
    
    BEWERTUNGSKRITERIEN:
    - [Kriterium 1]
    - [Kriterium 2]
    - [Kriterium 3]
    """
}

# Prompt für das Feedback (nur für offene Fragen)
FEEDBACK_PROMPT = """
Bewerte die folgende Antwort auf eine offene Frage:

Frage: {question}

Musterantwort: {model_answer}

Bewertungskriterien:
{criteria}

Antwort des Studenten: {answer}

Gib deine Antwort in folgendem Format zurück:
PUNKTZAHL: [Eine Zahl zwischen 0 und 100]
FEEDBACK: [Ein präzises, konstruktives Feedback in 2-5 Sätzen, das auf die Stärken und Schwächen der Antwort eingeht und sich auf die Bewertungskriterien bezieht]
"""


# Prompt für Nachfragen
FOLLOWUP_PROMPT = """
Beantworte die folgende Nachfrage des Studenten kurz und präzise in 2-3 Sätzen.
Gehe direkt auf die Frage ein und liefere nur relevante Informationen.

{context}

Deine Antwort sollte klar, präzise und hilfreich sein.
"""
