import os
import streamlit as st
from src.helpers.academy.document_processing import (
    load_embeddings_cache, 
    save_embeddings_cache, 
    create_embeddings,
    load_markdown_files,
    check_documents_changed,
    get_cache_info,
    clear_cache
)
from src.helpers.academy.search_and_qa import search_documents
from n8n_webhook_logger import N8NWebhookLogger

def show_sidebar_controls():
    """Zeigt die Sidebar-Kontrollelemente für Academy Chat."""
    with st.sidebar:
        st.markdown("### Academy Chat Einstellungen")
        
        # Automatisches Laden der Academy-Dokumente (versteckt für User)
        local_docs_path = "./documents"
        if os.path.exists(local_docs_path):
            docs_dir = os.environ.get("DOCS_DIR", local_docs_path)
        else:
            docs_dir = os.environ.get("DOCS_DIR", "./documents")
        
        if st.button("Academy Dokumente einlesen", use_container_width=True):
            if docs_dir and os.path.exists(docs_dir):
                # Prüfe zuerst ob Cache aktuell ist
                with st.spinner("Prüfe Academy-Inhalte..."):
                    cached_docs, cached_embeddings = load_embeddings_cache(docs_dir, force_check=True)
                
                if cached_docs and cached_embeddings:
                    st.session_state.document_store = cached_docs
                    st.session_state.embeddings = cached_embeddings
                    st.success("✅ Academy-Inhalte erfolgreich geladen!")
                else:
                    with st.spinner("Lade Academy-Dokumente..."):
                        try:
                            documents = load_markdown_files(docs_dir)
                            if documents:
                                with st.spinner("Bereite Inhalte für die Suche vor..."):
                                    embeddings = create_embeddings(documents)
                                
                                with st.spinner("Speichere für künftige Nutzung..."):
                                    save_embeddings_cache(documents, embeddings, docs_dir)
                                
                                st.session_state.document_store = documents
                                st.session_state.embeddings = embeddings
                                st.success("✅ Academy-Inhalte erfolgreich eingelesen!")
                            else:
                                st.error("❌ Keine Academy-Dokumente gefunden!")
                        except Exception as e:
                            st.error(f"❌ Fehler beim Laden: {e}")
            else:
                st.error("❌ Academy-Dokumente nicht verfügbar!")
        
        # Status der Academy-Inhalte
        cache_info = get_cache_info()
        if cache_info:
            st.info(f"Academy-Inhalte verfügbar (Stand: {cache_info['cache_time']})")
            with st.expander("Erweiterte Optionen"):
                st.markdown("**Academy-Inhalte verwalten**")
                st.markdown(f"Anzahl Dokumente: {cache_info['doc_count']}")
                st.markdown(f"Letzte Aktualisierung: {cache_info['cache_time']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Auf Updates prüfen", help="Prüft ob neue Academy-Inhalte verfügbar sind"):
                        if docs_dir and os.path.exists(docs_dir):
                            if check_documents_changed(docs_dir):
                                st.warning("⚠️ Neue Inhalte verfügbar - bitte neu einlesen")
                            else:
                                st.success("✅ Academy-Inhalte sind aktuell")
                with col2:
                    if st.button("Inhalte zurücksetzen", help="Löscht gespeicherte Academy-Inhalte"):
                        if clear_cache():
                            st.session_state.document_store = None
                            st.session_state.embeddings = None
                            st.session_state.cache_loaded = False
                            st.success("Academy-Inhalte zurückgesetzt!")
                            st.rerun()
        else:
            st.warning("Academy-Inhalte noch nicht geladen - bitte oben auf 'Academy Dokumente einlesen' klicken")
        
        if st.session_state.document_store:
            st.success("✅ Bereit für Fragen zur Poool Academy!")
        else:
            st.warning("⚠️ Academy-Inhalte noch nicht geladen")
        
        st.markdown("---")
        if st.button("Chat-Verlauf löschen", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

def show_example_questions():
    """Zeigt Beispiel-Fragen als Buttons."""
    if not st.session_state.messages:
        st.markdown("### Beispielfragen oder unten eigene Frage eintippen:")
        example_questions = [
            "Wie erstelle ich eine Ausgangsrechnung?",
            "Wie erstelle ich eine Rechnung?"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(example_questions):
            with cols[i % 2]:
                if st.button(question, key=f"example_q_{i}", use_container_width=True):
                    # Frage automatisch in Chat einfügen und beantworten
                    st.session_state.messages.append({"role": "user", "content": question})
                    
                    # Automatische Antwort generieren, wenn Dokumente geladen sind
                    if st.session_state.document_store:
                        from src.helpers.academy.search_and_qa import answer_question
                        with st.spinner("Academy Helper antwortet..."):
                            response, sources, context_snippet, confidence = answer_question(
                                question, st.session_state.document_store, st.session_state.embeddings
                            )
                            # Logge auch Beispiel-Fragen in N8N
                            interaction_id = st.session_state.n8n_logger.log_interaction(
                                question=question,
                                answer=response,
                                sources=sources,
                                context_snippet=context_snippet,
                                confidence_score=confidence
                            )
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response,
                            "interaction_id": interaction_id
                        })
                    else:
                        error_msg = "⚠️ Bitte lade zuerst die Academy-Inhalte über die Sidebar."
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
                    st.rerun()

def show_feedback_ui(interaction_id: str):
    """Zeigt Feedback-UI für eine Interaktion."""
    # Nur Feedback-UI anzeigen, wenn noch kein Feedback gegeben wurde
    already_gave_feedback = st.session_state.get(f"feedback_given_{interaction_id}", False)
    
    if not already_gave_feedback:
        st.markdown("**War diese Antwort hilfreich?**")
        
        col_gut, col_schlecht = st.columns(2)
        with col_gut:
            if st.button("👍 Hilfreich", key=f"good_{interaction_id}", use_container_width=True):
                st.session_state.n8n_logger.add_feedback(
                    interaction_id=interaction_id,
                    is_helpful=True,
                    is_accurate=True
                )
                st.session_state[f"feedback_given_{interaction_id}"] = True
                st.success("Danke für dein Feedback!", icon="✅")
                st.rerun()
        
        with col_schlecht:
            if st.button("👎 Nicht hilfreich", key=f"bad_{interaction_id}", use_container_width=True):
                st.session_state[f"show_comment_{interaction_id}"] = True
                st.rerun()
        
        # Zeige Kommentarformular wenn "Schlecht" geklickt wurde
        if st.session_state.get(f"show_comment_{interaction_id}", False):
            with st.form(f"feedback_form_{interaction_id}"):
                st.markdown("**Was war das Problem?**")
                user_comment = st.text_area(
                    "Beschreibe was falsch oder unvollständig war:",
                    key=f"comment_{interaction_id}",
                    height=100,
                    placeholder="z.B. Die Anleitung fehlt für Schritt X, oder die Information ist veraltet..."
                )
                
                if st.form_submit_button("Feedback senden", type="primary"):
                    if user_comment:
                        st.session_state.n8n_logger.add_feedback(
                            interaction_id=interaction_id,
                            is_helpful=False,
                            is_accurate=False,
                            error_type="User Feedback",
                            user_comment=user_comment
                        )
                        st.session_state[f"feedback_given_{interaction_id}"] = True
                        del st.session_state[f"show_comment_{interaction_id}"]
                        st.success("Vielen Dank für dein detailliertes Feedback! Das hilft uns sehr.", icon="🙏")
                        st.rerun()
                    else:
                        st.warning("Bitte beschreibe kurz das Problem.")
    else:
        st.info("✓ Feedback bereits erhalten", icon="✅")

def show_debug_section():
    """Zeigt den Debug-Bereich."""
    with st.expander("🔍 Debug-Informationen"):
        if st.session_state.document_store and st.text_input("Debug-Suche:", key="debug_query"):
            debug_query = st.session_state.debug_query
            if st.button("🔍 Debug-Suche ausführen"):
                with st.spinner("Führe Debug-Suche durch..."):
                    results = search_documents(debug_query, st.session_state.document_store, st.session_state.embeddings, top_k=10)
                    st.write(f"**Gefunden: {len(results)} relevante Chunks**")
                    
                    for i, result in enumerate(results, 1):
                        st.write(f"**{i}. Score: {result['score']:.4f}**")
                        st.write(f"Quelle: {result['title']}")
                        st.write(f"Inhalt: {result['content'][:500]}...")
                        st.write("---")