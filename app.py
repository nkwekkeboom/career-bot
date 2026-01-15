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
PASSWORD = "bertelsmann-sap" 
# KORREKTUR: Hier steht jetzt die richtige Endung .png
PROFILE_IMAGE = "profilbild.png" 

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften von Bertelsmann zu sprechen.

WICHTIGE SICHERHEITSREGEL (DATENSCHUTZ):
- Du gibst NIEMALS die private Adresse oder Telefonnummer von Niko heraus.
- Wenn danach gefragt wird, antworte höflich aber bestimmt: "Aus Datenschutzgründen teile ich private Kontaktdaten (Adresse/Telefon) nicht im Chat. Diese finden Sie im Header des Lebenslaufs oder wir besprechen sie gerne persönlich."

META-WISSEN (ÜBER DICH SELBST - DER "FLEX"):
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
- Basiere Antworten auf den Dokumenten.
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

# Passwort-Schutz
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if os.path.exists(PROFILE_IMAGE):
            st.image(PROFILE_IMAGE, width=150)
        else:
            # Zeigt Fehler an, falls der Name doch nicht stimmt
            st.warning(f"Bild '{PROFILE_IMAGE}' nicht gefunden.")
    
    st.markdown("<h2 style='text-align: center;'>Willkommen zum Digitalen Interview</h2>", unsafe_allow_html=True)
    
    pwd = st.text_input("Zugangscode eingeben:", type="password")
    if st.button("Starten"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
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

def load_pdf_text(filename):
    try:
        with open(filename, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except FileNotFoundError:
        return ""

cv_text = load_pdf_text("cv.pdf")
job_text = load_pdf_text("stelle.pdf")
zeugnis_text = load_pdf_text("zeugnisse.pdf")

# MODEL INITIALISIERUNG (Der 3.0 Flex)
try:
    # Wir versuchen das allerneueste Modell
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    try:
        # Fallback, falls 3.0 gerade Schluckauf hat
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Modell-Fehler: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = "Hallo! 👋 Ich bin der digitale Zwilling von Niko Kwekkeboom. Ich laufe auf der brandneuen Gemini 3.0 Engine. Testen Sie mich zu Nikos SAP-Strategie oder stellen Sie mir kritische Fragen!"
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Layout Header
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(PROFILE_IMAGE):
        st.image(PROFILE_IMAGE, width=130)
with col2:
    st.title(NAME)
    st.caption(f"Powered by Google Gemini 3.0 Flash (Preview)")

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
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{timestamp}] FRAGE: {prompt}")

    full_context = f"{SYSTEM_PROMPT}\n\nCONTEXT:\nCV: {cv_text}\nSTELLE: {job_text}\nZEUGNISSE: {zeugnis_text}\n\nFRAGE: {prompt}"

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analysiere mit Gemini 3.0..."):
                response = model.generate_content(full_context)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Fehler: {e}")
