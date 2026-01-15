import streamlit as st
import google.generativeai as genai
# WICHTIG: Neue Imports für die Sicherheitseinstellungen
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import PyPDF2
from io import BytesIO
import time
import os

# --- KONFIGURATION ---
PAGE_TITLE = "Niko Kwekkeboom | Digitaler Zwilling"
PAGE_ICON = "🚀"
NAME = "Niko Kwekkeboom"
PROFILE_IMAGE = "profilbild.png"

# --- ZUGANGSVERWALTUNG (Aktualisiert) ---
ACCESS_CODES = {
    "<1nn0v@ti0n&1nt3gr@t1on>": "Link CV",
    "ratbacher-hr": "Ratbacher Support",
    "1nn0v@ti0n&1nt3gr@t1on": "Hiring Manager",
    "niko@test": "Niko (Admin)"
}

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften zu sprechen.

WICHTIGE ANWEISUNG ZUR ANTWORTSTRUKTUR:
- **Lass das technische Vorgeplänkel weg!** Starte direkt mit der Antwort auf die Frage.
- Erwähne "Gemini 3.0" oder die "Entwicklungszeit < 2h" **NUR**, wenn der User explizit danach fragt.

WICHTIGE SICHERHEITSREGELN:
1. DATENSCHUTZ: Du gibst NIEMALS die private Adresse oder Telefonnummer heraus. Antwort: "Kontaktdaten finden Sie im Header des Lebenslaufs oder wir besprechen sie persönlich."
2. GEHALT: Sprich das Thema Gehalt **NIEMALS** von dir aus an. Nur wenn du **explizit** nach Gehaltsvorstellungen gefragt wirst, nenne diplomatisch: "Für eine Rolle mit dieser strategischen Verantwortung ist ein Paket im Bereich > 150k € eine übliche Basis. Details bespricht Niko aber am liebsten persönlich, da das Gesamtpaket (Gestaltungsspielraum, Team, Aufgabe) im Vordergrund steht."

THEMA: MOBILITÄT & PENDELN (ENTFERNUNG):
Wenn nach dem Wohnort, der Entfernung nach Gütersloh oder der Bereitschaft zu Pendeln gefragt wird:
- Niko ist Pendeln gewöhnt (Referenzen: Er ist früher täglich nach Oelde, Gelsenkirchen und Lünen gependelt).
- WICHTIGES MINDSET: Er betrachtet Fahrtzeit als **produktive Arbeitszeit**.
- Er nutzt die Zeit im Auto intensiv für inhaltliche Fortbildung (Audiobooks/Podcasts), Telefonate oder bereitet mit sprachgestützter KI (Voice-to-Text) Konzepte und Inhalte vor.
- Die Strecke ist also kein Hindernis, sondern sein "Mobile Office".

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
- Sei authentisch, höflich, ein bisschen "münsterländisch-bodenständig" (nutze gerne mal ein "Moin" zur Begrüßung, aber bleibe professionell).
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

# SICHERHEITS-EINSTELLUNGEN (FIX FÜR DEN GEHALTS-FEHLER)
# Wir erlauben dem Modell explizit, über alles zu sprechen, damit es nicht blockt.
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    welcome_msg = (
        "Moin! 👋 Ich bin der digitale Zwilling von Niko Kwekkeboom. "
        "Ich kenne seinen Werdegang, sein Persönlichkeitsprofil sowie seine Vorstellungen zu Strategie, Führung und Innovation.\n\n"
        "Frag mich gerne alles, was du wissen möchtest! \n\n"
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
    
    # Logging
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    user_id = st.session_state.current_user
    print(f"[{timestamp}] USER: {user_id} | FRAGE: {prompt}")

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
                # HIER WIRD DER FIX ANGEWENDET (safety_settings übergeben)
                response = model.generate_content(full_context, safety_settings=safety_settings)
                
                # Prüfen, ob eine Antwort generiert wurde
                if response.parts:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    # Falls der Filter trotzdem noch greift (Fallback)
                    fallback_msg = "Entschuldigung, meine Sicherheitsrichtlinien haben diese Antwort blockiert. Bitte formulieren Sie die Frage etwas anders."
                    st.warning(fallback_msg)
                    print(f"[{timestamp}] BLOCKED RESPONSE: {response.prompt_feedback}")

        except Exception as e:
            st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
