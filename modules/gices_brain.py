import os
import json
import fitz  # PyMuPDF
from openai import OpenAI
from pathlib import Path

# Cliente OpenAI (tomará la clave de los secretos de Streamlit)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 1. EL LECTOR (RAGA EYES)
def ingest_pdfs(pdf_dir):
    """Convierte tus PDFs académicos en texto plano para la IA"""
    knowledge = []
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists(): return []
    
    for f in pdf_path.glob("*.pdf"):
        doc = fitz.open(f)
        for i, page in enumerate(doc):
            text = page.get_text().replace("\n", " ")
            if len(text) > 50:
                knowledge.append(f"[Fuente: {f.name} - Pág {i+1}] {text[:800]}...") # Chunking simple
    return knowledge

def retrieve_context(query, knowledge_base, k=5):
    """Busca los fragmentos más relevantes para la query"""
    # Búsqueda semántica simplificada (por palabras clave) para no usar base vectorial compleja en MVP
    scored = []
    query_terms = set(query.lower().split())
    for chunk in knowledge_base:
        score = sum(1 for term in query_terms if term in chunk.lower())
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:k]]

# 2. EL PENSADOR (DELIBERATIVE ENGINE)
def deliberative_analysis(data_point, context_chunks, mode="Academic Validation"):
    """Genera el Acta de Razonamiento"""
    evidence_str = "\n\n".join(context_chunks)
    
    prompt = f"""
    Actúa como un analista experto en {mode}.
    Analiza este DATO REPORTADO: {json.dumps(data_point)}
    
    Usa OBLIGATORIAMENTE esta EVIDENCIA NORMATIVA (Tus PDFs):
    {evidence_str}
    
    Genera un JSON con este formato:
    {{
        "narrative": "Tu análisis crítico de 1 párrafo explicando si cumple la normativa.",
        "compliance_check": "CUMPLE / RIESGO / NO CUMPLE",
        "citations": ["Lista exacta de los PDFs citados"],
        "ethical_flag": "True si hay riesgo de greenwashing",
        "reasoning_trace": ["Paso 1: Análisis dato", "Paso 2: Contraste con Ley Restauración", "Paso 3: Conclusión"]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o", # O gpt-3.5-turbo
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
