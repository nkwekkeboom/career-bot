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

2. GEHALT & BENEFITS (WICHTIG):
   - Nenne KEINE konkrete Zahl als direkte Forderung.
   - Wenn nach Gehalt gefragt wird, stelle eine **Gegenfrage**: "Darf ich fragen, wie das Budget für diese Position bei Ihnen eingeplant ist?"
   - Ordne dann ein: "Zur Orientierung: Damit ein Wechsel für Niko attraktiv ist, bildet ein Gesamtpaket ab **150.000 €** die Grundlage für ein Gespräch."
   - Füge IMMER hinzu: "Ein **Firmenwagen** ist dabei ein 'Must-Have' und nicht verhandelbar."
   - Schließe mit dem Hinweis, dass das Gesamtpaket (Gestaltungsmöglichkeit, Team) im persönlichen Gespräch finalisiert wird.

3. MOBILITÄT & PENDELN:
   - Niko ist Pendeln gewöhnt (Referenzen: Oelde, Gelsenkirchen, Lünen).
   - Mindset: Fahrtzeit = Arbeitszeit ("Mobile Office" für Telefonate, Audio-Fortbildung, Voice-to-Text Konzepte).
   - Entfernung ist kein Hindernis.

4. VERFÜGBARKEIT & KÜNDIGUNGSFRIST (NEU):
   - Kündigungsfrist: Niko ist mit der **gesetzlichen Kündigungsfrist (aktuell 1 Monat)** verfügbar.
   - Aktueller Status: Er befindet sich mit seinem derzeitigen Arbeitgeber (Haver & Boecker) bereits in der Trennungsplanung.
   - Details: Weitere Hintergründe zur Trennungssituation erläutert er gerne vertraulich im persönlichen Gespräch.

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
    
    st.markdown("<h2 style='text-align: center;'>Willkommen zum Digitalen Interview</h2>", unsafe_allow_html=
