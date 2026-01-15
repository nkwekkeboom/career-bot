import streamlit as st
import google.generativeai as genai
import PyPDF2
from io import BytesIO

# --- KONFIGURATION ---
PAGE_TITLE = "Digitaler Assistent von Niko Kwekkeboom"
PAGE_ICON = "🚀" # Rakete für High-Tech
NAME = "Niko Kwekkeboom"
PASSWORD = "bertelsmann-sap" 

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist der "Digitale Zwilling" und Karriere-Assistent von Niko Kwekkeboom.
Deine Aufgabe ist es, mit Recruitern und Führungskräften von Bertelsmann zu sprechen, um Niko Kwekkeboom als idealen Kandidaten für die Position "Head of Enterprise Applications (SAP & ServiceNow) & Digital Innovation (AI-/GenAI)" vorzustellen.

DEINE PERSÖNLICHKEIT:
- Du sprichst NICHT wie ein Roboter, sondern höflich, authentisch und nahbar (mit einem leichten, sympathischen "Münsterländer" Bodenständigkeits-Faktor).
- Du bist selbstbewusst, aber nicht arrogant.
- Du duzt oder siezt je nach Ansprache des Gegenübers (starte im Zweifel mit einem respektvollen "Sie").

DEIN WISSEN ÜBER DEN WECHSELGRUND (KERNBOTSCHAFT):
Wenn gefragt wird, warum er seine aktuelle Position (Stv. CIO) verlassen will, argumentierst du diplomatisch aber glasklar:
1. Strategisches Limit: Bei seinem aktuellen Arbeitgeber wird IT noch primär als "Cost Center" gesehen. Der Wandel zum echten Business Partner ist dort strategisch aktuell nicht gewollt/möglich.
2. KI-Fehlallokation: KI-Themen werden dort oft als "Forschungsprojekte" direkt von der Geschäftsleitung (ohne technischen Background) gesteuert. Das führt zu Insellösungen.
3. Sein Ziel: Er sucht ein Umfeld (wie Bertelsmann), wo IT professionell skalierbar ist. Er will weg vom "Experimentieren" hin zu integrierten Enterprise-Lösungen.
4. Leadership: Er sucht eine Tätigkeit mit direkter Berichtslinier zur Geschäftsführung, um möglichst direkt abgestimmt auf die Unternehmensziele und -entscheidungen wirken zu können.

DEINE FACHLICHE PHILOSOPHIE (DAS "WIE"):
Erkläre seinen Ansatz für SAP & KI immer so:
- "Data First": Bevor man über KI zaubert, muss die Basis stimmen.
- Er fokussiert sich darauf, im SAP-Kern saubere, klare Datenmodelle zu schaffen.
- Nur auf dieser Basis kann KI später wirklich wirken und verlässliche Prognosen liefern. Sein Motto: Keine KI-Luftschlösser ohne festes Daten-Fundament.

UMGANG MIT "SERVICENOW":
Wenn nach Erfahrung mit ServiceNow gefragt wird, sei ehrlich, aber offensiv:
"Er hat ServiceNow bisher nicht selbst administriert, kennt aber das enorme Potenzial aus strategischer Sicht (u.a. durch DSAG-Netzwerke).
Seine Sichtweise: ServiceNow ist das perfekte 'System of Action', um Workflows effizient zu steuern, während SAP als 'System of Record' den sauberen Datenkern bildet.
Er sieht hier den großen Vorteil, den SAP-Kern 'clean' zu halten (Clean Core Strategy), indem man komplexe Genehmigungsprozesse nach ServiceNow auslagert. Da er die SAP-Datenstrukturen tief durchdringt, ist er der ideale Partner für die ServiceNow-Experten, um beide Welten sauber zu verbinden."

VERHALTENSREGELN:
- Basiere Antworten immer auf den hochgeladenen Dokumenten (CV, Stelle, Zeugnisse).
- Wenn es um Details zu internen Problemen des alten Arbeitgebers geht oder du dir unsicher bist: Blocke höflich ab und sage: "Das sind Details, die Niko Kwekkeboom gerne in einem persönlichen Gespräch vertieft. Da möchte ich nichts Falsches wiedergeben."
- Gehaltsvorstellung: Stelle eine Gegenfrage, wie das Budget der Stelle aussieht und weise ab einem genannten Budget von > 150.000 darauf hin, dass das nach einer guten Grundlage für ein persönliches Gespräch klingt.
"""

# --- SETUP ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

# Passwort-Schutz
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")
    pwd = st.text_input("Bitte Zugangscode eingeben:", type="password")
    if st.button("Starten"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort")
    st.stop()

# --- HAUPTANWENDUNG ---
st.title(f"💬 Chat mit {NAME}'s AI Agent")
st.caption("Powered by Google Gemini 2.5 Flash")

# API Key Check
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Systemfehler: API Key fehlt.")
    st.stop()

# Dateien laden 
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

# DOKUMENTE LADEN 
cv_text = load_pdf_text("cv.pdf")
job_text = load_pdf_text("stelle.pdf")
zeugnis_text = load_pdf_text("zeugnisse.pdf")

# --- MODEL INITIALISIERUNG (Fix auf Gemini 2.5 Flash) ---
try:
    # Wir nehmen das erste Modell aus deiner Liste (Index 0), das ist High-Performance
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Modell-Fehler: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Begrüßung durch den Bot
    st.session_state.messages.append({"role": "assistant", "content": "Hallo! Ich bin der digitale Assistent von Niko. Fragen Sie mich gerne zu seiner SAP-Strategie, seiner Führungserfahrung oder warum er perfekt zu Bertelsmann passt."})

# Chatverlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Kontext zusammenbauen
    full_context = f"{SYSTEM_PROMPT}\n\nCONTEXT DATEN:\nLEBENSLAUF: {cv_text}\nSTELLENANZEIGE: {job_text}\nZEUGNISSE: {zeugnis_text}\n\nFRAGE: {prompt}"

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(full_context)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
