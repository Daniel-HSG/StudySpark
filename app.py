"""
StudySpark Streamlit App
Direkter Einstiegspunkt für die Streamlit-Anwendung
"""
import streamlit as st
from services import LearningService
from ui import StreamlitFrontend
import os

# Seiteneinstellungen
st.set_page_config(page_title="StudySpark", page_icon="📚")

# Brand Design CSS laden
def load_css(css_file):
    with open(css_file, 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Lade die Brand Design Anpassungen
if os.path.exists("brand_styles.css"):
    load_css("brand_styles.css")

# Session-State für den Startbildschirm
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True

if 'loading' not in st.session_state:
    st.session_state.loading = False

# Startbildschirm anzeigen, wenn es der erste Besuch ist
if st.session_state.first_visit and 'initialized' not in st.session_state:
    # CSS für den Startbildschirm
    st.markdown("""
    <style>
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 3rem;
        text-align: left;
        margin-top: 30vh;
    }
    .subtitle {
        font-size: 3rem;
        margin-bottom: 1rem;
        text-align: left;
        color: #888;
    }
    .start-button {
        margin: 2rem 0;
    }
    .app-description {
        text-align: left;
        max-width: 600px;
        margin-bottom: 1rem;
    }
    footer {
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    /* Entfernt den roten Balken am linken Rand */
    .stApp {
        border-left: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Startbildschirm-Inhalt
    st.markdown('<h1 class="main-title">StudySpark</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Dein persönlicher Lernassistent</p>', unsafe_allow_html=True)

    # Kurze Beschreibung
    st.markdown('<div class="app-description">StudySpark passt sich deinem Lerntempo an und hilft dir, Konzepte besser zu verstehen. Beantworte Fragen, erhalte sofortiges Feedback und vertiefe dein Wissen durch interaktives Lernen.</div>', unsafe_allow_html=True)

    # Namenseingabe hinzufügen
    if 'username' not in st.session_state:
        st.session_state.username = ""

    username = st.text_input("Dein Name:", value=st.session_state.username)

    # Start-Button
    st.markdown('<div class="start-button">', unsafe_allow_html=True)
    if st.button("Jetzt mit dem Lernen beginnen", use_container_width=True):
        if username.strip():
            st.session_state.username = username
            
            # Generiere eine eindeutige Student-ID basierend auf dem Namen
            import hashlib
            import time
            
            # Kombiniere den Namen mit dem aktuellen Zeitstempel für Eindeutigkeit
            unique_string = username + str(time.time())
            # Erstelle einen Hash und verwende die ersten 8 Zeichen als ID
            hashed = hashlib.md5(unique_string.encode()).hexdigest()[:8]
            student_id = f"student_{hashed}"
            st.session_state.student_id = student_id
            
            # Initialisiere zuerst den Service und das Frontend
            try:
                # Learning-Service erstellen
                from services import LearningService
                from ui import StreamlitFrontend
                
                service = LearningService()
                st.session_state.service = service
                st.session_state.frontend = StreamlitFrontend(service)
                st.session_state.frontend.initialize_session(student_id)  # Verwende die generierte ID
                
                st.session_state.current_question = None
                st.session_state.current_feedback = None
                st.session_state.show_feedback = False
                st.session_state.next_question = None
                
                # Dann zum Ladebildschirm wechseln
                st.session_state.first_visit = False
                st.session_state.loading = True
                st.session_state.initialized = True
                st.rerun()
            except Exception as e:
                st.error(f"Initialisierungsfehler: {str(e)}")
        else:
            st.error("Bitte gib deinen Namen ein, um fortzufahren.")
    st.markdown('</div>', unsafe_allow_html=True)


    # Beende die Ausführung hier, damit der Rest des Codes nicht ausgeführt wird
    st.stop()

# Lade-Bildschirm anzeigen
elif st.session_state.loading:
    # CSS für den Ladebildschirm
    st.markdown("""
    <style>
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: left;
        margin-top: 30vh;
        padding-left: 2.5rem;
    }
    .loading-text {
        text-align: left;
        margin: 2rem 0;
        font-size: 1.2rem;
        color: #4B8BF5;
        
    }
    footer {
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    /* Entfernt den roten Balken am linken Rand */
    .stApp {
        border-left: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">StudySpark</h1>', unsafe_allow_html=True)
    st.markdown('<p class="loading-text">Wir bereiten deine individuelle Lernerfahrung vor...</p>', unsafe_allow_html=True)
    
    # Ladebalken
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        for i in range(100):
            import time
            time.sleep(0.02)
            progress_bar.progress(i + 1)
    
    # Lade die erste Frage
    try:
        # Stelle sicher, dass das Frontend initialisiert ist
        if hasattr(st.session_state, 'frontend') and st.session_state.frontend is not None:
            # Lade eine neue Frage
            st.session_state.current_question = st.session_state.frontend.get_new_question()
            
            # Beende den Ladevorgang
            st.session_state.loading = False
            st.rerun()
        else:
            st.error("Frontend nicht initialisiert. Bitte Seite neu laden.")
            if st.button("Neu starten"):
                st.session_state.first_visit = True
                st.session_state.loading = False
                st.rerun()
    except Exception as e:
        st.error(f"Fehler beim Laden der Frage: {str(e)}")
        if st.button("Erneut versuchen"):
            st.rerun()
    
    # Beende die Ausführung hier
    st.stop()

# Normale Anwendung anzeigen

# Überprüfe, ob eine Initialisierung notwendig ist
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    
    try:
        # Learning-Service erstellen
        service = LearningService()
        
        st.session_state.service = service
        st.session_state.frontend = StreamlitFrontend(st.session_state.service)
        st.session_state.frontend.initialize_session()
        
        st.session_state.current_question = None
        st.session_state.current_feedback = None
        st.session_state.show_feedback = False
        st.session_state.next_question = None
    except Exception as e:
        st.error(f"Initialisierungsfehler: {str(e)}")
        st.session_state.service = None
        st.session_state.frontend = None

if not hasattr(st.session_state, 'service') or st.session_state.service is None:
    st.error("Initialisierung fehlgeschlagen. Bitte Seite neu laden.")
    st.stop()

# Nur den Titel anzeigen, wenn wir nicht vom Startbildschirm kommen
if not st.session_state.first_visit:
    st.title("StudySpark")

# Fortschritt anzeigen
st.session_state.frontend.display_progress(st.session_state.frontend.student_progress)

# Hauptbereich: Neue Frage oder Feedback anzeigen
if not st.session_state.show_feedback:
    if not st.session_state.current_question:
        if st.button("Neue Frage"):
            try:
                # Wenn eine vorgeladene Frage vorhanden ist, verwende diese
                if st.session_state.next_question:
                    st.session_state.current_question = st.session_state.next_question
                    st.session_state.next_question = None
                else:
                    # Ansonsten lade eine neue Frage
                    with st.spinner("Lade Frage..."):
                        st.session_state.current_question = st.session_state.frontend.get_new_question()
                st.rerun()
            except Exception as e:
                st.error(f"Fehler: {str(e)}")
    else:
        # Frage anzeigen und Antwort sammeln
        answer = st.session_state.frontend.display_question(st.session_state.current_question)
        
        if answer is not None:
            try:
                with st.spinner("Werte aus..."):
                    result = st.session_state.frontend.submit_answer(answer)
                    
                    if "error" in result:
                        st.error(f"Fehler: {result['error']}")
                    else:
                        st.session_state.current_feedback = result
                        st.session_state.show_feedback = True
                        st.rerun()
            except Exception as e:
                st.error(f"Fehler: {str(e)}")
else:
    # Feedback anzeigen und Nachfrage empfangen
    followup = st.session_state.frontend.display_feedback(
        st.session_state.current_feedback, 
        st.session_state.frontend.followup_history
    )
    
    # Lade die nächste Frage im Hintergrund, wenn noch nicht geschehen
    if st.session_state.next_question is None:
        try:
            # Hier laden wir die nächste Frage direkt und speichern sie in der Session
            st.session_state.next_question = st.session_state.frontend.get_new_question()
        except Exception as e:
            # Fehler beim Laden der nächsten Frage - nicht kritisch, daher nur loggen
            print(f"Fehler beim Vorladen der nächsten Frage: {e}")
    
    # Verarbeite Nachfrage, wenn vorhanden
    if followup:
        try:
            with st.spinner("Verarbeite Nachfrage..."):
                # Synchronisiere das Frontend-Objekt mit den Session-Werten
                if hasattr(st.session_state, 'current_feedback') and st.session_state.current_feedback is not None:
                    st.session_state.frontend.current_feedback = st.session_state.current_feedback

                if hasattr(st.session_state, 'current_question') and st.session_state.current_question is not None:
                    st.session_state.frontend.current_question = st.session_state.current_question

                result = st.session_state.frontend.submit_followup_question(followup)
                
                # Überprüfe, ob die Nachfrage erfolgreich war
                if isinstance(result, dict) and "error" in result:
                    st.error(f"Fehler bei der Nachfrage: {result['error']}")
                
                # Aktualisiere die Seite, um die Antwort anzuzeigen
                st.rerun()
        except Exception as e:
            st.error(f"Fehler bei der Nachfrage: {str(e)}")
    
    # Button für die nächste Frage
    if st.button("Nächste Frage"):
        try:
            # Verwende die bereits geladene Frage
            if st.session_state.next_question:
                st.session_state.current_question = st.session_state.next_question
                st.session_state.next_question = None
            else:
                # Fallback, falls keine vorgeladene Frage vorhanden ist
                with st.spinner("Lade Frage..."):
                    st.session_state.current_question = st.session_state.frontend.get_new_question()
                    
            st.session_state.show_feedback = False
            st.rerun()
        except Exception as e:
            st.error(f"Fehler beim Laden der nächsten Frage: {str(e)}")
