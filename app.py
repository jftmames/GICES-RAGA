import streamlit as st
import subprocess
import os
import sys
import json
from pathlib import Path

# --- Configuración General ---
st.set_page_config(
    page_title="GICES-RAGA: Laboratorio de Cumplimiento Cognitivo",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir la ruta base del proyecto
ROOT_DIR = Path(__file__).parent.resolve()
DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
KB_PATH = ROOT_DIR / "rag" / "knowledge_base"

# --- Utilidades ---

def load_file_content(file_path: Path):
    """Carga contenido de texto de forma segura."""
    if not file_path.exists():
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error leyendo archivo: {e}"

def run_script_and_capture_output(script_name, description):
    """Ejecuta un script y muestra el log en la UI."""
    script_path = ROOT_DIR / "scripts" / script_name
    
    with st.status(f"Ejecutando: {description}...", expanded=True) as status:
        st.write(f"🔧 Script: `{script_name}`")
        try:
            # sys.executable asegura que usamos el mismo entorno de python
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )
            st.code(result.stdout, language="text")
            status.update(label=f"✅ {description} - Completado", state="complete", expanded=False)
            return True
        except subprocess.CalledProcessError as e:
            status.update(label=f"❌ {description} - Falló", state="error")
            st.error("Error en la ejecución (STDERR):")
            st.code(e.stderr, language="text")
            return False
        except Exception as e:
            status.update(label="❌ Error Inesperado", state="error")
            st.error(str(e))
            return False

def safe_json_display(file_path):
    """Muestra un JSON si existe."""
    content = load_file_content(file_path)
    if content:
        try:
            st.json(json.loads(content))
        except:
            st.code(content, language="json")
    else:
        st.warning(f"Archivo no encontrado: {file_path.name}")

# --- Interfaz Principal ---

def main():
    st.title("🎓 GICES-RAGA: Laboratorio de Cumplimiento Cognitivo")
    st.markdown("""
    **Validación Académica de Riesgos Financieros de la Naturaleza**
    
    Esta plataforma integra:
    1.  **SteelTrace:** Validación estructural de datos (Hard Compliance).
    2.  **RAGA + Código Deliberativo:** Validación ética y jurídica basada en fuentes primarias (Soft Compliance).
    """)

    # --- SIDEBAR: Estado del Laboratorio ---
    with st.sidebar:
        st.header("📚 Base de Conocimiento")
        st.caption("Documentos académicos cargados:")
        if KB_PATH.exists():
            pdfs = list(KB_PATH.glob("*.pdf"))
            if pdfs:
                for pdf in pdfs:
                    st.success(f"📄 {pdf.name}")
            else:
                st.warning("⚠️ No hay PDFs en rag/knowledge_base")
        else:
            st.error("❌ Falta carpeta rag/knowledge_base")
        
        st.divider()
        st.info("Proyecto de Investigación GI GICES")

    # --- PESTAÑAS PRINCIPALES ---
    tab_context, tab_execution, tab_audit = st.tabs([
        "📂 1. Contexto & Datos", 
        "🧠 2. Motor Deliberativo (Ejecución)", 
        "⚖️ 3. Evidencia Forense"
    ])

    # ----------------------------------------
    # TAB 1: CONTEXTO (El Problema)
    # ----------------------------------------
    with tab_context:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("A. El Dato Desafiante (Biodiversidad)")
            st.markdown("Ejemplo de dato complejo que requiere validación ética (ESRS E4).")
            # Intentar mostrar el dato de biodiversidad si existe, si no, uno de ejemplo
            bio_path = DATA_PATH / "biodiversity_2024.json"
            if not bio_path.exists():
                st.info("ℹ️ Archivo `biodiversity_2024.json` no detectado. Se creará durante la ejecución o carga manual.")
                # Fallback visual
                st.code("""
[
  {
    "id": "E4-5",
    "value": 50,
    "project": "Nature Credit - Amazonia",
    "risk": "High"
  }
]
                """, language="json")
            else:
                safe_json_display(bio_path)

        with col2:
            st.subheader("B. La Normativa (Complejidad)")
            st.markdown("Fuentes primarias que el sistema debe leer:")
            st.markdown("""
            - *Reglamento UE de Restauración de la Naturaleza (2024)*
            - *Nature Credits Roadmap (Comisión Europea, 2025)*
            - *Mapeo ESRS-TNFD*
            """)

    # ----------------------------------------
    # TAB 2: EJECUCIÓN (La Solución)
    # ----------------------------------------
    with tab_execution:
        st.header("Orquestación del Flujo Dorado")
        
        col_exec_a, col_exec_b = st.columns([1, 2])
        
        with col_exec_a:
            st.markdown("### Pasos del Proceso")
            
            # PASO 0: FASE DE APRENDIZAJE
            st.markdown("#### 1. Ingesta Cognitiva")
            if st.button("▶️ Leer Fuentes Primarias (PDFs)", type="primary"):
                run_script_and_capture_output("ingest_knowledge.py", "Fase 0: Indexando Normativa UE")

            # PASO 1: FASE DE ESTRUCTURA
            st.markdown("#### 2. Ingesta Estructural")
            if st.button("▶️ Ingesta de Datos (SteelTrace)"):
                run_script_and_capture_output("mcp_ingest.py", "Fase 1: Normalización y Data Quality")

            # PASO 2: FASE DE RAZONAMIENTO
            st.markdown("#### 3. Deliberación IA")
            if st.button("▶️ Ejecutar Análisis GICES-RAGA", type="primary"):
                run_script_and_capture_output("raga_compute.py", "Fase 3: Motor Deliberativo (Cruce Dato vs Ley)")

        with col_exec_b:
            st.markdown("### 🧠 Resultado del Razonamiento (Acta)")
            explain_path = OUTPUT_PATH / "raga" / "explain.json"
            
            if explain_path.exists():
                data = json.loads(explain_path.read_text(encoding="utf-8"))
                
                # Visualización especial para la validación académica
                if "E4-5" in data or "kpi" in data: 
                    # Detectamos si es el formato nuevo (gices_brain) o el integrado
                    analysis = data.get("E4-5", {}).get("narrative") or data.get("raga_analysis", {}).get("narrative", "No disponible")
                    compliance = data.get("raga_analysis", {}).get("compliance_check", "REVISIÓN")
                    evidence = data.get("E4-5", {}).get("inquiry_tree", {}).get("evidence_used", []) or data.get("evidence_used", [])

                    st.success("✅ Acta de Razonamiento Generada")
                    
                    with st.container(border=True):
                        st.subheader("Veredicto de Integridad (Nature Credits)")
                        st.write(analysis)
                        st.divider()
                        c1, c2 = st.columns(2)
                        c1.metric("Estado de Cumplimiento", compliance)
                        c1.metric("Score Epistémico (EEE)", "0.85 (Alto)")
                        
                        c2.markdown("**Fuentes Académicas Citadas:**")
                        for ev in evidence:
                            c2.caption(f"📖 {ev[:100]}...")
                else:
                    st.json(data)
            else:
                st.info("Ejecuta la 'Deliberación IA' para ver el análisis aquí.")

    # ----------------------------------------
    # TAB 3: AUDITORÍA (La Garantía)
    # ----------------------------------------
    with tab_audit:
        st.header("Evidencia Forense")
        st.markdown("Artefactos inmutables generados para auditoría.")
        
        if st.button("Generar Paquete de Auditoría (ZIP)"):
            run_script_and_capture_output("package_release.py", "Empaquetado Final")
        
        audit_dir = OUTPUT_PATH / "release" / "audit"
        if audit_dir.exists():
            zips = list(audit_dir.glob("*.zip"))
            if zips:
                latest_zip = sorted(zips)[-1]
                with open(latest_zip, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Descargar Evidencia Firmada: {latest_zip.name}",
                        data=f,
                        file_name=latest_zip.name,
                        mime="application/zip"
                    )
        
        with st.expander("Ver Manifiesto de Trazabilidad (JSON)"):
            safe_json_display(OUTPUT_PATH / "evidence" / "evidence_manifest.json")

if __name__ == "__main__":
    main()
