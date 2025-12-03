import os
import json
import fitz  # PyMuPDF
import numpy as np
from openai import OpenAI
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

# --- CONFIGURACIÓN ---
# Intenta obtener la clave de las variables de entorno o secretos
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# Ruta para persistencia simple de vectores (Memoria a largo plazo)
VECTOR_DB_PATH = Path("rag/knowledge_vectors.json")

def get_embedding(text, model="text-embedding-3-small"):
    """Genera el vector numérico para un texto usando OpenAI."""
    if not client:
        return []
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

# --- 1. CAPACIDAD VISUAL Y MEMORIZACIÓN (Ingesta + Embeddings) ---
def ingest_pdfs(pdf_dir):
    """
    Lee PDFs, extrae texto y lo convierte en vectores (embeddings).
    Guarda el resultado en un JSON local para no recalcular siempre.
    """
    knowledge = []
    pdf_path = Path(pdf_dir)
    
    # Si ya existe una base de vectores guardada, la cargamos para ahorrar costes
    # (En producción real, aquí verificaríamos si hay PDFs nuevos)
    if VECTOR_DB_PATH.exists():
        print(f"🧠 Cargando memoria vectorial existente desde {VECTOR_DB_PATH}")
        try:
            with open(VECTOR_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando memoria vectorial: {e}. Reindexando...")

    if not pdf_path.exists():
        print("❌ No se encontró el directorio de PDFs.")
        return []
    
    print(f"📂 Indexando y vectorizando PDFs desde: {pdf_path}")
    
    for f in pdf_path.glob("*.pdf"):
        try:
            doc = fitz.open(f)
            for i, page in enumerate(doc):
                text = page.get_text().replace("\n", " ").strip()
                # Solo procesamos párrafos con contenido sustancial (>50 caracteres)
                if len(text) > 50:
                    print(f"   ...Vectorizando pág {i+1} de {f.name}")
                    vector = get_embedding(text)
                    
                    # Estructura de conocimiento enriquecida
                    knowledge.append({
                        "source": f.name,
                        "page": i + 1,
                        "content": text,
                        "embedding": vector
                    })
        except Exception as e:
            print(f"⚠️ Error leyendo {f.name}: {e}")
            
    # Guardamos la memoria vectorial en disco
    try:
        VECTOR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VECTOR_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        print("💾 Memoria vectorial guardada exitosamente.")
    except Exception as e:
        print(f"⚠️ No se pudo guardar la memoria vectorial: {e}")

    return knowledge

# --- 2. RECUPERACIÓN SEMÁNTICA (Búsqueda Vectorial) ---
def retrieve_context(query, knowledge_base=None, k=3):
    """
    Busca los fragmentos más relevantes usando Similitud de Coseno.
    Entiende el significado, no solo las palabras exactas.
    """
    # Si no nos pasan la base, intentamos cargarla del disco
    if not knowledge_base:
        if VECTOR_DB_PATH.exists():
            with open(VECTOR_DB_PATH, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
        else:
            return []

    if not client or not knowledge_base:
        return []

    # 1. Vectorizar la pregunta del usuario
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        print(f"Error generando embedding de consulta: {e}")
        return []

    # 2. Calcular similitud con cada fragmento de la base
    # Preparamos matrices para cálculo rápido con numpy
    try:
        kb_embeddings = [item["embedding"] for item in knowledge_base]
        
        # Convertimos a arrays de numpy
        query_vec = np.array(query_embedding).reshape(1, -1)
        kb_matrix = np.array(kb_embeddings)
        
        # Cálculo de Similitud de Coseno
        similarities = cosine_similarity(query_vec, kb_matrix)[0]
        
        # 3. Obtener los índices de los mejores resultados
        # argsort ordena de menor a mayor, tomamos los últimos k e invertimos
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            item = knowledge_base[idx]
            score = similarities[idx]
            # Opcional: Filtrar si la similitud es muy baja (ruido)
            if score > 0.3: 
                results.append({
                    "source": item["source"],
                    "page": item["page"],
                    "content": item["content"],
                    "score": float(score) # Para debug
                })
        
        return results

    except Exception as e:
        print(f"⚠️ Error en cálculo vectorial: {e}")
        return []

# --- 3. CAPACIDAD DE RAZONAMIENTO (Sin cambios mayores, solo uso) ---
def deliberative_analysis(data_point, context_chunks, mode="Academic Validation"):
    """Genera el Acta de Razonamiento comparando el dato con la norma recuperada."""
    
    if not client:
        return {
            "narrative": "Error: No se detectó OPENAI_API_KEY.",
            "compliance_check": "ERROR",
            "citations": []
        }

    # Formatear evidencia con puntuación de relevancia
    evidence_str = "\n\n".join([
        f"- [Fuente: {c['source']} Pág.{c['page']} | Relevancia: {c.get('score',0):.2f}] {c['content'][:800]}..." 
        for c in context_chunks
    ])
    
    prompt = f"""
    Actúa como un auditor experto en normativas de sostenibilidad (CSRD/ESRS/TNFD).
    
    OBJETIVO: Validar rigurosamente el siguiente dato reportado contra la evidencia normativa.
    
    DATO A AUDITAR: {json.dumps(data_point)}
    
    EVIDENCIA NORMATIVA RECUPERADA (Contexto Real):
    {evidence_str}
    
    INSTRUCCIONES:
    1. Basa tu juicio ÚNICAMENTE en la evidencia proporcionada arriba.
    2. Si la evidencia no menciona reglas específicas para este dato, indícalo claramente.
    3. Verifica criterios de integridad (ej: permanencia, adicionalidad en créditos).
    
    Genera un JSON:
    {{
        "narrative": "Juicio técnico y conciso (3 frases).",
        "compliance_check": "CUMPLE / RIESGO / NO CUMPLE / NO EVIDENCIA",
        "citations": ["Lista exacta de archivos PDF usados"],
        "key_gap": "Brecha principal detectada o 'Ninguna'"
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
        return {"narrative": f"Error en deliberación: {e}", "compliance_check": "FAIL"}
