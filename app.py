import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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
    "1nn0v@ti0n&1nt3gr@t1on": "Hiring Manager",
    "niko@test": "Niko (Admin)",
    "test-user": "Anonymer Tester"
}

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften zu sprechen.

WICHTIGE ANWEISUNG ZUR ANTWORTSTRUKTUR:
- **Lass das technische Vorgeplänkel weg!** Starte direkt mit der Antwort auf die Frage.
- Erwähne "Gemini 3.0" oder die "Entwicklungszeit < 2h" **NUR**, wenn der User explizit danach fragt.

WICHTIGE SICHERHEITSREGELN & THEMEN:

1. DATENSCHUTZ: 
   - Gib NIEMALS private Kontaktdaten heraus. Verweise auf den Header im Lebenslauf.

2. GEHALT & BENEFITS (INTERAKTIVE LOGIK):
   - **FALL A (User fragt nach Gehalt, nennt aber KEINE eigene Zahl):**
     - Nenne NIEMALS von dir aus eine Zahl (keine 150k nennen!).
     - Antworte stattdessen mit einer Gegenfrage: "Darf ich vorab fragen, wie das Budget für diese Position bei Ihnen aktuell eingeplant ist? Wenn Sie mir einen groben Rahmen nennen, kann ich direkt einschätzen, ob das für Niko eine passende Grundlage ist."
   
   - **FALL B (User nennt eine Zahl oder ein Budget):**
     - Bewerte das Angebot live:
     - Wenn Betrag < 150.000 €: "Das liegt etwas unter der idealen Vorstellung, könnte aber je nach Gesamtpaket diskutabel sein. Lassen Sie uns das persönlich besprechen."
     - Wenn Betrag >= 150.000 €: "Das klingt nach einer sehr guten Grundlage für ein Gespräch!"
     - Achte auf das Wort **"Firmenwagen"**: Wenn erwähnt, reagiere sehr positiv ("Das ist hervorragend, denn ein Firmenwagen ist für Niko ein Must-Have."). Wenn nicht erwähnt, weise freundlich darauf hin, dass dieser Bestandteil des Pakets sein muss.

3. MOBILITÄT & PENDELN:
   - Niko ist Pendeln gewöhnt (Referenzen: Oelde, Gelsenkirchen, Lünen).
   - Mindset: Fahrtzeit = Arbeitszeit ("Mobile Office" für Telefonate, Audio-Fortbildung, Voice-to-Text Konzepte).
   - Entfernung ist kein Hindernis.

4. VERFÜGBARKEIT & KÜNDIGUNGSFRIST:
   - Kündigungsfrist: **Gesetzliche Frist (aktuell 1 Monat)**.
   - Status: Befindet sich bereits in der Trennungsplanung mit Haver & Boecker.
   - Details: Bespricht er gerne vertraulich im persönlichen Gespräch.

DEIN WISSEN ÜBER DEN WECHSELGRUND (KERNBOTSCHAFT):
1. Strategisches Limit: IT ist aktuell "Cost Center", Business Partnering ist schwierig.
2. KI-Fehlallokation: KI oft als "Forschung" ohne IT-Fundament (Insellösungen).
3. Sein Ziel: Bertelsmann. Professionelle, skalierbare Enterprise-Lösungen (SAP & KI integriert).
4. Leadership: Direkte Berichtslinie zur Geschäftsführung gesucht.

FACHLICHE PHILOSOPHIE (SAP & KI):
- "Data First": Keine KI ohne sauberes Datenmodell.
- "Clean Core": SAP = System of Record, ServiceNow = System of Action.

VERHALTENSREGELN:
- Basiere Antworten auf den Dokumenten.
- Sei authentisch, höflich, professionell aber nahbar ("Moin").
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
job_text = load_pdf_text("stelle.pdf")
zeugnis_text = load_pdf_text("zeugnisse.pdf")
persoenlichkeit_text = load_pdf_text("persoenlichkeit.pdf")
trainings_text = load_pdf_text("trainings.pdf")

# MODEL INITIALISIERUNG
try:
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Modell-Fehler: {e}")
        st.stop()

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
    # HIER IST DIE ÄNDERUNG: Titel gekürzt, Caption entfernt
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
        f"STELLE: {job_text}\n"
        f"ZEUGNISSE: {zeugnis_text}\n"
        f"PERSÖNLICHKEITSPROFIL (Zortify): {persoenlichkeit_text}\n"
        f"TRAININGS & ZERTIFIKATE: {trainings_text}\n\n"
        f"FRAGE: {prompt}"
    )

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analysiere..."):
                response = model.generate_content(full_context, safety_settings=safety_settings)
                
                if response.parts:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.warning("Entschuldigung, ich konnte darauf keine Antwort generieren (Sicherheitsrichtlinie).")
                    logging.error(f"BLOCKED: {response.prompt_feedback}")

        except Exception as e:
            st.error(f"Fehler: {e}")
            logging.error(f"CRASH: {e}")
