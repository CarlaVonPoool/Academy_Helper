import os
import glob
import re
import hashlib
import json
import pickle
from typing import List
import streamlit as st
from sentence_transformers import SentenceTransformer
import numpy as np

# Cache-Pfad für persistente Speicherung
CACHE_DIR = "./embeddings_store"
EMBEDDINGS_CACHE_FILE = os.path.join(CACHE_DIR, "embeddings_index.pkl")
DOCUMENT_HASH_FILE = os.path.join(CACHE_DIR, "document_hashes.json")

def ensure_cache_dir():
    """Stellt sicher, dass das Cache-Verzeichnis existiert."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def calculate_document_hash(documents):
    """Berechnet einen Hash für alle Dokumente zur Änderungserkennung."""
    content_hash = hashlib.md5()
    for doc in sorted(documents, key=lambda x: x['source']):
        content_hash.update(doc['content'].encode('utf-8'))
        content_hash.update(doc['source'].encode('utf-8'))
    return content_hash.hexdigest()

def save_document_hashes(documents, docs_dir):
    """Speichert Hashes der aktuellen Dokumente."""
    ensure_cache_dir()
    doc_hashes = {}
    for doc in documents:
        file_hash = hashlib.md5(doc['content'].encode('utf-8')).hexdigest()
        doc_hashes[doc['source']] = {
            'hash': file_hash,
            'chunk_id': doc['chunk_id']
        }
    
    hash_data = {
        'docs_dir': docs_dir,
        'document_hashes': doc_hashes,
        'total_hash': calculate_document_hash(documents),
        'total_chunks': len(documents)
    }
    
    with open(DOCUMENT_HASH_FILE, 'w', encoding='utf-8') as f:
        json.dump(hash_data, f, indent=2)

def save_embeddings_cache(documents, embeddings, docs_dir):
    """Speichert Dokumente und Embeddings DAUERHAFT."""
    ensure_cache_dir()
    
    # Speichere Dokument-Hashes für Änderungserkennung
    save_document_hashes(documents, docs_dir)
    
    # Speichere Embeddings und Dokumente
    cache_data = {
        'documents': documents,
        'embeddings': embeddings,
        'docs_dir': docs_dir,
        'total_hash': calculate_document_hash(documents),
        'created_timestamp': os.path.getmtime(docs_dir) if os.path.exists(docs_dir) else 0,
        'version': '2.0'  # Für zukünftige Kompatibilität
    }
    
    with open(EMBEDDINGS_CACHE_FILE, 'wb') as f:
        pickle.dump(cache_data, f)
    
    st.success(f"💾 Embeddings dauerhaft gespeichert in {CACHE_DIR}/")

def check_documents_changed(docs_dir):
    """Prüft ob sich Dokumente seit dem letzten Cache geändert haben."""
    if not os.path.exists(DOCUMENT_HASH_FILE):
        return True  # Kein Hash-File = Neuindexierung nötig
    
    try:
        # Lade gespeicherte Hashes
        with open(DOCUMENT_HASH_FILE, 'r', encoding='utf-8') as f:
            stored_hash_data = json.load(f)
        
        # Lade aktuelle Dokumente für Vergleich
        current_documents = load_markdown_files(docs_dir)
        if not current_documents:
            return True
        
        # Vergleiche Gesamt-Hash
        current_total_hash = calculate_document_hash(current_documents)
        stored_total_hash = stored_hash_data.get('total_hash')
        
        if current_total_hash != stored_total_hash:
            st.info(f"📝 Dokument-Änderungen erkannt - Cache wird aktualisiert")
            return True
        
        return False  # Keine Änderungen
        
    except Exception as e:
        st.warning(f"Hash-Vergleich fehlgeschlagen: {e}")
        return True  # Bei Fehlern sicher neu indexieren

def validate_cache_integrity(cache_data):
    """Überprüft die Integrität der Cache-Daten."""
    required_fields = ['documents', 'embeddings', 'docs_dir', 'version']
    
    for field in required_fields:
        if field not in cache_data:
            return False, f"Fehlendes Feld: {field}"
    
    # Überprüfe Datentypen
    if not isinstance(cache_data['documents'], list):
        return False, "Dokumente sind kein Liste"
    
    if len(cache_data['documents']) == 0:
        return False, "Keine Dokumente im Cache"
    
    # Überprüfe Struktur der Dokumente
    for i, doc in enumerate(cache_data['documents'][:3]):  # Prüfe erste 3
        required_doc_fields = ['content', 'source', 'chunk_id', 'title']
        for field in required_doc_fields:
            if field not in doc:
                return False, f"Dokument {i} fehlt Feld: {field}"
    
    # Überprüfe Embeddings-Form
    try:
        embeddings = cache_data['embeddings']
        if not isinstance(embeddings, tuple) or len(embeddings) != 2:
            return False, "Embeddings haben falsche Struktur"
        
        if not all(isinstance(emb, np.ndarray) for emb in embeddings):
            return False, "Embeddings sind keine NumPy Arrays"
        
        # Überprüfe ob Anzahl Embeddings = Anzahl Dokumente
        if len(embeddings[0]) != len(cache_data['documents']):
            return False, "Mismatch zwischen Embeddings und Dokumenten"
            
    except Exception as e:
        return False, f"Embeddings-Validierung fehlgeschlagen: {e}"
    
    return True, "OK"

def load_embeddings_cache(docs_dir=None, force_check=False):
    """Lädt gespeicherte Embeddings mit Sicherheitsprüfungen."""
    if not os.path.exists(EMBEDDINGS_CACHE_FILE):
        return None, None
    
    try:
        # Sicherheitsprüfung: Dateigröße
        file_size = os.path.getsize(EMBEDDINGS_CACHE_FILE)
        max_size = 500 * 1024 * 1024  # 500MB Limit
        if file_size > max_size:
            st.error(f"❌ Cache-Datei zu groß ({file_size / 1024 / 1024:.1f}MB). Sicherheitshalber nicht geladen.")
            return None, None
        
        # Lade Cache-Daten
        with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Validiere Integrität
        is_valid, validation_msg = validate_cache_integrity(cache_data)
        if not is_valid:
            st.error(f"❌ Cache-Validierung fehlgeschlagen: {validation_msg}")
            return None, None
        
        # Sicherheitsprüfung: Prüfe ob docs_dir sicher ist
        if docs_dir:
            # Verhindere Directory Traversal
            docs_dir = os.path.abspath(docs_dir)
            if not docs_dir.startswith(os.path.abspath(".")):
                st.error("❌ Sicherheitsfehler: Zugriff außerhalb des App-Verzeichnisses nicht erlaubt")
                return None, None
        
        # Wenn kein docs_dir angegeben oder force_check = False, lade einfach
        if not docs_dir or not force_check:
            return cache_data['documents'], cache_data['embeddings']
        
        # Nur bei expliziter Prüfung: Schaue ob Dokumente geändert wurden
        if not check_documents_changed(docs_dir):
            return cache_data['documents'], cache_data['embeddings']
        else:
            return None, None  # Neuindexierung nötig
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Embeddings: {e}")
        # Bei Verdacht auf korrupte Datei: Lösche Cache
        if "pickle" in str(e).lower() or "corrupt" in str(e).lower():
            st.warning("🔧 Cache wird zurückgesetzt...")
            clear_cache()
        return None, None

def get_cache_info():
    """Gibt Informationen über den Cache zurück."""
    if not os.path.exists(EMBEDDINGS_CACHE_FILE):
        return None
    
    try:
        with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
            cache_data = pickle.load(f)
        
        import datetime
        timestamp = cache_data.get('timestamp', 0)
        cache_time = datetime.datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")
        doc_count = len(cache_data.get('documents', []))
        docs_dir = cache_data.get('docs_dir', 'Unbekannt')
        
        return {
            'doc_count': doc_count,
            'cache_time': cache_time,
            'docs_dir': docs_dir
        }
    except:
        return None

def clear_cache():
    """Löscht den Cache."""
    if os.path.exists(EMBEDDINGS_CACHE_FILE):
        os.remove(EMBEDDINGS_CACHE_FILE)
        return True
    return False

def simple_preprocessing(text: str) -> str:
    """Einfache Text-Vorverarbeitung."""
    text = text.lower()
    text = re.sub(r'[^\w\säöüß]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_simple_keywords(text: str) -> List[str]:
    """Einfache Keyword-Extraktion."""
    words = simple_preprocessing(text).split()
    
    stopwords = {
        'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für',
        'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus',
        'er', 'hat', 'dass', 'sie', 'nach', 'wird', 'bei', 'einer', 'um', 'am', 'sind', 'noch',
        'wie', 'einem', 'über', 'einen', 'so', 'zum', 'war', 'haben', 'nur', 'oder', 'aber',
        'vor', 'zur', 'bis', 'mehr', 'durch', 'man', 'sein', 'wurde', 'sei', 'in', 'wenn'
    }
    
    keywords = [word for word in words if len(word) > 3 and word not in stopwords]
    return list(set(keywords))[:10]

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 400) -> List[str]:
    """Teilt Text in Chunks auf."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Versuche bei Satzende zu teilen
        if end < len(text):
            for i in range(end, max(start + overlap, end - 200), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def load_markdown_files(docs_dir: str) -> List[dict]:
    """Lädt Markdown-Dateien aus einem Verzeichnis."""
    documents = []
    
    for file_path in glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Text in Chunks aufteilen
                chunks = chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    documents.append({
                        'content': chunk,
                        'processed_content': simple_preprocessing(chunk),
                        'source': file_path,
                        'chunk_id': i,
                        'title': os.path.basename(file_path).replace('.md', '')
                    })
        except Exception as e:
            st.warning(f"Fehler beim Laden von {file_path}: {e}")
    
    return documents

@st.cache_resource
def load_embedding_model():
    """Lädt das Embedding-Modell."""
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def create_embeddings(documents: List[dict]) -> tuple:
    """Erstellt Embeddings für alle Dokumente."""
    model = load_embedding_model()
    
    # Erstelle Embeddings für Original- und verarbeiteten Text
    texts = [doc['content'] for doc in documents]
    processed_texts = [doc['processed_content'] for doc in documents]
    
    st.write(f"Erstelle Embeddings für {len(texts)} Dokument-Chunks...")
    
    original_embeddings = model.encode(texts, show_progress_bar=True)
    processed_embeddings = model.encode(processed_texts, show_progress_bar=True)
    
    return original_embeddings, processed_embeddings