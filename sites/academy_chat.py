import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from n8n_webhook_logger import N8NWebhookLogger
from src.components.academy_chat.ui import (
    show_sidebar_controls, 
    show_example_questions, 
    show_feedback_ui, 
    show_debug_section
)
from src.helpers.academy.document_processing import load_embeddings_cache
from src.helpers.academy.search_and_qa import answer_question

load_dotenv()

st.set_page_config(
    page_title="Academy Chat - Poool Academy Helper", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für Poool Styling
st.markdown("""
<style>
    /* Poool Farbschema */
    :root {
        --poool-primary: #1a237e;
        --poool-secondary: #3949ab;
        --poool-accent: #00bcd4;
        --poool-light: #e8eaf6;
        --poool-dark: #0d1421;
    }
    
    /* Text color for dark theme */
    .stMarkdown, .stText, p, div {
        color: white !important;
    }
    
    /* Chat Interface */
    .stChatMessage {
        background: #2b2b2b;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
    }
    
    /* Main content background */
    .main .block-container {
        background-color: #1e1e1e;
        color: white;
    }
    
    /* App background */
    .stApp {
        background-color: #1e1e1e;
    }
    
    /* Buttons - dezente Farben */
    .stButton > button {
        background: #4a4a4a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #5a5a5a;
        transform: translateY(-1px);
    }
    
    /* Success/Warning Messages */
    .stSuccess {
        background: linear-gradient(135deg, #4caf50, #8bc34a);
        color: white;
        border-radius: 8px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #ff9800, #ffc107);
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'document_store' not in st.session_state:
    st.session_state.document_store = None
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'cache_loaded' not in st.session_state:
    st.session_state.cache_loaded = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if 'n8n_logger' not in st.session_state:
    # N8N Webhook URL aus Environment/Secrets - fallback auf lokalen N8N
    n8n_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/feedback")
    st.session_state.n8n_logger = N8NWebhookLogger(n8n_url)

def auto_load_cache_if_available():
    """Lädt automatisch Cache beim App-Start - IMMER wenn vorhanden."""
    if not st.session_state.cache_loaded and st.session_state.document_store is None:
        # Versuche IMMER zuerst den dauerhaften Cache zu laden
        cached_docs, cached_embeddings = load_embeddings_cache()  # Ohne force_check
        
        if cached_docs and cached_embeddings:
            st.session_state.document_store = cached_docs
            st.session_state.embeddings = cached_embeddings
        
        st.session_state.cache_loaded = True

# Automatisch Cache laden, falls verfügbar
auto_load_cache_if_available()

# Page title
st.title("📚 Academy Chat")
st.markdown("Academy Helper - unterstützt dich bei Fragen zur Poool Software basierend auf der Poool Academy. Aktuell noch in der Beta-Version und ggf. fehleranfällig")

# Status Indicator und Controls im Main Chat
col_status, col_action = st.columns([3, 1])

with col_status:
    if st.session_state.document_store:
        st.success("✅ Dateien sind indexiert - Du kannst Fragen stellen!", icon="✅")
    else:
        st.warning("❌ Dateien sind noch nicht indexiert - Bitte auf das X klicken um zu indexieren", icon="❌")

with col_action:
    if st.session_state.document_store:
        st.markdown("<div style='text-align: center; font-size: 24px; color: green;'>✅</div>", unsafe_allow_html=True)
    else:
        if st.button("❌", help="Klicken um Academy-Inhalte zu indexieren", key="index_btn"):
            local_docs_path = "./documents"
            if os.path.exists(local_docs_path):
                docs_dir = os.environ.get("DOCS_DIR", local_docs_path)
            else:
                docs_dir = os.environ.get("DOCS_DIR", "./documents")
                
            if docs_dir and os.path.exists(docs_dir):
                from src.helpers.academy.document_processing import load_embeddings_cache, load_markdown_files, create_embeddings, save_embeddings_cache
                
                with st.spinner("Indexiere Academy-Inhalte..."):
                    try:
                        # Prüfe zuerst Cache
                        cached_docs, cached_embeddings = load_embeddings_cache(docs_dir, force_check=True)
                        
                        if cached_docs and cached_embeddings:
                            st.session_state.document_store = cached_docs
                            st.session_state.embeddings = cached_embeddings
                        else:
                            # Lade und erstelle neue Embeddings
                            documents = load_markdown_files(docs_dir)
                            if documents:
                                embeddings = create_embeddings(documents)
                                save_embeddings_cache(documents, embeddings, docs_dir)
                                st.session_state.document_store = documents
                                st.session_state.embeddings = embeddings
                            else:
                                st.error("❌ Keine Academy-Dokumente gefunden!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Fehler beim Indexieren: {e}")
            else:
                st.error("❌ Academy-Dokumente nicht verfügbar!")

st.markdown("---")

# Show sidebar controls (now hidden/minimized)
# show_sidebar_controls()

# Show example questions if no messages yet
show_example_questions()

# Chat Messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Zeige Feedback-Buttons für Assistant-Antworten mit interaction_id
        if message["role"] == "assistant" and "interaction_id" in message:
            interaction_id = message["interaction_id"]
            show_feedback_ui(interaction_id)

# Chat input
if prompt := st.chat_input("Stelle deine Frage zum Poool Academy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if st.session_state.document_store:
        with st.chat_message("assistant"):
            with st.spinner("Suche nach relevanten Informationen..."):
                response, sources, context_snippet, confidence = answer_question(
                    prompt, st.session_state.document_store, st.session_state.embeddings
                )
                
                # Logge die Interaktion in N8N
                interaction_id = st.session_state.n8n_logger.log_interaction(
                    question=prompt,
                    answer=response,
                    sources=sources,
                    context_snippet=context_snippet,
                    confidence_score=confidence
                )
                
            st.markdown(response)
            
            # Zeige Feedback-Buttons SOFORT unter der Antwort
            show_feedback_ui(interaction_id)
        
        # Speichere die Nachricht mit interaction_id für späteres Feedback
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "interaction_id": interaction_id
        })
    else:
        with st.chat_message("assistant"):
            error_msg = "⚠️ Bitte lade zuerst die Academy-Inhalte über die Sidebar."
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Debug section
show_debug_section()