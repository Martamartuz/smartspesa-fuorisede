import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# --- CONFIGURAZIONE SICURA DA STREAMLIT SECRETS ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.8-flash')

# Connessione a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SmartSpesa Fuorisede", page_icon="🥑", layout="wide")

# --- GESTIONE ACCOUNT SEMPLIFICATA ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🥑 SmartSpesa Fuorisede - Accedi")
    st.write("Accedi con la tua email per gestire il tuo frigo, le tue ricette e i preferiti!")
    
    with st.form("form_login"):
        email_input = st.text_input("La tua email")
        password_input = st.text_input("Password", type="password")
        col1, col2 = st.columns(2)
        
        btn_login = col1.form_submit_button("Accedi")
        btn_signup = col2.form_submit_button("Registrati")
        
        if btn_signup and email_input and password_input:
            try:
                response = supabase.auth.sign_up({"email": email_input, "password": password_input})
                st.success("Registrazione completata! Ora puoi effettuare l'accesso.")
            except Exception as e:
                st.error(f"Errore nella registrazione: {e}")
                
        if btn_login and email_input and password_input:
            try:
                response = supabase.auth.sign_in_with_password({"email": email_input, "password": password_input})
                st.session_state.user = response.user.email
                st.rerun()
            except Exception as e:
                st.error(f"Credenziali non valide o errore di login: {e}")
    st.stop()

# --- APP PRINCIPALE (Se l'utente è loggato) ---
st.sidebar.write(f"👤 Benvenuta, **{st.session_state.user}**!")
if st.sidebar.button("Esci (Logout)"):
    st.session_state.user = None
    st.rerun()

st.title("🥑 SmartSpesa Fuorisede - Workspace")

scelta = st.sidebar.selectbox("Navigazione", [
    "📦 Il mio Frigo / Freezer", 
    "📖 Ricettario Comune", 
    "⭐ I miei Preferiti",
    "🍳 Aggiungi Ricetta", 
    "🤖 Genera Menù Intelligente"
])

# Funzioni di caricamento dati
def carica_ricette():
    try:
        return supabase.table("ricette").select("*").execute().data
    except:
        return []

def carica_frigo(email):
    try:
        return supabase.table("inventario_frigo").select("*").eq("user_email", email).execute().data
    except:
        return []

def carica_preferiti(email):
    try:
        res = supabase.table("preferiti_utenti").select("ricetta_id").eq("user_email", email).execute()
        ids = [item["ricetta_id"] for item in res.data]
        if not ids:
            return []
        ricette_fav = supabase.table("ricette").select("*").in_("id", ids).execute()
        return ricette_fav.data
    except:
        return []

if scelta == "📦 Il mio Frigo / Freezer":
    st.header("📦 Cosa hai in Frigo e in Freezer?")
    st.write("Registra quello che hai in casa o rimuovi ciò che hai terminato per evitare sprechi.")
    
    with st.form("form_frigo"):
        ingrediente = st.text_input("Nome ingrediente (es. Mozzarella, Petto di pollo, Zucchine)")
        quantita = st.text_input("Quantità (es. 2 confezioni, 500g)")
        scadenza = st.date_input("Data di scadenza")
        
        submitted = st.form_submit_button("Aggiungi al Frigo")
        if submitted and ingrediente:
            try:
                supabase.table("inventario_frigo").insert({
                    "user_email": st.session_state.user,
                    "ingrediente": ingrediente,
                    "quantita": quantita,
                    "scadenza": str(scadenza)
                }).execute()
                st.success(f"'{ingrediente}' aggiunto con successo al tuo inventario!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nel salvataggio: {e}")
                
    st.subheader("I tuoi alimenti registrati:")
    oggetti_frigo = carica_frigo(st.session_state.user)
    if oggetti_frigo:
        for item in oggetti_frigo:
            col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
            col_a.write(f"🔹 **{item['ingrediente']}**")
            col_b.write(f"Qt: {item['quantita']}")
            col_c.write(f"Scad: {item['scadenza']}")
            
            # Pulsante per rimuovere l'ingrediente dal frigo
            if col_d.button("🗑️", key=f"del_frigo_{item['id']}"):
                try:
                    supabase.table("inventario_frigo").delete().eq("id", item['id']).execute()
                    st.success(f"'{item['ingrediente']}' rimosso dal frigo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante l'eliminazione: {e}")
    else:
        st.info("Il tuo frigo è vuoto al momento.")

elif scelta == "📖 Ricettario Comune":
    st.header("📖 Ricettario della Casa")
    st.write("Sfoglia i piatti della casa e aggiungi quelli che preferisci alla tua lista personale!")
    ricette = carica_ricette()
    preferiti_attuali = [r['id'] for r in carica_preferiti(st.session_state.user)]
    
    if ricette:
        for r in ricette:
            with st.expander(f"{r['titolo']} ({r['categoria']})"):
                st.write(f"**Ingredienti:** {r['ingredienti']}")
                
                is_fav = r['id'] in preferiti_attuali
                if is_fav:
                    if st.button("❌ Rimuovi dai Preferiti", key=f"rem_{r['id']}"):
                        supabase.table("preferiti_utenti").delete().eq("user_email", st.session_state.user).eq("ricetta_id", r['id']).execute()
                        st.success("Rimossa dai preferiti!")
                        st.rerun()
                else:
                    if st.button("⭐ Aggiungi ai Preferiti", key=f"add_{r['id']}"):
                        supabase.table("preferiti_utenti").insert({
                            "user_email": st.session_state.user,
                            "ricetta_id": r['id']
                        }).execute()
                        st.success("Aggiunta ai preferiti!")
                        st.rerun()
    else:
        st.info("Nessuna ricetta nel database.")

elif scelta == "⭐ I miei Preferiti":
    st.header("⭐ Le tue Ricette Preferite")
    st.write("Qui trovi tutti i piatti che hai salvato per consultarli rapidamente quando non sai cosa cucinare.")
    ricette_fav = carica_preferiti(st.session_state.user)
    
    if ricette_fav:
        for r in ricette_fav:
            with st.expander(f"{r['titolo']} ({r['categoria']})"):
                st.write(f"**Ingredienti:** {r['ingredienti']}")
    else:
        st.info("Non hai ancora salvato nessuna ricetta tra i preferiti. Vai nel 'Ricettario Comune' per aggiungerne qualcuna!")

elif scelta == "🍳 Aggiungi Ricetta":
    st.header("🍳 Aggiungi una nuova ricetta al ricettario comune")
    with st.form("form_nuova_ricetta"):
        titolo = st.text_input("Titolo della ricetta (es. Pasta alla Norma)")
        ingredienti_ricetta = st.text_area("Ingredienti principali (separati da virgola)")
        categoria = st.selectbox("Categoria", ["Primo", "Secondo", "Piatto Unico", "Contorno"])
        
        submit_ricetta = st.form_submit_button("Salva Ricetta nel Cloud")
        if submit_ricetta and titolo and ingredienti_ricetta:
            try:
                supabase.table("ricette").insert({
                    "titolo": titolo,
                    "ingredienti": ingredienti_ricetta,
                    "categoria": categoria
                }).execute()
                st.success(f"Evviva! La ricetta '{titolo}' è stata salvata nel cloud per tutte le coinquiline!")
            except Exception as e:
                st.error(f"Errore durante il salvataggio della ricetta: {e}")

elif scelta == "🤖 Genera Menù Intelligente":
    st.header("🤖 Pianificatore di Pasti Intelligente")
    st.write("L'IA analizzerà il tuo frigo personale e selezionerà le ricette migliori per creare il piano e la lista della spesa di ciò che manca.")
    
    giorni = st.slider("Giorni di pianificazione", 1, 7, 5)
    
    frigo_utente = carica_frigo(st.session_state.user)
    ricette_comuni = carica_ricette()
    
    elenco_frigo_str = ", ".join([f"{item['ingrediente']} ({item['quantita']}, scade il {item['scadenza']})" for item in frigo_utente]) if frigo_utente else "Nessun ingrediente registrato."
    elenco_ricette_str = "\n".join([f"- {r['titolo']} (Ingredienti: {r['ingredienti']})" for r in ricette_comuni]) if ricette_comuni else "Nessuna ricetta."
    
    st.write(f"📌 **Stai cucinando usando dal tuo frigo:** {elenco_frigo_str}")
    
    if st.button("Crea Menù e Lista della Spesa Mancante"):
        if not frigo_utente:
            st.warning("Prima di generare il menù, inserisci almeno un ingrediente nella sezione 'Il mio Frigo / Freezer'!")
        else:
            with st.spinner("Sto elaborando il menù perfetto per evitare sprechi..."):
                prompt = f"""
                Sei il sistema intelligente di SmartSpesa Fuorisede.
                Crea un piano di {giorni} giorni utilizzando prioritariamente QUESTI INGREDIENTI PRESENTI NEL FRIGO DELL'UTENTE:
                {elenco_frigo_str}
                
                Le ricette devono essere scelte o ispirate da QUESTO RICETTARIO DELLA CASA:
                {elenco_ricette_str}
                
                Genera:
                1. Una tabella con il menù settimanale (Giorno, Pranzo, Cena).
                2. Una lista della spesa intelligente che elenchi SOLO gli ingredienti che MANCANO rispetto a quelli che l'utente ha già nel frigo per preparare questi piatti.
                """
                try:
                    risposta = model.generate_content(prompt)
                    st.markdown(risposta.text)
                except Exception as e:
                    st.error(f"Errore nella generazione con l'IA: {e}")
