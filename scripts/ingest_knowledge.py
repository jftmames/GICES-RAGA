import json
import os
import fitz  # Requiere instalar: pip install pymupdf
from pathlib import Path

# Configuración
KB_DIR = Path("rag/knowledge_base")
INDEX_FILE = Path("rag/index.jsonl")

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if len(text) > 100:  # Ignorar páginas casi vacías
            chunks.append({
                "page": i + 1,
                "content": text.replace("\n", " ") # Limpieza básica
            })
    return chunks

def main():
    if not KB_DIR.exists():
        print(f"Error: No existe el directorio {KB_DIR}")
        return

    knowledge_base = []
    
    print(f"🔄 Iniciando ingesta de conocimiento desde {KB_DIR}...")
    
    files = list(KB_DIR.glob("*.pdf"))
    for pdf_file in files:
        print(f"   📖 Leyendo: {pdf_file.name}")
        chunks = extract_text_from_pdf(pdf_file)
        
        for chunk in chunks:
            # Formato compatible con RAGA-MVP
            entry = {
                "id": f"{pdf_file.name}_P{chunk['page']}",
                "title": f"{pdf_file.stem} - Pág {chunk['page']}",
                "source": pdf_file.name,
                "jurisdiction": "EU", # Etiqueta académica
                "snippet": chunk['content']
            }
            knowledge_base.append(entry)

    # Guardar el índice
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        for entry in knowledge_base:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"✅ Ingesta completada. {len(knowledge_base)} fragmentos indexados en {INDEX_FILE}")

if __name__ == "__main__":
    main()
