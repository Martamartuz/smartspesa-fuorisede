import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# --- CONFIGURAZIONE SICURA DA STREAMLIT SECRETS ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Connessione a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def carica_ricette_da_db():
    try:
        response = supabase.table("ricette").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Errore di connessione al database: {e}")
        return []

st.set_page_config(page_title="SmartSpesa Fuorisede", page_icon="🥑", layout="wide")

st.title("🥑 SmartSpesa Fuorisede")
st.write("Il pianificatore di pasti intelligente con ricettario condiviso nel cloud per le coinquiline!")

# Carichiamo le ricette dal database online
ricette_salvate = carica_ricette_da_db()

# Menu laterale per scegliere cosa fare
scelta = st.sidebar.selectbox("Navigazione", ["Genera Menù", "Aggiungi Ricetta alla Casa", "Vedi Ricettario"])

if scelta == "Genera Menù":
    st.header("Pianifica i pasti della settimana")
    
    giorni = st.slider("Per quanti giorni devo pianificare?", 1, 7, 5)
    ingredienti = st.text_input("Quali ingredienti hai già in frigo da consumare urgentemente?")
    budget = st.selectbox("Qual è il tuo budget?", ["Molto Economico", "Medio", "Senza limiti"])
    
    # Prepariamo l'elenco delle ricette dal database
    if ricette_salvate:
        elenco_testo_ricette = "\n".join([f"- {r['titolo']} (Ingredienti: {r['ingredienti']})" for r in ricette_salvate])
    else:
        elenco_testo_ricette = "Nessuna ricetta salvata al momento."

    if st.button("Genera Menù e Lista della Spesa"):
        if not ingredienti:
            st.warning("Inserisci almeno un ingrediente per evitare sprechi!")
        else:
            st.info("Elaborazione del menù in corso...")
            
            prompt = f"""
            Sei il software di gestione pasti per un appartamento di studentesse fuorisede.
            Crea un menù di {giorni} giorni basandoti principalmente su QUESTO RICETTARIO DELLA CASA:
            {elenco_testo_ricette}
            
            Devi assolutamente dare priorità e inserire nel menù i piatti del ricettario che usano questi ingredienti in scadenza: {ingredienti}.
            Budget: {budget}.
            
            Restituisci ESATTAMENTE:
            1. Tabella Markdown con il menù (Giorno, Pranzo, Cena).
            2. Lista della spesa con caselle di controllo divisa per reparti.
            """
            
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Errore tecnico o limite di quota raggiunto. Riprova tra poco: {e}")

elif scelta == "Aggiungi Ricetta alla Casa":
    st.header("Aggiungi una nuova ricetta al ricettario comune 🍳")
    with st.form("form_ricetta"):
        nuovo_titolo = st.text_input("Nome del piatto (es. Pasta tonno e limone)")
        nuovi_ingredienti = st.text_area("Ingredienti principali (separati da virgola)")
        nuova_categoria = st.selectbox("Categoria", ["Primo", "Secondo", "Piatto Unico", "Contorno"])
        
        submit = st.form_submit_button("Salva nel Ricettario Cloud")
        if submit and nuovo_titolo and nuovi_ingredienti:
            try:
                # Salvataggio diretto nel database online di Supabase
                supabase.table("ricette").insert({
                    "titolo": nuovo_titolo,
                    "ingredienti": nuovi_ingredienti,
                    "categoria": nuova_categoria
                }).execute()
                st.success(f"Evviva! '{nuovo_titolo}' è stata salvata per sempre nel cloud per tutte le coinquiline!")
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")

elif scelta == "Vedi Ricettario":
    st.header("📖 Il Ricettario della Casa (Cloud)")
    st.write("Ecco tutti i piatti salvati da te e dalle tue coinquiline in tempo reale:")
    if ricette_salvate:
        for i, r in enumerate(ricette_salvate):
            with st.expander(f"{i+1}. {r['titolo']} ({r['categoria']})"):
                st.write(f"**Ingredienti:** {r['ingredienti']}")
    else:
        st.info("Il ricettario è ancora vuoto. Aggiungi la prima ricetta dalla sezione dedicata!")
