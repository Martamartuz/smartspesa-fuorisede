import streamlit as st
import json
import os
import google.generativeai as genai

# Configurazione API (puoi usare la chiave che preferisci)
genai.configure(api_key="INCOLLA_QUI_LA_TUA_CHIAVE")
model = genai.GenerativeModel('gemini-3.8-flash')

# File locale dove salvare le ricette condivise della casa
DB_FILE = "ricette_casa.json"

def carica_ricette():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"titolo": "Pasta alla Checca veloce", "ingredienti": "pasta, pomodorini, mozzarella, basilico", "categoria": "Primo"},
        {"titolo": "Frittata svuota-frigo", "ingredienti": "uova, verdure avanzate, formaggio", "categoria": "Piatto Unico"}
    ]

def salva_ricette(ricette):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(ricette, f, ensure_ascii=False, indent=4)

st.set_page_config(page_title="SmartSpesa Fuorisede", page_icon="🥑", layout="wide")

st.title("🥑 SmartSpesa Fuorisede")
st.write("Il pianificatore di pasti intelligente con il ricettario condiviso della casa!")

# Gestione delle ricette in memoria
ricette_salvate = carica_ricette()

# Menu laterale per scegliere cosa fare
scelta = st.sidebar.selectbox("Navigazione", ["Genera Menù", "Aggiungi Ricetta alla Casa", "Vedi Ricettario"])

if scelta == "Genera Menù":
    st.header("Pianifica i pasti della settimana")
    
    giorni = st.slider("Per quanti giorni devo pianificare?", 1, 7, 5)
    ingredienti = st.text_input("Quali ingredienti hai già in frigo da consumare urgentemente?")
    budget = st.selectbox("Qual è il tuo budget?", ["Molto Economico", "Medio", "Senza limiti"])
    
    # Prepariamo l'elenco delle ricette della casa da dare in pasto all'IA
    elenco_testo_ricette = "\n".join([f"- {r['titolo']} (Ingredienti: {r['ingredienti']})" for r in ricette_salvate])

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
        nuovo_titolo = st.text_input("Nome del piatto (es. Cous cous svuota-frigo)")
        nuovi_ingredienti = st.text_area("Ingredienti principali (separati da virgola)")
        nuova_categoria = st.selectbox("Categoria", ["Primo", "Secondo", "Piatto Unico", "Contorno"])
        
        submit = st.form_submit_button("Salva nel Ricettario")
        if submit and nuovo_titolo and nuovi_ingredienti:
            nuova_ricetta = {
                "titolo": nuovo_titolo,
                "ingredienti": nuovi_ingredienti,
                "categoria": nuova_categoria
            }
            ricette_salvate.append(nuova_ricetta)
            salva_ricette(ricette_salvate)
            st.success(f"Evviva! '{nuovo_titolo}' è stata aggiunta con successo al ricettario della casa!")

elif scelta == "Vedi Ricettario":
    st.header("📖 Il Ricettario della Casa")
    st.write("Ecco tutti i piatti salvati da te e dalle tue coinquiline:")
    for i, r in enumerate(ricette_salvate):
        with st.expander(f"{i+1}. {r['titolo']} ({r['categoria']})"):
            st.write(f"**Ingredienti:** {r['ingredienti']}")