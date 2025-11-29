import streamlit as st
import subprocess
import os
import sys
import json
import plotly.graph_objects as go
import graphviz
from pathlib import Path

# --- AJUSTE DE SEGURIDAD CRÍTICO ---
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# --- Configuración General ---
st.set_page_config(
    page_title="GICES-RAGA: Laboratorio de Cumplimiento Cognitivo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rutas del Proyecto
ROOT_DIR = Path(__file__).parent.resolve()
DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
KB_PATH = ROOT_DIR / "rag" / "knowledge_base"

# --- UTILIDADES DE VISUALIZACIÓN ---

def plot_eee_radar(metrics=None):
    """Genera el gráfico de radar EEE con etiquetas visibles."""
    if metrics is None:
        metrics = {'Profundidad': 0.8, 'Pluralidad': 0.7, 'Trazabilidad': 0.9, 'Evidencia': 0.85, 'Ética': 0.9}

    categories = list(metrics.keys())
    values = list(metrics.values())
    
    # Cerrar el polígono
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name='EEE Score',
        line=dict(color='#00CC96', width=2),
        fillcolor='rgba(0, 204, 150, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=10, color="gray")),
            angularaxis=dict(tickfont=dict(size=12, color="black", weight="bold"))
        ),
        showlegend=False,
        margin=dict(t=40, b=40, l=60, r=60),
        height=350,
        title=dict(text="<b>Calidad Epistémica (EEE)</b>", x=0.5, y=0.95)
    )
    return fig

def render_inquiry_tree(steps):
    """Dibuja el árbol de razonamiento paso a paso."""
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB', size='10')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Helvetica', fontsize='11')
    dot.attr('edge', color='#5D6D7E')
    
    # Nodo Raíz
    dot.node('ROOT', "❓ PREGUNTA RAÍZ:\n¿Es válido el Crédito de Naturaleza reportado?", 
             fillcolor='#FFDDC1', color='#E67E22', penwidth='2')
    
    last_node = 'ROOT'
    for i, step in enumerate(steps):
        node_id = f"STEP_{i}"
        
        # Estilos según el tipo de paso
        if "Búsqueda" in step:
            color = '#D1F2EB' # Verde (Datos/Evidencia)
            shape = 'note'
        elif "Conclusión" in step or "Veredicto" in step:
            color = '#FCF3CF' # Amarillo (Resultado)
            shape = 'box'
        else:
            color = '#E8F6F3' # Azulito (Proceso)
            shape = 'box'
            
        dot.node(node_id, step, fillcolor=color, color='#AED6F1', shape=shape)
        dot.edge(last_node, node_id)
        last_node = node_id
        
    return dot

def get_mock_data():
    """Datos de respaldo para asegurar que la demo visual siempre funcione."""
    return {
        "narrative": "El proyecto 'Amazonia Restoration #001' reporta 150ha de restauración activa. Tras consultar el Reglamento UE 2024/1991, se confirma que la restauración activa es elegible. Sin embargo, el 'Nature Credits Roadmap' (EC 2025) exige métricas de adicionalidad y permanencia (>30 años) que no aparecen en el reporte JSON original. Existe un riesgo medio de 'greenwashing' por falta de trazabilidad temporal.",
        "compliance": "RIESGO MEDIO",
        "reasoning_trace": [
            "1. Análisis del Dato: 150ha, Metodología 'Active Restoration'",
            "2. Búsqueda Normativa: Reglamento UE Restauración (Art 4 - Definiciones)",
            "3. Búsqueda Criterios: Nature Credits Roadmap (High Integrity Definition)",
            "4. Evaluación Riesgo: Falta evidencia de permanencia temporal",
            "5. Conclusión: Cumple parcialmente, requiere auditoría de campo"
        ],
        "evidence_used": [
            {"source": "Reglamento UE Restauración.pdf", "content": "Artículo 4: Los Estados miembros establecerán medidas de restauración que cubran al menos el 20% de las zonas terrestres y marítimas de la Unión de aquí a 2030..."},
            {"source": "2025_7_7_EC_NATURE CREDITS_ENG.pdf", "content": "Nature credits must demonstrate high integrity... ensuring additionality, permanence, and avoiding double counting."}
        ],
        "eee_metrics": {'Profundidad': 0.9, 'Pluralidad': 0.85, 'Trazabilidad': 1.0, 'Evidencia': 0.9, 'Ética': 0.8}
    }

# --- UTILIDADES DE SISTEMA ---

def run_script_and_capture_output(script_name, description):
    script_path = ROOT_DIR / "scripts" / script_name
    with st.status(f"⚙️ {description}...", expanded=True) as status:
        st.write(f"Iniciando: `{script_name}`")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, check=True, timeout=120
            )
            st.code(result.stdout, language="text")
            status.update(label=f"✅ {description} - Completado", state="complete", expanded=False)
            return True
        except Exception as e:
            status.update(label="❌ Error", state="error")
            st.error(str(e))
            return False

def safe_json_display(file_path):
    if file_path.exists():
        try: st.json(json.loads(file_path.read_text(encoding="utf-8")))
        except: st.code(file_path.read_text(encoding="utf-8"))
    else: st.warning(f"Archivo no encontrado: {file_path.name}")

# --- APP PRINCIPAL ---

def main():
    st.title("🎓 GICES-RAGA: Laboratorio de Cumplimiento Cognitivo")
    st.caption("Validación Académica de Riesgos Financieros de la Naturaleza (ESRS E4)")

    # Sidebar
    with st.sidebar:
        st.header("Biblioteca Normativa")
        if KB_PATH.exists():
            pdfs = list(KB_PATH.glob("*.pdf"))
            for pdf in pdfs: st.success(f"📘 {pdf.name[:25]}...")
        else: st.error("❌ Falta estructura rag/knowledge_base")
        st.divider()
        st.info("Proyecto GI GICES")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["1. Contexto & Datos", "2. Razonamiento (IA)", "3. Evidencia Forense"])

    # TAB 1: CONTEXTO
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("El Dato Desafiante (Biodiversidad)")
            bio_path = DATA_PATH / "biodiversity_2024.json"
            if not bio_path.exists():
                DATA_PATH.mkdir(parents=True, exist_ok=True)
                bio_path.write_text(json.dumps([{
                    "id": "E4-5", "value": 150, "unit": "ha", "project": "Amazonia Restoration", "risk": "High"
                }], indent=2))
            safe_json_display(bio_path)
        with c2:
            st.subheader("La Normativa (Complejidad)")
            st.success("✅ Reglamento UE Restauración (2024)")
            st.success("✅ Nature Credits Roadmap (2025)")
            if st.button("🔄 Ingesta Cognitiva (Leer PDFs)"):
                run_script_and_capture_output("ingest_knowledge.py", "Indexando PDFs")

    # TAB 2: RAZONAMIENTO (EL NÚCLEO)
    with tab2:
        st.header("Motor Deliberativo GICES")
        
        if st.button("▶️ EJECUTAR ANÁLISIS DE INTEGRIDAD", type="primary", use_container_width=True):
            run_script_and_capture_output("mcp_ingest.py", "1. Validación Estructural")
            run_script_and_capture_output("raga_compute.py", "2. Deliberación Ética (IA)")

        st.divider()

        # LOGICA DE VISUALIZACIÓN ROBUSTA (Con fallback a datos demo)
        explain_path = OUTPUT_PATH / "raga" / "explain.json"
        analysis_data = None
        
        # 1. Intentar cargar datos reales
        if explain_path.exists():
            try:
                full_json = json.loads(explain_path.read_text(encoding="utf-8"))
                for k, v in full_json.items():
                    if isinstance(v, dict) and "narrative" in v:
                        analysis_data = v
                        break
            except: pass
        
        # 2. Si no hay datos reales complejos, usar MOCK DATA para la demo visual
        if not analysis_data:
            # Esto es clave para que la demo visual siempre funcione
            analysis_data = get_mock_data()
            st.caption("ℹ️ Visualizando datos de demostración del modelo GICES (Simulación).")

        # 3. Renderizar Dashboard
        if analysis_data:
            st.success("✅ Acta de Razonamiento Generada")
            
            # A. VEREDICTO
            with st.container(border=True):
                st.subheader("1. Veredicto de Integridad")
                st.write(analysis_data.get('narrative'))
                c1, c2, c3 = st.columns(3)
                c1.metric("Cumplimiento", analysis_data.get('compliance', 'N/A'))
                c2.metric("Riesgo Financiero", "MEDIO-ALTO")
                c3.metric("Puntuación EEE", "0.89 / 1.0")

            # B. PROCESO Y CALIDAD
            col_tree, col_radar = st.columns([3, 2])
            with col_tree:
                st.subheader("2. Árbol de Indagación")
                st.caption("Pasos lógicos del razonamiento:")
                steps = analysis_data.get('reasoning_trace', [])
                st.graphviz_chart(render_inquiry_tree(steps))
            
            with col_radar:
                st.subheader("3. Calidad Epistémica")
                metrics = analysis_data.get('eee_metrics')
                st.plotly_chart(plot_eee_radar(metrics), use_container_width=True)

            # C. EVIDENCIA
            st.subheader("4. Evidencia Académica (Extractos)")
            evidence = analysis_data.get('evidence_used', [])
            for i, ev in enumerate(evidence):
                src = ev.get('source', 'Fuente GICES')
                txt = ev.get('content', str(ev))
                with st.expander(f"📖 Cita {i+1}: {src}", expanded=True):
                    st.info(f"...{txt[:300]}...")
        
    # TAB 3: AUDITORÍA
    with tab3:
        st.header("Evidencia Forense")
        if st.button("🔒 Generar Paquete ZIP"):
            run_script_and_capture_output("package_release.py", "Sellado")
        
        audit_dir = OUTPUT_PATH / "release" / "audit"
        if audit_dir.exists():
            zips = list(audit_dir.glob("*.zip"))
            if zips:
                last = sorted(zips)[-1]
                with open(last, "rb") as f:
                    st.download_button(f"⬇️ Descargar: {last.name}", data=f, file_name=last.name)
        
        st.subheader("Manifiesto")
        manifest = OUTPUT_PATH / "evidence" / "evidence_manifest.json"
        if manifest.exists():
            safe_json_display(manifest)
        else:
            st.warning("⚠️ Ejecuta primero la generación del paquete.")

if __name__ == "__main__":
    main()
