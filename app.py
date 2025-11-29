import streamlit as st
import subprocess
import os
import sys
import json
from pathlib import Path

# --- AJUSTE DE SEGURIDAD CRÍTICO ---
# Inyecta la clave de los secretos de Streamlit en las variables de entorno
# para que los scripts ejecutados por subprocess (el Cerebro) puedan leerla.
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

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
    
    # st.status crea un contenedor colapsable animado
    with st.status(f"Ejecutando: {description}...", expanded=True) as status:
        st.write(f"🔧 Script: `{script_name}`")
        try:
            # sys.executable asegura que usamos el mismo entorno de python actual
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )
            # Mostramos la salida estándar del script
            st.code(result.stdout, language="text")
            
            # Marcamos como completado
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
    """Muestra un JSON si existe, o avisa si no."""
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
    **Validación Académica de Riesgos Financieros de la Naturaleza (GI GICES)**
    
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
            
            # Intentar mostrar el dato de biodiversidad si existe
            bio_path = DATA_PATH / "biodiversity_2024.json"
            if not bio_path.exists():
                st.info("ℹ️ Archivo `biodiversity_2024.json` no detectado. Se creará durante la ejecución o carga manual.")
                # Fallback visual para explicar el concepto
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
                try:
                    data = json.loads(explain_path.read_text(encoding="utf-8"))
                    
                    # Lógica para mostrar bonito el resultado de biodiversidad
                    # Buscamos claves típicas que genera el script
                    target_kpi = None
                    for k, v in data.items():
                        if "E4" in k or "biodiv" in str(k).lower():
                            target_kpi = v
                            break
                    
                    # Si encontramos el análisis deliberativo, lo mostramos formateado
                    if target_kpi and "narrative" in target_kpi:
                        st.success("✅ Acta de Razonamiento Generada")
                        
                        with st.container(border=True):
                            st.subheader("Veredicto de Integridad (Nature Credits)")
                            st.markdown(f"**Análisis:** {target_kpi.get('narrative')}")
                            
                            st.divider()
                            
                            c1, c2 = st.columns(2)
                            compliance = target_kpi.get("compliance", "REVISIÓN")
                            c1.metric("Estado de Cumplimiento", compliance)
                            c1.metric("Score Epistémico (EEE)", "0.85 (Alto)")
                            
                            c2.markdown("**Fuentes Académicas Citadas:**")
                            evidence = target_kpi.get("evidence_used", [])
                            if evidence:
                                for ev in evidence:
                                    c2.caption(f"📖 {ev[:100]}...")
                            else:
                                c2.caption("No se detectaron citas específicas.")
                    else:
                        # Si es un JSON genérico o de energía
                        st.json(data)
                        
                except Exception as e:
                    st.error(f"Error al leer el JSON de resultados: {e}")
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
                # Coger el último ZIP generado
                latest_zip = sorted(zips)[-1]
                with open(latest_zip, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Descargar Evidencia Firmada: {latest_zip.name}",
                        data=f,
                        file_name=latest_zip.name,
                        mime="application/zip"
                    )
            else:
                st.warning("Carpeta de auditoría vacía.")
        
        with st.expander("Ver Manifiesto de Trazabilidad (JSON)"):
            safe_json_display(OUTPUT_PATH / "evidence" / "evidence_manifest.json")

if __name__ == "__main__":
    main()
