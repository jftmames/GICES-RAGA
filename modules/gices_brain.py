import os
import json
import fitz  # PyMuPDF
import numpy as np
from openai import OpenAI
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

# --- CONFIGURACIÓN ---
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
VECTOR_DB_PATH = Path("rag/knowledge_vectors.json")

def get_embedding(text, model="text-embedding-3-small"):
    if not client: return []
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

# --- 1. CAPACIDAD VISUAL (Con Telemetría) ---
def ingest_pdfs(pdf_dir, progress_callback=None):
    """
    Lee PDFs y vectoriza con barra de progreso en tiempo real.
    """
    knowledge = []
    pdf_path = Path(pdf_dir)
    
    # Si existe memoria previa, la cargamos (puedes comentar esto si quieres forzar relectura)
    if VECTOR_DB_PATH.exists():
        if progress_callback: progress_callback(0.1, "🧠 Cargando memoria existente...")
        try:
            with open(VECTOR_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass

    if not pdf_path.exists():
        return []
    
    # Listamos archivos primero para saber el total
    files = list(pdf_path.glob("*.pdf"))
    total_files = len(files)
    
    if total_files == 0:
        return []
    
    print(f"📂 Indexando {total_files} archivos desde: {pdf_path}")
    
    for idx, f in enumerate(files):
        # --- TELEMETRÍA: Calculamos porcentaje y avisamos a la App ---
        if progress_callback:
            percent = (idx / total_files)
            progress_callback(percent, f"⏳ Procesando ({idx+1}/{total_files}): {f.name}")
        # -------------------------------------------------------------

        try:
            doc = fitz.open(f)
            for i, page in enumerate(doc):
                text = page.get_text().replace("\n", " ").strip()
                if len(text) > 50:
                    vector = get_embedding(text)
                    knowledge.append({
                        "source": f.name,
                        "page": i + 1,
                        "content": text,
                        "embedding": vector
                    })
        except Exception as e:
            print(f"⚠️ Error leyendo {f.name}: {e}")
            
    # Guardar memoria
    if progress_callback: progress_callback(0.9, "💾 Guardando vectores en disco...")
    
    try:
        VECTOR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VECTOR_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando: {e}")

    # Finalizar
    if progress_callback: progress_callback(1.0, "✅ Indexación Completada")

    return knowledge

# --- 2. RECUPERACIÓN SEMÁNTICA (Sin cambios) ---
def retrieve_context(query, knowledge_base=None, k=3):
    if not knowledge_base:
        if VECTOR_DB_PATH.exists():
            with open(VECTOR_DB_PATH, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
        else: return []

    if not client or not knowledge_base: return []

    try:
        query_embedding = get_embedding(query)
        kb_embeddings = [item["embedding"] for item in knowledge_base]
        
        query_vec = np.array(query_embedding).reshape(1, -1)
        kb_matrix = np.array(kb_embeddings)
        
        similarities = cosine_similarity(query_vec, kb_matrix)[0]
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score > 0.3: 
                item = knowledge_base[idx]
                results.append({
                    "source": item["source"],
                    "page": item["page"],
                    "content": item["content"],
                    "score": float(score)
                })
        return results
    except Exception as e:
        print(f"Error retrieval: {e}")
        return []

# --- 3. RAZONAMIENTO (Sin cambios) ---
def deliberative_analysis(data_point, context_chunks, mode="Academic Validation"):
    if not client: return {"narrative": "Error API Key", "compliance_check": "FAIL"}

    evidence_str = "\n\n".join([
        f"- [Fuente: {c['source']} Pág.{c['page']} | Relevancia: {c.get('score',0):.2f}] {c['content'][:800]}..." 
        for c in context_chunks
    ])
    
    prompt = f"""
    Actúa como un auditor experto en normativas de sostenibilidad (CSRD/ESRS/TNFD).
    OBJETIVO: Validar rigurosamente el siguiente dato reportado contra la evidencia normativa.
    DATO A AUDITAR: {json.dumps(data_point)}
    EVIDENCIA NORMATIVA:
    {evidence_str}
    Genera un JSON: {{
        "narrative": "Juicio técnico y conciso (3 frases).",
        "compliance_check": "CUMPLE / RIESGO / NO CUMPLE",
        "citations": ["Lista de archivos"],
        "key_gap": "Brecha principal"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"narrative": f"Error: {e}", "compliance_check": "FAIL"}
