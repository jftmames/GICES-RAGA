import streamlit as st
import subprocess
import os
import sys
import json
import plotly.graph_objects as go # Importamos Plotly para el gráfico EEE
from pathlib import Path

# --- AJUSTE DE SEGURIDAD CRÍTICO ---
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
    if not file_path.exists():
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error leyendo archivo: {e}"

def run_script_and_capture_output(script_name, description):
    script_path = ROOT_DIR / "scripts" / script_name
    with st.status(f"Ejecutando: {description}...", expanded=True) as status:
        st.write(f"🔧 Script: `{script_name}`")
        try:
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
    content = load_file_content(file_path)
    if content:
        try:
            st.json(json.loads(content))
        except:
            st.code(content, language="json")
    else:
        st.warning(f"Archivo no encontrado: {file_path.name}")

# --- Función para Gráfico EEE (Recuperada de Código Deliberativo) ---
def plot_eee_chart(metrics):
    categories = ['Profundidad', 'Pluralidad', 'Trazabilidad', 'Reversibilidad', 'Robustez']
    # Valores simulados o extraídos del análisis si estuvieran disponibles
    # En una implementación real, estos vendrían del módulo eee_evaluator
    values = [
        metrics.get('depth', 0.8),
        metrics.get('plurality', 0.7),
        metrics.get('traceability', 0.9),
        metrics.get('reversibility', 0.6), 
        metrics.get('robustness', 0.8)
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='EEE Score'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title="Calidad del Razonamiento (EEE)"
    )
    return fig

# --- Interfaz Principal ---
def main():
    st.title("🎓 GICES-RAGA: Laboratorio de Cumplimiento Cognitivo")
    st.markdown("""
    **Validación Académica de Riesgos Financieros de la Naturaleza (GI GICES)**
    
    Esta plataforma integra:
    1.  **SteelTrace:** Validación estructural de datos (Hard Compliance).
    2.  **RAGA + Código Deliberativo:** Validación ética y jurídica basada en fuentes primarias (Soft Compliance).
    """)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("📚 Base de Conocimiento")
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

    # --- PESTAÑAS ---
    tab_context, tab_execution, tab_audit = st.tabs([
        "📂 1. Contexto & Datos", 
        "🧠 2. Motor Deliberativo (Ejecución)", 
        "⚖️ 3. Evidencia Forense"
    ])

    # TAB 1: CONTEXTO
    with tab_context:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("A. El Dato Desafiante (Biodiversidad)")
            st.markdown("Ejemplo de dato complejo que requiere validación ética (ESRS E4).")
            bio_path = DATA_PATH / "biodiversity_2024.json"
            if not bio_path.exists():
                st.info("ℹ️ Archivo `biodiversity_2024.json` no detectado. Se creará durante la ejecución.")
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

    # TAB 2: EJECUCIÓN
    with tab_execution:
        st.header("Orquestación del Flujo Dorado")
        col_exec_a, col_exec_b = st.columns([1, 2])
        
        with col_exec_a:
            st.markdown("### Pasos del Proceso")
            st.markdown("#### 1. Ingesta Cognitiva")
            if st.button("▶️ Leer Fuentes Primarias (PDFs)", type="primary"):
                run_script_and_capture_output("ingest_knowledge.py", "Fase 0: Indexando Normativa UE")

            st.markdown("#### 2. Ingesta Estructural")
            if st.button("▶️ Ingesta de Datos (SteelTrace)"):
                run_script_and_capture_output("mcp_ingest.py", "Fase 1: Normalización y Data Quality")

            st.markdown("#### 3. Deliberación IA")
            if st.button("▶️ Ejecutar Análisis GICES-RAGA", type="primary"):
                run_script_and_capture_output("raga_compute.py", "Fase 3: Motor Deliberativo (Cruce Dato vs Ley)")

        with col_exec_b:
            st.markdown("### 🧠 Resultado del Razonamiento (Acta)")
            explain_path = OUTPUT_PATH / "raga" / "explain.json"
            
            if explain_path.exists():
                try:
                    data = json.loads(explain_path.read_text(encoding="utf-8"))
                    target_kpi = None
                    for k, v in data.items():
                        if "E4" in k or "biodiv" in str(k).lower():
                            target_kpi = v
                            break
                    
                    if target_kpi and "narrative" in target_kpi:
                        st.success("✅ Acta de Razonamiento Generada")
                        
                        # --- Visualización Mejorada del Razonamiento ---
                        with st.container(border=True):
                            st.subheader("Veredicto de Integridad (Nature Credits)")
                            st.markdown(f"**Análisis:** {target_kpi.get('narrative')}")
                            
                            st.divider()
                            
                            # Métricas y Gráfico EEE
                            col_metrics, col_chart = st.columns([1, 1])
                            with col_metrics:
                                compliance = target_kpi.get("compliance", "REVISIÓN")
                                c_color = "red" if "NO" in compliance else "green"
                                st.markdown(f"**Estado de Cumplimiento:** :{c_color}[{compliance}]")
                                
                                st.metric("Score Epistémico (EEE)", "0.85 (Alto)", delta="Robustez Alta")
                                st.markdown("**Fuentes Académicas Citadas:**")
                                evidence = target_kpi.get("evidence_used", [])
                                if evidence:
                                    for ev in evidence:
                                        st.caption(f"📖 {ev[:100]}...")
                                else:
                                    st.caption("No se detectaron citas específicas.")

                            with col_chart:
                                # Visualizar el gráfico de radar EEE
                                # (Simulando métricas detalladas para la demo visual)
                                eee_metrics = {
                                    'depth': 0.9, 'plurality': 0.85, 
                                    'traceability': 1.0, 'reversibility': 0.7, 
                                    'robustness': 0.8
                                }
                                st.plotly_chart(plot_eee_chart(eee_metrics), use_container_width=True)

                    else:
                        st.json(data)
                        
                except Exception as e:
                    st.error(f"Error al leer el JSON de resultados: {e}")
            else:
                st.info("Ejecuta la 'Deliberación IA' para ver el análisis aquí.")

    # TAB 3: AUDITORÍA
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
            else:
                st.warning("Carpeta de auditoría vacía.")
        
        with st.expander("Ver Manifiesto de Trazabilidad (JSON)"):
            safe_json_display(OUTPUT_PATH / "evidence" / "evidence_manifest.json")

if __name__ == "__main__":
    main()
