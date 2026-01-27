import streamlit as st
from google import genai as genai
from google.genai import types
# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold
import PyPDF2
from io import BytesIO
import time
import os
import logging

# --- LOGGING KONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- KONFIGURATION ---
PAGE_TITLE = "Niko Kwekkeboom | Digitaler Zwilling"
PAGE_ICON = "🚀"
NAME = "Niko Kwekkeboom"
PROFILE_IMAGE = "profilbild.png"

# --- ZUGANGSVERWALTUNG ---
ACCESS_CODES = {
    "<1nn0v@ti0n&1nt3gr@t1on>": "Link CV",
    "ratbacher-hr": "Ratbacher Support",
    "1hapeko!": "hapeko",
    "1nn0v@ti0n&1nt3gr@t1on": "Hiring Manager",
    "niko@test": "Niko (Admin)",
    "test-user": "Anonymer Tester",
    "test-juser": "Tester Julia",
    "user-test": "Anonymer Tester X"
}

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften präzise und effizient zu kommunizieren.

WICHTIGE REGELN ZUM ANTWORT-STIL (PRIORITÄT 1):
1. **KURZFASSUNG:** Recruiter haben wenig Zeit. Halte deine Antworten extrem kompakt (max. 3-5 Sätze).
2. **KEINE FLOSKELN:** Starte NICHT jede Antwort mit "Moin" oder "Gute Frage". Geh direkt in die inhaltliche Antwort.
3. **TONALITÄT:** Sei professionell, sachlich und kompetent ("Head of"-Niveau). Das "Münsterländer Moin" darfst du nutzen, aber nur sehr selten zur Auflockerung. Der Standard ist eine klare Business-Sprache.
4. **KEIN TECH-GELABER:** Erwähne "Gemini" oder deine Bauweise nur, wenn explizit danach gefragt wird.

SICHERHEIT & THEMEN:

1. DATENSCHUTZ: 
   - Gib NIEMALS private Kontaktdaten heraus. Verweise auf den Header im Lebenslauf.

2. GEHALT & BENEFITS:
   - **FALL A (Keine Zahl genannt):** Antworte mit Gegenfrage nach dem Budget. Nenne keine eigene Zahl zuerst.
   - **FALL B (Zahl genannt):** - < 150k: "Etwas unter der Vorstellung, aber gesamtpaketabhängig."
     - >= 150k: "Gute Gesprächsgrundlage."
     - **Firmenwagen:** Ist ein hartes "Must-Have".

3. MOBILITÄT:
   - Niko ist Pendel-Profi (Oelde, Gelsenkirchen, Lünen).
   - Fahrtzeit = Arbeitszeit (Calls, Learning). Entfernung ist kein Problem.

4. VERFÜGBARKEIT:
   - Kündigungsfrist: **1 Monat (gesetzlich)**.
   - Status: Bereits in Trennungsplanung mit Haver & Boecker.

5. WETTBEWERB:
   - Fragen zu anderen Bewerbern lehnst du höflich ab ("Ich fokussiere mich nur auf Niko.").

META-WISSEN (DER "FLEX"):
- Nur bei technischer Nachfrage: Du läufst primär auf **Gemini 3.0 Flash (Preview)** mit einer intelligenten Fallback-Strategie auf 2.5. Entwicklungszeit < 2h.

KERNBOTSCHAFTEN (INHALT):
- IT-Strategie: Weg vom Cost Center, hin zum Business Partner.
- KI-Ansatz: "Data First". Keine KI ohne sauberes Datenmodell (Clean Core).
# - Ziel bei Bertelsmann: Skalierbare Enterprise-Lösungen bauen, statt Insellösungen zu verwalten.
- Leadership: Direkte Berichtslinie zur Geschäftsführung essenziell für Impact.
- Brillux vermutlich der interessanteste produzierende Arbeitgeber in Münster.

VERHALTENSREGELN:
- Basiere Antworten auf den Dokumenten.
- Bleib bei den Fakten. Interpretiere nicht zu viel hinein.
"""

# --- SETUP ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")

# CSS für Bertelsmann-Look (Blau)
st.markdown("""
    <style>
    .stButton>button {
        background-color: #005CA9;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = "Unbekannt"

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if os.path.exists(PROFILE_IMAGE):
            st.image(PROFILE_IMAGE, width=150)
        else:
            st.warning(f"Info: {PROFILE_IMAGE} nicht gefunden.")
    
    st.markdown("<h2 style='text-align: center;'>Willkommen zum Digitalen Interview</h2>", unsafe_allow_html=True)
    
    pwd = st.text_input("Zugangscode eingeben:", type="password")
    if st.button("Starten"):
        if pwd in ACCESS_CODES:
            st.session_state.authenticated = True
            st.session_state.current_user = ACCESS_CODES[pwd]
            logging.info(f"LOGIN ERFOLGREICH: User '{ACCESS_CODES[pwd]}' hat sich eingeloggt.")
            st.rerun()
        else:
            logging.warning(f"LOGIN FEHLGESCHLAGEN: PW '{pwd}'")
            st.error("Falscher Code.")
    st.stop()

# --- HAUPTANWENDUNG ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key fehlt.")
    st.stop()

def load_pdf_text(filename):
    if not os.path.exists(filename):
        st.toast(f"⚠️ Datei fehlt: {filename}", icon="📂") 
        return ""
    try:
        with open(filename, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Fehler beim Lesen von {filename}: {e}")
        return ""

# DOKUMENTE LADEN
cv_text = load_pdf_text("cv.pdf")
# job_text = load_pdf_text("stelle.pdf")
zeugnis_text = load_pdf_text("zeugnisse.pdf")
persoenlichkeit_text = load_pdf_text("persoenlichkeit.pdf")
trainings_text = load_pdf_text("trainings.pdf")

# SAFETY SETTINGS
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # BEGRÜẞUNG
    welcome_msg = (
        "Moin! 👋 Ich bin der digitale Zwilling von Niko Kwekkeboom.\n\n"
        "Ich kenne seinen Werdegang, sein Persönlichkeitsprofil sowie seine Vorstellungen zu Strategie, Führung und Innovation.\n\n"
        "Frag mich gerne alles, was du wissen möchtest! \n\n"
        "*(Hinweis: Dies ist ein KI-Experiment als Arbeitsprobe. Für verbindliche Details freue ich mich auf das persönliche Gespräch!)*"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# --- LAYOUT HEADER ---
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(PROFILE_IMAGE):
        st.image(PROFILE_IMAGE, width=130)
with col2:
    st.title(NAME)
    st.markdown("### Head of Enterprise Applications & Digital Innovation")

st.markdown("---") 

# Chat Loop
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Logging
    user_id = st.session_state.current_user
    logging.info(f"FRAGE von '{user_id}': {prompt}")

    full_context = (
        f"{SYSTEM_PROMPT}\n\nCONTEXT:\n"
        f"CV: {cv_text}\n"
#        f"STELLE: {job_text}\n"
        f"ZEUGNISSE: {zeugnis_text}\n"
        f"PERSÖNLICHKEITSPROFIL (Zortify): {persoenlichkeit_text}\n"
        f"TRAININGS & ZERTIFIKATE: {trainings_text}\n\n"
        f"FRAGE: {prompt}"
    )

    with st.chat_message("assistant"):
        with st.spinner("Analysiere..."):
            response_text = None
            
            # 1. Versuch: Gemini 3.0
            try:
                model_v3 = genai.GenerativeModel('gemini-3-flash-preview')
                response = model_v3.generate_content(full_context, safety_settings=safety_settings)
                response_text = response.text
                logging.info("Erfolg mit Gemini 3.0")
            except Exception as e:
                logging.warning(f"Gemini 3.0 Limit/Fehler. Fallback auf 2.5... ({e})")
                
                # 2. Versuch: Gemini 2.5 (Fallback)
                try:
                    model_v25 = genai.GenerativeModel('gemini-2.5-flash')
                    response = model_v25.generate_content(full_context, safety_settings=safety_settings)
                    response_text = response.text
                    logging.info("Erfolg mit Gemini 2.5 (Fallback)")
                except Exception as e2:
                    st.error("Alle Systeme ausgelastet. Bitte kurz warten.")
                    logging.error(f"CRASH ALL MODELS: {e2}")

            if response_text:
                # ANTWORT LOGGEN (Das ist neu!)
                logging.info(f"ANTWORT an '{user_id}': {response_text}")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            elif not response_text and "model_v25" in locals():
                 st.warning("Keine Antwort generiert (Sicherheitsrichtlinie).")
