"""
UI-Modul für StudySpark
Kombiniert Frontend-Implementierungen (Konsole und Streamlit)
"""
import streamlit as st
from services import LearningService
from models import BLOOM_LEVELS

class UserInterface:
    """
    Basisklasse für das Frontend.
    Diese Klasse sollte von konkreten Frontend-Implementierungen erweitert werden.
    """
    
    def __init__(self, learning_service):
        """Initialisiert das Frontend mit einem Learning-Service."""
        self.service = learning_service
        self.current_question = None
        self.current_feedback = None
        self.followup_history = []
        self.student_id = "student_123"  # Standard-Student-ID
        self.student_progress = None
    
    def initialize_session(self, student_id="student_123"):
        """Initialisiert eine neue Sitzung für einen Studenten und generiert die erste Frage im Voraus."""
        self.student_id = student_id
        self.student_progress = self.service.get_student_progress(student_id)
        self.current_question = None
        self.current_feedback = None
        self.followup_history = []
        
        # Erste Frage im Voraus generieren
        self.service.pregenerate_question(student_id)
    
    def get_new_question(self):
        """Holt eine neue Frage vom Service (vorgeneriert oder frisch generiert)."""
        question_data = self.service.get_next_question(self.student_id)
        self.current_question = question_data
        self.current_feedback = None
        self.followup_history = []
        return question_data
    
    def submit_answer(self, answer):
        """Übermittelt eine Antwort an den Service und erhält Feedback."""
        if not self.current_question:
            return {"error": "Keine aktuelle Frage vorhanden."}
        
        result = self.service.evaluate_answer(
            self.student_id, 
            self.current_question,
            answer
        )
        self.current_feedback = result
        self.student_progress = self.service.get_student_progress(self.student_id)
        
        return result
    
    def submit_followup_question(self, followup_question):
        """Übermittelt eine Nachfrage zum Feedback."""
        if not self.current_question or not self.current_feedback:
            return {"error": "Keine aktuelle Frage oder Feedback vorhanden."}
        
        answer = self.service.process_followup_question(
            self.student_id,
            self.current_question,
            self.current_feedback.get("feedback", ""),
            followup_question
        )
        
        followup_entry = {
            "question": followup_question,
            "answer": answer
        }
        self.followup_history.append(followup_entry)
        return followup_entry
    
    def get_progress(self):
        """Gibt den aktuellen Fortschritt des Studenten zurück."""
        return self.student_progress
    
    def update_student_level(self, new_level):
        """Aktualisiert das Level des Studenten."""
        if not 1 <= new_level <= 6:
            return False  # Ungültiges Level
            
        # Hole den aktuellen Fortschritt
        progress = self.student_progress
        
        # Aktualisiere die Datenbank direkt
        from models import update_progress
        update_progress(
            self.student_id,
            progress["module"],
            progress["topic"],
            new_level,
            0  # Setze den Fortschritt auf 0 für das neue Level
        )
        
        # Aktualisiere den lokalen Fortschritt
        self.student_progress = self.service.get_student_progress(self.student_id)
        
        # Generiere eine neue Frage für das neue Level im Voraus
        self.service.pregenerate_question(self.student_id)
        
        return True  # Erfolgreiche Aktualisierung


    # Abstrakte Methoden, die von konkreten Implementierungen überschrieben werden müssen
    def display_question(self, question_data):
        """Zeigt eine Frage an."""
        raise NotImplementedError("Diese Methode muss von einer konkreten Frontend-Implementierung überschrieben werden.")
    
    def display_feedback(self, feedback, followup_history):
        """Zeigt Feedback und Nachfragen an."""
        raise NotImplementedError("Diese Methode muss von einer konkreten Frontend-Implementierung überschrieben werden.")

    def display_progress(self, progress_data):
        """Zeigt den Fortschritt des Studenten an."""
        raise NotImplementedError("Diese Methode muss von einer konkreten Frontend-Implementierung überschrieben werden.")
    
    def run(self):
        """Startet die Frontend-Anwendung."""
        raise NotImplementedError("Diese Methode muss von einer konkreten Frontend-Implementierung überschrieben werden.")

class ConsoleFrontend(UserInterface):
    """Einfache Konsolen-basierte Frontend-Implementierung."""
    
    def display_question(self, question_data):
        """Zeigt eine Frage in der Konsole an mit Vorbereitung für sofortige Anzeige der richtigen Antwort."""
        if not question_data:
            print("Fehler: Keine Fragedaten vorhanden.")
            return None
            
        question_type = question_data.get("question_type", "")
        question = question_data.get("question", {})
        
        if not question_type or not question:
            print("Fehler: Unvollständige Fragedaten.")
            return None
        
        print("\n" + "="*50)
        fragetyp_name = ""
        if question_type == "single_choice":
            fragetyp_name = "Single-Choice"
        elif question_type == "multiple_choice":
            fragetyp_name = "Multiple-Choice"
        elif question_type == "sorting":
            fragetyp_name = "Sortierung"
        elif question_type == "open_answer":
            fragetyp_name = "Offene Frage"
            
        print(f"Frage (Typ: {fragetyp_name}):")
        print("-"*50)
        
        if "error" in question:
            print(f"Fehler bei der Fragengenerierung: {question.get('error', 'Unbekannter Fehler')}")
            print("Rohtext:")
            print(question_data.get("raw_question", "Kein Rohtext verfügbar"))
            return None
        
        print(question.get("question", "Keine Frage verfügbar"))
        print()
        
        if question_type in ["multiple_choice", "single_choice"]:
            options = question.get("options", {})
            if not options:
                print("Fehler: Keine Antwortmöglichkeiten verfügbar.")
                return None
                
            print("Antwortmöglichkeiten:")
            for key, value in options.items():
                print(f"{key}) {value}")
            
            if question_type == "multiple_choice":
                return input("\nWähle alle zutreffenden Antworten (z.B. 'A,C'): ").split(",")
            else:
                return input("\nWähle die richtige Antwort: ")
            
        elif question_type == "sorting":
            elements = question.get("elements", {})
            if not elements:
                print("Fehler: Keine Elemente zum Sortieren verfügbar.")
                return None
                
            print("Elemente:")
            for key, value in elements.items():
                print(f"{key}. {value}")
            
            return input("\nGib die richtige Reihenfolge ein (z.B. '3,1,4,2'): ").split(",")
            
        else:  # open_answer
            return input("\nDeine Antwort: ")
    
    def display_feedback(self, feedback, followup_history):
        """Zeigt Feedback, die richtige Antwort und Erklärung in der Konsole an."""
        if not feedback:
            print("\nKein Feedback verfügbar.")
            return None
            
        print("\n" + "="*50)
        
        # Richtige Antwort anzeigen
        correct_answer_info = feedback.get("correct_answer_info", "")
        if correct_answer_info:
            print("Richtige Antwort:")
            print(correct_answer_info)
            print("-"*50)
        
        # Erklärung anzeigen
        explanation = feedback.get("explanation", "")
        if explanation:
            print("Erklärung:")
            print(explanation)
            print("-"*50)
        
        # Punktzahl anzeigen
        # Punktzahl anzeigen
        score = feedback.get("score", 0)
        max_score = feedback.get("max_score", 100)
        print(f"Punktzahl: {score} von {max_score}")
        
        # Feedback anzeigen
        feedback_text = feedback.get("feedback", "")
        if feedback_text:
            print("\nFeedback:")
            print(feedback_text)
        
        if followup_history:
            print("\nBisherige Nachfragen:")
            for entry in followup_history:
                print(f"\nFrage: {entry['question']}")
                print(f"Antwort: {entry['answer']}")
        
        followup = input("\nHast du eine Frage zum Feedback? (Leerlassen zum Überspringen): ")
        return followup if followup.strip() else None
    
    def display_progress(self, progress_data):
        """Zeigt den Fortschritt in der Konsole an und ermöglicht die Anpassung des Niveaus."""
        if not progress_data:
            print("\nKein Fortschritt verfügbar.")
            return
            
        print("\n" + "="*50)
        print("Fortschritt:")
        print("-"*50)
        
        level = progress_data.get('level', 1)
        level_description = progress_data.get('level_description', 'Keine Beschreibung verfügbar')
        progress = progress_data.get('progress', 0)
        
        print(f"Level {level}: {level_description}")
        print(f"Fortschritt: {progress}%")
        
        # Anforderungsniveau anpassen
        print("\nMöchtest du das Anforderungsniveau anpassen? (j/n)")
        choice = input()
        
        if choice.lower() == 'j':
            print("\nVerfügbare Niveaus:")
            for level_num, desc in BLOOM_LEVELS.items():
                print(f"{level_num}: {desc}")
                
            try:
                new_level = int(input("\nWähle ein Niveau (1-6): "))
                if 1 <= new_level <= 6:
                    self.update_student_level(new_level)
                    print(f"\nNiveau auf Level {new_level} gesetzt!")
                else:
                    print("\nUngültige Eingabe. Niveau bleibt unverändert.")
            except ValueError:
                print("\nUngültige Eingabe. Niveau bleibt unverändert.")
    
    def run(self):
        """Startet die Konsolen-Anwendung mit sofortiger Anzeige der richtigen Antworten."""
        print("Willkommen bei StudySpark!")
        
        # Initialisiere die Sitzung
        self.initialize_session()
        
        while True:
            # Zeige den aktuellen Fortschritt an
            self.display_progress(self.student_progress)
            
            # Frage den Benutzer, ob er eine neue Frage möchte
            choice = input("\nMöchtest du eine Frage beantworten? (j/n): ")
            if choice.lower() != "j":
                break
            
            # Hole eine neue Frage (vorgeneriert oder frisch generiert)
            try:
                question_data = self.get_new_question()
            except Exception as e:
                print(f"Fehler beim Abrufen einer Frage: {e}")
                continue
            
            # Zeige die Frage an und hole die Antwort
            answer = self.display_question(question_data)
            if answer is None:
                continue
            
            # Übermittle die Antwort und erhalte Feedback mit sofortiger Anzeige der richtigen Antwort
            try:
                result = self.submit_answer(answer)
                if "error" in result:
                    print(f"Fehler: {result['error']}")
                    continue
            except Exception as e:
                print(f"Fehler beim Übermitteln der Antwort: {e}")
                result = {"feedback": "Fehler beim Verarbeiten der Antwort."}
            
            # Zeige das Feedback mit der richtigen Antwort und Erklärung an
            followup = self.display_feedback(result, [])
            print("vor while schleife")
            # Verarbeite Nachfragen
            while followup:
                try:
                    print("followup4554")
                    followup_result = self.submit_followup_question(followup)
                    if isinstance(followup_result, dict) and "error" in followup_result:
                        print(f"Fehler: {followup_result['error']}")
                        break
                except Exception as e:
                    print(f"Fehler bei der Verarbeitung der Nachfrage: {e}")
                    break
                
                # Zeige das aktualisierte Feedback mit allen bisherigen Nachfragen an
                followup = self.display_feedback(self.current_feedback, self.followup_history)
        
        print("Vielen Dank für die Nutzung von StudySpark!")

class StreamlitFrontend(UserInterface):
    """Streamlit-basierte Frontend-Implementierung."""
    
    def display_question(self, question_data):
        """Zeigt eine Frage an und sammelt die Antwort."""
        import streamlit as st
        
        if not question_data or "error" in question_data.get("question", {}):
            st.error("Fehler bei der Fragengenerierung.")
            return None
            
        question_type = question_data.get("question_type", "")
        question = question_data.get("question", {})
        
        st.write(question.get("question", ""))
        
        # Eingabeelemente je nach Fragetyp
        if question_type == "multiple_choice":
            options = question.get("options", {})
            selected_options = []
            for key, value in sorted(options.items()):
                if st.checkbox(f"{key}) {value}"):
                    selected_options.append(key)
            if st.button("Antworten"):
                return selected_options
            
        elif question_type == "single_choice":
            options = question.get("options", {})
            option_list = [f"{key}) {value}" for key, value in sorted(options.items())]
            selected_option = st.radio("", option_list)
            if st.button("Antworten"):
                return selected_option.split(")")[0]
            
        elif question_type == "sorting":
            elements = question.get("elements", {})
            for key, value in sorted(elements.items()):
                st.write(f"{key}. {value}")
            order_input = st.text_input("Reihenfolge (z.B. '3,1,4,2'):")
            if st.button("Antworten"):
                return order_input.split(",")
            
        else:  # open_answer
            user_answer = st.text_area("", height=150)
            if st.button("Antworten"):
                return user_answer
        
        return None

    def display_feedback(self, feedback, followup_history):
        import streamlit as st
        
        if not feedback:
            return None
        
        # Zeige die ursprüngliche Frage an
        if hasattr(self, 'current_question') and self.current_question:
            question_data = self.current_question
            question_type = question_data.get("question_type", "")
            question = question_data.get("question", {})
            
            # Frage anzeigen
            st.markdown("### " + question.get("question", ""))
            
            # Antwortmöglichkeiten anzeigen
            if question_type in ["multiple_choice", "single_choice"]:
                options = question.get("options", {})
                if options:
                    for key, value in sorted(options.items()):
                        st.markdown(f"- **{key})** {value}")
            elif question_type == "sorting":
                elements = question.get("elements", {})
                if elements:
                    for key, value in sorted(elements.items()):
                        st.markdown(f"- **{key}.** {value}")
        
        st.markdown("---")
        
        # Richtige Antwort und Erklärung
        st.success(feedback.get("correct_answer_info", ""))
        # Feedback
        if feedback.get("feedback"):
            st.info(feedback.get("feedback"))
        else:
            st.info(feedback.get("explanation", ""))
        
        # Punktzahl
        st.metric("Punktzahl", f"{feedback.get('score', 0)} von {feedback.get('max_score', 100)}")
        
        # Bisherige Nachfragen anzeigen (falls vorhanden)
        if followup_history:
            st.subheader("Bisherige Nachfragen")
            for i, entry in enumerate(followup_history):
                st.write(f"**Nachfrage {i+1}:** {entry.get('question', '')}")
                st.write(f"**Antwort:** {entry.get('answer', '')}")
        
        # Nachfrage-Option hinzufügen
        st.subheader("Hast du eine Frage zum Feedback?")
        followup_question = st.text_area("Deine Nachfrage:", height=100, key="followup_input")
        
        # Wichtig: Stelle sicher, dass der Button-Klick einen Wert zurückgibt
        if st.button("Senden", key="send_followup"):
            if followup_question.strip():  # Prüfe, ob die Nachfrage nicht leer ist
                return followup_question.strip()
        
        return None



    def display_progress(self, progress_data):
        """Zeigt den Fortschritt an."""
        import streamlit as st
        
        if not progress_data:
            return
            
        # Grundlegende Fortschrittsinformationen
        level = progress_data.get('level', 1)
        progress = progress_data.get('progress', 0)
        
        st.sidebar.subheader("Fortschritt")
        st.sidebar.progress(progress / 100)
        st.sidebar.write(f"Level {level}: {progress}%")
        
        # Niveau-Auswahl
        level_options = [f"Level {i}" for i in BLOOM_LEVELS.keys()]
        selected_level = st.sidebar.selectbox(
            "Niveau:",
            level_options,
            index=level-1
        )
        
        selected_level_num = int(selected_level.split(" ")[1])
        
        if st.sidebar.button("Ändern"):
            success = self.update_student_level(selected_level_num)
            if success:
                st.sidebar.success(f"Level auf {selected_level_num} geändert!")
                st.rerun()
            else:
                st.sidebar.error("Fehler beim Ändern des Levels.")

