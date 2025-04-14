"""
Services-Modul für StudySpark
Kombiniert Backend-Services, LLM-Chains und Vektorspeicher
"""
import os
import random
import re
import glob

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader

from config import OPENAI_API_KEY
from models import BLOOM_LEVELS, QUESTION_TYPES, get_progress, update_progress, select_question_type
from prompts import QUESTION_PROMPTS, FEEDBACK_PROMPT, FOLLOWUP_PROMPT

# LLM-Initialisierung
llm = ChatOpenAI(model="gpt-4-turbo", api_key=OPENAI_API_KEY)

# Chain-Funktionen
def create_question_chain():
    prompt = PromptTemplate(
        input_variables=["topic", "level"],
        template="""
        {topic}
        
        {level}
        
        Erstelle eine gut strukturierte Frage mit klaren Antwortmöglichkeiten.
        """
    )
    return LLMChain(llm=llm, prompt=prompt)

def create_feedback_chain():
    prompt = PromptTemplate(
        input_variables=["question", "model_answer", "criteria", "answer"],
        template=FEEDBACK_PROMPT
    )
    return LLMChain(llm=llm, prompt=prompt)


def create_followup_chain():
    prompt = PromptTemplate(
        input_variables=["context"],
        template="""
        {context}
        
        Beantworte die Nachfrage des Studenten kurz und präzise.
        Halte deine Antwort auf 2-3 Sätze begrenzt.
        """
    )
    return LLMChain(llm=llm, prompt=prompt)

# Vektorspeicher-Initialisierung
def initialize_vector_store():
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    # Stelle sicher, dass das resources-Verzeichnis existiert
    if not os.path.exists("resources"):
        os.makedirs("resources")
        # Gib einen leeren Vektorspeicher zurück, wenn noch keine Dokumente existieren
        return FAISS.from_texts(["Leeres Dokument"], embeddings)
    
    try:
        # Verwende PyPDFLoader für bessere Kompatibilität
        documents = []
        for filename in os.listdir("resources"):
            if filename.endswith(".pdf"):
                try:
                    loader = PyPDFLoader(os.path.join("resources", filename))
                    documents.extend(loader.load())
                except Exception:
                    pass
        
        if documents:
            # Extrahiere Text aus Dokumenten
            texts = [doc.page_content for doc in documents]
            metadata = [doc.metadata for doc in documents]
            
            # Erstelle FAISS-Index
            vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadata)
            return vector_store
        else:
            return FAISS.from_texts(["Leeres Dokument"], embeddings)
    except Exception:
        # Gib einen leeren Vektorspeicher im Fehlerfall zurück
        return FAISS.from_texts(["Leeres Dokument"], embeddings)

# Hauptserviceklasse
class LearningService:
    def __init__(self):
        """Initialisiert den Learning-Service"""
        # Datenbank initialisieren
        from models import init_db
        init_db()
        
        # LLM-Chains erstellen
        self.question_chain = create_question_chain()
        self.feedback_chain = create_feedback_chain()
        self.followup_chain = create_followup_chain()
        
        # Inhaltsspeicher
        self.content_chunks = []
        
        # Einfaches Caching
        self.fragen_cache = {}
        self.feedback_cache = {}
        
        # Fragen-Queue für vorgenerierte Fragen
        self.question_queue = {}  # Dictionary mit student_id als Schlüssel
        
        # Vektorspeicher initialisieren
        try:
            self.vector_store = initialize_vector_store()
        except Exception:
            self.vector_store = None
    
    def get_student_progress(self, student_id):
        """Ruft den aktuellen Fortschritt des Studenten ab"""
        progress = get_progress(student_id)
        if not progress:
            update_progress(student_id, "BWL", "Modul 1", 1, 0)
            progress = get_progress(student_id)
        
        return {
            "student_id": progress[0],
            "module": progress[1],
            "topic": progress[2],
            "level": progress[3],
            "progress": progress[4],
            "level_description": BLOOM_LEVELS[progress[3]]
        }
    
    def load_content(self):
        """Lädt Inhalte nur bei Bedarf"""
        if not self.content_chunks:
            try:
                with open(os.path.join("resources", "modul1.txt"), 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Teile den Inhalt in Chunks auf
                    paragraphs = content.split('\n\n')
                    current_chunk = ""
                    for para in paragraphs:
                        if len(current_chunk) + len(para) > 800:
                            self.content_chunks.append(current_chunk)
                            current_chunk = para
                        else:
                            current_chunk += "\n\n" + para if current_chunk else para
                    if current_chunk:
                        self.content_chunks.append(current_chunk)
            except Exception as e:
                print(f"Fehler beim Laden des Inhalts: {e}")
                # Füge einen Dummy-Inhalt hinzu, damit wir weitermachen können
                self.content_chunks = ["Dies ist ein Beispielinhalt für BWL Modul 1."]
    def generate_question(self, bloom_level, content, question_type):
        """Generiert eine Frage mit explizitem Format"""
        # Prompt aus der Prompts-Datei laden und formatieren
        prompt = QUESTION_PROMPTS[question_type].format(
            level=bloom_level,
            level_description=BLOOM_LEVELS[bloom_level],
            content=content
        )
        
        # Direkte Ausführung mit dem Chain-Objekt
        result = self.question_chain.run(
            topic=prompt, 
            level=f"Bloom-Level: {bloom_level} - {BLOOM_LEVELS[bloom_level]}"
        )
        
        return result.strip()
    
    def parse_question(self, question_text, question_type):
        """Verbessertes Parsen von Fragen mit klarer Extraktion der richtigen Antworten"""
        try:
            # Frage extrahieren
            question_match = re.search(r'(?:FRAGE|Frage):\s*(.*?)(?:\n\n|\n(?=ANTWORT|Option|ELEMENT|MUSTER)|$)',
                                     question_text, re.DOTALL | re.IGNORECASE)
            
            question = question_match.group(1).strip() if question_match else "Frage nicht gefunden"
            
            # Gemeinsames Ergebnis-Dictionary für alle Fragetypen
            result = {
                "question": question,
                "correct_answer_info": "",  # Wird für die sofortige Anzeige der richtigen Antwort verwendet
                "explanation": ""           # Neue Eigenschaft für die Erklärung
            }
            
            # Erklärung extrahieren (für alle Fragetypen außer open_answer)
            if question_type != "open_answer":
                explanation_match = re.search(r'(?:ERKLÄRUNG|Erklärung):\s*(.*?)(?:\n\n|$)',
                                             question_text, re.DOTALL | re.IGNORECASE)
                explanation = explanation_match.group(1).strip() if explanation_match else ""
                result["explanation"] = explanation
            
            if question_type in ["multiple_choice", "single_choice"]:
                # Optionen-Block extrahieren
                options_block_match = re.search(r'(?:ANTWORTMÖGLICHKEITEN|Antwortmöglichkeiten):(.*?)(?:RICHTIGE ANTWORT|Richtige Antwort|RICHTIGE ANTWORTEN|Richtige Antworten)',
                                             question_text, re.DOTALL | re.IGNORECASE)
                
                options_block = options_block_match.group(1).strip() if options_block_match else ""
                
                # Optionen aus dem Block extrahieren
                options = {}
                for line in options_block.split('\n'):
                    option_match = re.match(r'([A-D])[\.|\)]?\s*(.*?)$', line.strip())
                    if option_match:
                        key = option_match.group(1)
                        value = option_match.group(2).strip()
                        options[key] = value
                
                # Richtige Antworten extrahieren
                correct_pattern = r'(?:RICHTIGE ANTWORT|Richtige Antwort)[:\s]*(.*?)(?:\n\n|\n(?=ERKLÄRUNG|Erklärung)|$)'
                if question_type == "multiple_choice":
                    correct_pattern = r'(?:RICHTIGE ANTWORTEN|Richtige Antworten)[:\s]*(.*?)(?:\n\n|\n(?=ERKLÄRUNG|Erklärung)|$)'
                
                correct_match = re.search(correct_pattern, question_text, re.DOTALL | re.IGNORECASE)
                correct = correct_match.group(1).strip() if correct_match else ""
                
                # Formatierung der richtigen Antworten für die Anzeige
                if question_type == "multiple_choice":
                    correct_answers = [ans.strip() for ans in correct.split(',')]
                    correct_answer_text = ", ".join(correct_answers)
                    result["correct_answer_info"] = f"Richtige Antworten: {correct_answer_text}"
                else:  # single_choice
                    result["correct_answer_info"] = f"Richtige Antwort: {correct}"
                
                result["options"] = options
                result["correct_answers"] = [ans.strip() for ans in correct.split(',')] if question_type == "multiple_choice" else correct.strip()
            
            elif question_type == "sorting":
                # Elemente extrahieren
                elements_block_match = re.search(r'(?:ELEMENTE|Elemente):(.*?)(?:RICHTIGE REIHENFOLGE|Richtige Reihenfolge)',
                                             question_text, re.DOTALL | re.IGNORECASE)
                elements_block = elements_block_match.group(1).strip() if elements_block_match else ""
                
                elements = {}
                for line in elements_block.split('\n'):
                    elem_match = re.match(r'(\d+)[\.|\)]?\s*(.*?)$', line.strip())
                    if elem_match:
                        elements[elem_match.group(1)] = elem_match.group(2).strip()
                
                # Richtige Reihenfolge extrahieren
                order_match = re.search(r'(?:RICHTIGE REIHENFOLGE|Richtige Reihenfolge)[:\s]*(.*?)(?:\n\n|\n(?=ERKLÄRUNG|Erklärung)|$)',
                                     question_text, re.DOTALL | re.IGNORECASE)
                correct_order = [o.strip() for o in order_match.group(1).split(',')] if order_match else []
                
                # Formatierung der richtigen Antwort für die Anzeige
                result["elements"] = elements
                result["correct_order"] = correct_order
                result["correct_answer_info"] = f"Richtige Reihenfolge: {', '.join(correct_order)}"
            
            else:  # open_answer
                # Musterantwort extrahieren
                answer_match = re.search(r'(?:MUSTERANTWORT|Musterantwort)[:\s]*(.*?)(?:\n\n|\n(?=BEWERTUNG|Bewertung)|$)',
                                         question_text, re.DOTALL | re.IGNORECASE)
                answer = answer_match.group(1).strip() if answer_match else "Keine Musterantwort verfügbar"
                
                # Kriterien extrahieren
                criteria_match = re.search(r'(?:BEWERTUNGSKRITERIEN|Bewertungskriterien)[:\s]*(.*?)$',
                                         question_text, re.DOTALL | re.IGNORECASE)
                criteria_text = criteria_match.group(1).strip() if criteria_match else ""
                
                criteria = []
                for criterion in re.finditer(r'[-\*]\s*(.*?)(?=\n[-\*]|\n\n|$)', criteria_text, re.DOTALL):
                    criteria.append(criterion.group(1).strip())
                
                # Formatierung der Musterantwort für die Anzeige (auf max. 5 Sätze gekürzt)
                sentences = re.split(r'(?<=[.!?])\s+', answer)
                short_answer = ' '.join(sentences[:5])
                
                result["model_answer"] = answer
                result["criteria"] = criteria
                result["correct_answer_info"] = f"Musterantwort: {short_answer}"
                # Für offene Fragen verwenden wir die Musterantwort als Erklärung
                result["explanation"] = answer
            
            return result
            
        except Exception as e:
            print(f"Fehler beim Parsen der Frage: {e}")
            return {"error": f"Fehler beim Parsen der Frage: {e}", "raw": question_text}
    
    def pregenerate_question(self, student_id):
        """Generiert eine Frage im Voraus und speichert sie in der Queue"""
        # Inhalte laden
        self.load_content()
        
        # Studentenfortschritt abrufen
        progress = self.get_student_progress(student_id)
        bloom_level = progress["level"]
        
        # Fragetyp und Inhalt auswählen
        question_type = select_question_type()
        content_chunk = random.choice(self.content_chunks)
        
        # Frage generieren
        try:
            question_text = self.generate_question(bloom_level, content_chunk, question_type)
            
            # Frage parsen
            parsed_question = self.parse_question(question_text, question_type)
            
            # Frage mit Metadaten in der Queue speichern
            question_data = {
                "question": parsed_question,
                "question_type": question_type,
                "bloom_level": bloom_level,
                "raw_question": question_text
            }
            
            # In der Queue speichern
            if student_id not in self.question_queue:
                self.question_queue[student_id] = []
                
            self.question_queue[student_id].append(question_data)
            
            return True
        except Exception as e:
            print(f"Fehler bei der Vorgenerierung einer Frage: {e}")
            return False
    
    def get_next_question(self, student_id):
        """Holt die nächste Frage aus der Queue oder generiert eine neue"""
        # Prüfen, ob eine vorgenerierte Frage verfügbar ist
        if student_id in self.question_queue and self.question_queue[student_id]:
            # Vorgenerierte Frage aus der Queue holen
            question_data = self.question_queue[student_id].pop(0)
            
            # Sofort eine neue Frage vorgenerieren (asynchron wäre noch besser)
            self.pregenerate_question(student_id)
            
            return question_data
        else:
            # Keine vorgenerierte Frage verfügbar, direkt generieren
            return self.generate_next_question(student_id)
        
    def generate_next_question(self, student_id):
        """Generiert die nächste Frage basierend auf dem Level des Studenten"""
        # Inhalte laden
        self.load_content()
        
        # Studentenfortschritt abrufen
        progress = self.get_student_progress(student_id)
        bloom_level = progress["level"]
        
        # Fragetyp und Inhalt auswählen
        question_type = select_question_type()
        content_chunk = random.choice(self.content_chunks)
        
        # Frage generieren
        question_text = self.generate_question(bloom_level, content_chunk, question_type)
        
        # Frage parsen
        parsed_question = self.parse_question(question_text, question_type)
        
        # Frage mit Metadaten zurückgeben
        return {
            "question": parsed_question,
            "question_type": question_type,
            "bloom_level": bloom_level,
            "raw_question": question_text
        }
    
    def evaluate_answer(self, student_id, question_data, user_answer):
        """Bewertet die Antwort des Studenten und zeigt sofort die richtige Antwort an"""
        if not question_data or "question" not in question_data:
            return {"error": "Keine gültige Frage zur Bewertung"}
        
        question_type = question_data.get("question_type")
        question = question_data.get("question", {})
        
        if "error" in question:
            return {"error": "Die Frage enthält Fehler und kann nicht bewertet werden"}
        
        # Punktzahl berechnen
        score = 0
        max_score = 100
        
        # Detaillierte Bewertung für den ersten Satz des Feedbacks
        detailed_feedback = ""
        
        if question_type == "multiple_choice":
            correct_answers = question.get("correct_answers", [])
            user_answers = [ans.strip().upper() for ans in user_answer] if isinstance(user_answer, list) else [user_answer.strip().upper()]
            
            # Berechne richtige und falsche Antworten
            correct_selected = [ans for ans in user_answers if ans in correct_answers]
            incorrect_selected = [ans for ans in user_answers if ans not in correct_answers]
            missed_correct = [ans for ans in correct_answers if ans not in user_answers]
            
            correct_count = len(correct_selected)
            incorrect_count = len(incorrect_selected)
            
            if correct_count == len(correct_answers) and incorrect_count == 0:
                score = max_score
                detailed_feedback = f"Alle Antworten sind korrekt! Du hast die richtigen Optionen ({', '.join(correct_answers)}) ausgewählt."
            elif correct_count > 0 and incorrect_count == 0:
                score = int((correct_count / len(correct_answers)) * max_score)
                detailed_feedback = f"Teilweise richtig. Du hast {correct_count} von {len(correct_answers)} richtigen Optionen ausgewählt ({', '.join(correct_selected)}), aber die Optionen {', '.join(missed_correct)} fehlen."
            elif correct_count == 0:
                score = 0
                detailed_feedback = f"Leider falsch. Du hast keine der richtigen Optionen ({', '.join(correct_answers)}) ausgewählt."
            else:
                score = max(0, int((correct_count / len(correct_answers) - incorrect_count / (len(question.get("options", {})) - len(correct_answers))) * max_score))
                detailed_feedback = f"Teilweise richtig, aber mit Fehlern. Richtig ausgewählt: {', '.join(correct_selected)}. Falsch ausgewählt: {', '.join(incorrect_selected)}. Nicht ausgewählt, aber richtig wären: {', '.join(missed_correct)}."
            
        elif question_type == "single_choice":
            correct_answer = question.get("correct_answers", "")
            user_answer = user_answer.strip().upper() if isinstance(user_answer, str) else ""
            
            if user_answer == correct_answer:
                score = max_score
                detailed_feedback = f"Richtig! Die Antwort {correct_answer} ist korrekt."
            else:
                score = 0
                detailed_feedback = f"Leider falsch. Du hast {user_answer} ausgewählt, aber die richtige Antwort ist {correct_answer}."
            
        elif question_type == "sorting":
            correct_order = question.get("correct_order", [])
            user_order = [order.strip() for order in user_answer] if isinstance(user_answer, list) else []
            
            if user_order == correct_order:
                score = max_score
                detailed_feedback = f"Richtig! Die Reihenfolge {', '.join(correct_order)} ist korrekt."
            else:
                # Finde die korrekt positionierten Elemente
                correct_positions = [(i, item) for i, item in enumerate(user_order) if i < len(correct_order) and item == correct_order[i]]
                wrong_positions = [(i, item) for i, item in enumerate(user_order) if i < len(correct_order) and item != correct_order[i]]
                
                score = int((len(correct_positions) / len(correct_order)) * max_score)
                
                if correct_positions:
                    correct_pos_str = ", ".join([f"{item} an Position {i+1}" for i, item in correct_positions])
                    detailed_feedback = f"Teilweise richtig. Korrekt platziert: {correct_pos_str}. "
                else:
                    detailed_feedback = "Leider ist keine Position korrekt. "
                
                detailed_feedback += f"Die richtige Reihenfolge wäre: {', '.join(correct_order)}."
        
        
        elif question_type == "open_answer":
            # Kriterien und Musterantwort aus den Fragedaten abrufen
            criteria = question.get('criteria', [])
            model_answer = question.get('model_answer', '')
            question_text = question.get('question', '')
            
            # Benutzerantwort formatieren
            user_answer_text = str(user_answer) if not isinstance(user_answer, list) else ", ".join(user_answer)
            
            # Formatiere die Kriterien als Text
            criteria_text = "\n".join([f"- {criterion}" for criterion in criteria])
            
            # Feedback mit der Chain generieren
            result = self.feedback_chain.run(
                question=question_text,
                model_answer=model_answer,
                criteria=criteria_text,
                answer=user_answer_text
            )
            
            # Punktzahl und Feedback extrahieren
            score_match = re.search(r'PUNKTZAHL:\s*(\d+)', result)
            feedback_match = re.search(r'FEEDBACK:\s*(.*)', result, re.DOTALL)
            
            if not score_match or not feedback_match:
                raise ValueError("Das LLM hat kein gültiges Format für Punktzahl und Feedback zurückgegeben.")
                
            score = int(score_match.group(1))
            score = max(0, min(100, score))  # Sicherstellen, dass der Wert im gültigen Bereich liegt
            feedback = feedback_match.group(1).strip()
            
            # Richtige Antwort und Erklärung aus den Fragedaten extrahieren
            correct_answer_info = question.get("correct_answer_info", "")
            explanation = question.get("explanation", "")

        # Richtige Antwort und Erklärung aus den Fragedaten extrahieren
        correct_answer_info = question.get("correct_answer_info", "")
        explanation = question.get("explanation", "")
        
        # Feedback mit detaillierter Bewertung und erläuternder Erklärung
        feedback = ""
        
        # In der evaluate_answer-Methode für offene Fragen
        if question_type == "open_answer":
            question_text = question.get('question', '')
            model_answer = question.get('model_answer', '')
            
            # Benutzerantwort formatieren
            user_answer_text = ""
            if isinstance(user_answer, list):
                user_answer_text = ", ".join(user_answer)
            else:
                user_answer_text = str(user_answer)
            
            # Feedback mit der Chain generieren
            try:
                feedback_text = self.feedback_chain.run(
                    question=question_text,
                    answer=user_answer_text
                )
                
                # Feedback auf max. 5 Sätze begrenzen und mit detaillierter Bewertung kombinieren
                sentences = re.split(r'(?<=[.!?])\s+', feedback_text)
                feedback = detailed_feedback + ' '.join(sentences[:5])
            except Exception as e:
                print(f"Fehler bei der Generierung des Feedbacks: {e}")
                feedback = detailed_feedback + " Leider konnte kein detailliertes Feedback generiert werden."
        else:
            # Für andere Fragetypen verwenden wir die vorgenerierte Erklärung mit der detaillierten Bewertung
            feedback = detailed_feedback + " " + explanation
        
        # Fortschritt aktualisieren
        new_level, new_progress = self.update_student_progress(student_id, score)
        
        return {
            "feedback": feedback,
            "score": score,
            "max_score": max_score,
            "new_level": new_level,
            "progress": new_progress,
            "correct_answer_info": correct_answer_info,
            "explanation": explanation,
            "is_correct": score == max_score  # Flag für die Richtigkeit
        }
    
    def update_student_progress(self, student_id, score):
        """Aktualisiert den Fortschritt des Studenten basierend auf der Punktzahl"""
        progress = get_progress(student_id)
        current_level = progress[3]
        current_progress = progress[4]
        
        # Fortschrittszuwachs berechnen
        progress_increase = 0
        if score >= 90:
            progress_increase = 10
        elif score >= 70:
            progress_increase = 5
        elif score >= 50:
            progress_increase = 0
        else:
            progress_increase = -10
        
        new_progress = min(100, current_progress + progress_increase)
        
        # Wenn der Fortschritt 100% erreicht, steige ein Level auf
        new_level = current_level
        if new_progress >= 100 and current_level < 6:  # Maximal Bloom-Level 6
            new_level = current_level + 1
            new_progress = 0
        
        # Fortschritt in der Datenbank aktualisieren
        update_progress(student_id, progress[1], progress[2], new_level, new_progress)
        
        return new_level, new_progress
    
    def process_followup_question(self, student_id, question_data, feedback, followup_question):
        """Verarbeitet eine Nachfrage zum Feedback"""
        if not question_data or not feedback:
            return "Ich kann deine Frage nicht beantworten, da keine Frage oder Feedback vorhanden ist."
        
        try:
            # Kontext für die Nachfrage erstellen
            context_text = f"""
            Ursprüngliche Frage: {question_data.get('question', {}).get('question', 'Keine Frage verfügbar')}
            
            Feedback: {feedback}
            
            Nachfrage des Studenten: {followup_question}
            """
            
            # Nachfrage mit der bestehenden Chain verarbeiten
            result = self.followup_chain.run(context=context_text)
            
            # Antwort auf max. 5 Sätze begrenzen
            sentences = re.split(r'(?<=[.!?])\s+', result.strip())
            short_result = ' '.join(sentences[:5])
            
            return short_result
            
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der Nachfrage: {e}")
            return f"Leider ist bei der Verarbeitung deiner Nachfrage ein Fehler aufgetreten: {e}"
