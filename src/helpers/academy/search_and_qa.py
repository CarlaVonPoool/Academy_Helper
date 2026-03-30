import os
from typing import List, Tuple
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
from .document_processing import load_embedding_model, simple_preprocessing, extract_simple_keywords

def search_documents(query: str, document_store: List[dict], embeddings: tuple, top_k: int = 40) -> List[dict]:
    """Sucht in den Dokumenten."""
    if document_store is None or embeddings is None:
        return []
    
    model = load_embedding_model()
    
    # Verschiedene Query-Varianten
    queries = [query]
    queries.append(simple_preprocessing(query))
    
    keywords = extract_simple_keywords(query)
    if keywords:
        queries.append(" ".join(keywords[:5]))
    
    all_results = []
    seen_docs = set()
    
    for q in queries:
        query_embedding = model.encode([q])
        
        # Suche in Original- und verarbeiteten Embeddings
        orig_similarities = cosine_similarity(query_embedding, embeddings[0])[0]
        proc_similarities = cosine_similarity(query_embedding, embeddings[1])[0]
        
        # Kombiniere die Scores
        combined_similarities = (orig_similarities + proc_similarities) / 2
        
        # Top Ergebnisse für diese Query
        top_indices = np.argsort(combined_similarities)[::-1][:top_k]
        
        for idx in top_indices:
            doc_hash = hash(document_store[idx]['content'][:100])
            if doc_hash not in seen_docs:
                result = document_store[idx].copy()
                result['score'] = float(combined_similarities[idx])
                all_results.append(result)
                seen_docs.add(doc_hash)
    
    # Sortiere nach Score
    all_results.sort(key=lambda x: x['score'], reverse=True)
    return all_results[:top_k]

def answer_question(question: str, document_store: List[dict], embeddings: tuple) -> Tuple[str, List[str], str, float]:
    """Beantwortet eine Frage."""
    if document_store is None:
        return "Index wurde noch nicht initialisiert. Bitte lade zuerst Dokumente.", [], "", 0.0
    
    # Suche relevante Dokumente
    results = search_documents(question, document_store, embeddings)
    
    if not results:
        return "Keine relevanten Dokumente gefunden.", [], "", 0.0
    
    # Gruppiere nach Quellen
    sources = set()
    source_to_chunks = {}
    
    for doc in results:
        source = doc['source']
        title = doc['title']
        sources.add(source)
        
        if title not in source_to_chunks:
            source_to_chunks[title] = []
        source_to_chunks[title].append(doc['content'])
    
    # Erstelle Kontext
    context_parts = []
    for title, chunks in source_to_chunks.items():
        combined_content = "\n\n".join(chunks)
        context_parts.append(f"=== Dokument: {title} ===\n{combined_content}")
    
    context = "\n\n".join(context_parts)
    source_list = "\n".join([f"- {os.path.basename(s).replace('.md', '')}" for s in sources])
    
    # Claude API aufrufen
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Fehler: ANTHROPIC_API_KEY Umgebungsvariable ist nicht gesetzt.", [], "", 0.0
    
    client = anthropic.Anthropic(api_key=api_key)
    
    system_prompt = """Du bist ein Experten-Assistent. Analysiere ALLE bereitgestellten Dokumente gründlich.

ANALYSEPROZESS:
1. Lies ALLE Dokumente vollständig durch
2. Identifiziere alle relevanten Informationen zur Frage
3. Verknüpfe Informationen aus verschiedenen Dokumenten
4. Erstelle eine umfassende, vollständige Antwort

ANTWORTSTRUKTUR:
1. Vollständige Beantwortung der Frage
2. Praktische Schritte mit KOMPLETTEN Navigationspfaden
3. Alle relevanten Details aus ALLEN Dokumenten
4. Übersichtliche Struktur mit Überschriften

FORMATIERUNG VON UI-ELEMENTEN:
- Alle klickbaren Buttons, Menüs und Auswahlfelder in Backticks setzen: `Button Name`
- Navigationspfade mit Pfeilen: `Buchhaltung` → `Ausgangsrechnung` → `Wiederkehrende`
- Eingabefelder und Optionen: `"Monatlich"` oder `"Jährlich"`
- Wichtige UI-Elemente: **`Speichern`** (fett + Backticks)

BEISPIELE:
- "Klicken Sie auf `+ Kontakt`"
- "Wählen Sie `"Monatlich"` aus"
- "Navigieren Sie zu `CRM` → `Adressbuch` → `Neuer Kontakt`"
- "Betätigen Sie die Schaltfläche **`Rechnung erstellen`**"

QUELLENANGABE:
Füge am Ende hinzu:
"## Quellen
Die Informationen stammen aus folgenden Dokumenten:
[HIER LISTE DER VERWENDETEN QUELLEN]"

KRITISCH: Denke dir NIE etwas aus! Nutze NUR das Wissen aus den bereitgestellten Dokumenten!"""
    
    try:
        message = client.messages.create(
            max_tokens=4096,
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Kontext aus mehreren Dokumenten:\n\n{context}\n\n---\n\nFrage: {question}\n\nVerfügbare Quellen:\n{source_list}"}
            ]
        )
        answer_text = message.content[0].text
        # Berechne Konfidenz basierend auf Anzahl gefundener Dokumente
        confidence = min(len(results) / 10.0, 1.0) if results else 0.0
        return answer_text, [os.path.basename(s).replace('.md', '') for s in sources], context[:500], confidence
    except Exception as e:
        return f"Fehler bei der Antwortgenerierung: {e}", [], "", 0.0