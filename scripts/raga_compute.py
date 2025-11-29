import json
import sys
from pathlib import Path

# Añadir raíz al path para importar modules
sys.path.append(str(Path(__file__).parent.parent))
from modules.gices_brain import ingest_pdfs, retrieve_context, deliberative_analysis

DATA_DIR = Path("data/normalized")
RAGA_DIR = Path("raga")
KB_DIR = Path("rag/knowledge_base")

def main():
    RAGA_DIR.mkdir(exist_ok=True, parents=True)
    
    # 1. Cargar Conocimiento (Fase 0)
    print("📚 Leyendo biblioteca académica (PDFs)...")
    kb = ingest_pdfs(KB_DIR)
    print(f"   - {len(kb)} fragmentos de normativa procesados.")

    # 2. Cargar Datos (Fase 1)
    # Simulamos que leemos el dato de Biodiversidad (E4)
    # En tu demo real, asegúrate de tener data/normalized/biodiversity_2024.json
    # Si no existe, creamos uno en memoria para la demo
    biodiv_data = {
        "id": "E4-5",
        "value": 50,
        "unit": "hectareas",
        "project": "Nature Credit - Amazonia Reforest",
        "risk": "High"
    }
    
    # 3. Deliberación (Fase 3 - Integración)
    print("🧠 Iniciando análisis deliberativo sobre E4 (Biodiversidad)...")
    
    # a) Recuperar evidencia
    query = f"nature credits restoration high integrity {biodiv_data['project']}"
    context = retrieve_context(query, kb)
    
    # b) Razonar
    analysis = deliberative_analysis(biodiv_data, context)
    
    # 4. Guardar Resultados (Fase 5 - Evidencia)
    output = {
        "kpi": biodiv_data,
        "raga_analysis": analysis,
        "evidence_used": context
    }
    
    (RAGA_DIR / "explain.json").write_text(json.dumps(output, indent=2))
    print("✅ Razonamiento completado. Resultado guardado en raga/explain.json")

if __name__ == "__main__":
    main()
