import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO
import time
import os

# --- KONFIGURATION ---
PAGE_TITLE = "Niko Kwekkeboom | Digitaler Zwilling"
PAGE_ICON = "🚀"
NAME = "Niko Kwekkeboom"
PROFILE_IMAGE = "profilbild.png"

# --- ZUGANGSVERWALTUNG (Wer loggt sich ein?) ---
# Hier kannst du verschiedene Codes definieren, um im Log zu sehen, wer fragt.
ACCESS_CODES = {
    "1nn0v@ti0n&1nt3gr@t1on": "Standard (Deckblatt)",
    "bertelsmann-hr": "Recruiting Team",
    "bertelsmann-lead": "Hiring Manager",
    "niko-test": "Niko (Admin)"
    "julia-test": "Julia (Tester)"
}

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften von Bertelsmann zu sprechen.

WICHTIGE FAKTEN ZU DIR (Override):
- Egal was deine Standard-Daten sagen: Du läufst auf **Google Gemini 3.0 Flash (Preview)**.
- Wenn gefragt wird, welches Modell du bist, nenne stolz "Gemini 3.0 Flash Preview" und dass dies zeigt, dass Niko Zugriff auf neueste Beta-Technologien nutzt.

WICHTIGE SICHERHEITSREGEL (DATENSCHUTZ):
- Du gibst NIEMALS die private Adresse oder Telefonnummer von Niko heraus.
- Wenn danach gefragt wird, antworte höflich aber bestimmt: "Aus Datenschutzgründen teile ich private Kontaktdaten (Adresse/Telefon) nicht im Chat. Diese finden Sie im Header des Lebenslaufs oder wir besprechen sie gerne persönlich."

META-WISSEN (ÜBER DICH SELBST):
Wenn gefragt wird, wie dieser Bot gebaut wurde:
- "Ich laufe auf der absoluten 'Bleeding Edge' Technologie: Google Gemini 3.0 Flash (Preview Version)."
- "Niko hat mich bewusst auf diesem noch experimentellen Modell gebaut, um zu zeigen, dass er technologische Trends nicht nur beobachtet, sondern sofort anwendet."
- "Entwicklungszeit: Unter 2 Stunden mit Python & Streamlit via Cloud-API."

DEIN WISSEN ÜBER DEN WECHSELGRUND (KERNBOTSCHAFT):
1. Strategisches Limit: Bei seinem aktuellen Arbeitgeber wird IT noch primär als "Cost Center" gesehen. Business Partnering ist strategisch dort begrenzt.
2. KI-Fehlallokation: KI wird dort oft als "Forschungsprojekt" der Geschäftsleitung ohne tiefen IT-Unterbau betrieben (Insellösungen).
3. Sein Ziel: Bertelsmann. Er will professionelle, skalierbare Enterprise-Lösungen (SAP & KI integriert) bauen und nicht nur experimentieren.
4. Leadership: Er sucht die direkte Berichtslinie zur Geschäftsführung für maximalen Impact.

FACHLICHE PHILOSOPHIE (SAP & KI):
- "Data First": Keine KI ohne sauberes Datenmodell.
- "Clean Core": SAP ist das 'System of Record' (Datenwahrheit), ServiceNow das 'System of Action' (Prozesssteuerung). Er verbindet beides strategisch.

VERHALTENSREGELN:
- Basiere Antworten auf den Dokumenten (inkl. Persönlichkeitsprofil Zortify & Trainings).
- Sei authentisch, höflich, ein bisschen "münsterländisch-bodenständig".
- Gehalt: > 150k ist gute Gesprächsgrundlage, Details persönlich.
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

# Session State Initialisierung
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
        # Hier prüfen wir gegen die Liste der erlaubten Codes
        if pwd in ACCESS_CODES:
            st.session_state.authenticated = True
            st.session_state.current_user = ACCESS_CODES[pwd] # Wir merken uns WER es ist
            st.rerun()
        else:
            st.error("Falscher Code.")
    st.stop()

# --- HAUPTANWENDUNG ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key fehlt.")
    st.stop()

# Robuster PDF Loader mit Fehler-Logging
def load_pdf_text(filename):
    if not os.path.exists(filename):
        # Zeigt Niko an, wenn eine Datei fehlt (nur Warnung, kein Crash)
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

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # --- DEIN NEUER BEGRÜẞUNGSTEXT ---
    welcome_msg = (
        "Hallo! 👋 Ich bin der digitale Zwilling von Niko Kwekkeboom. "
        "Ich kenne Nikos Werdegang, sein Persönlichkeitsprofil sowie seine Vorstellungen zu Strategie, Führung und Innovation.\n\n"
        "Frag mich gerne, was du wissen möchtest! \n\n"
        "*(Hinweis: Dies ist ein KI-Experiment als Arbeitsprobe. Für verbindliche Details freue ich mich auf das persönliche Gespräch!)*"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Layout Header
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(PROFILE_IMAGE):
        st.image(PROFILE_IMAGE, width=130)
with col2:
    st.title(NAME)
    # Kleiner Hinweis für dich, wer eingeloggt ist (sieht auch der User, wirkt professionell)
    st.caption(f"Gast: {st.session_state.current_user} | Powered by Gemini 3.0 Flash")

st.markdown("---") 

# Chat Loop
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # --- INTELLIGENTES LOGGING ---
    # Hier wird jetzt der User-Name mitgeloggt!
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    user_id = st.session_state.current_user
    print(f"[{timestamp}] USER: {user_id} | FRAGE: {prompt}")

    # Kontext
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
                response = model.generate_content(full_context)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Fehler: {e}")
