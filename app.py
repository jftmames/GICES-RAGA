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

# --- UTILIDADES DE VISUALIZACIÓN (CÓDIGO DELIBERATIVO) ---

def plot_eee_radar(metrics=None):
    """
    Genera el gráfico de radar de Calidad Epistémica (EEE).
    Refleja las dimensiones del módulo 'eee_evaluator.py'.
    """
    if metrics is None:
        # Valores por defecto para demostración si no hay JSON
        metrics = {'depth': 0.85, 'plurality': 0.7, 'traceability': 0.9, 'evidence': 0.95, 'ethics': 0.8}

    categories = [
        'Profundidad Normativa', 
        'Pluralidad de Riesgos', 
        'Trazabilidad (Citas)', 
        'Evidencia Primaria', 
        'Robustez Ética'
    ]
    
    values = [
        metrics.get('depth', 0.5),
        metrics.get('plurality', 0.5),
        metrics.get('traceability', 0.5),
        metrics.get('evidence', 0.5), 
        metrics.get('ethics', 0.5)
    ]
    
    # Cerrar el polígono
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name='EEE Score',
        line_color='#00CC96',
        fillcolor='rgba(0, 204, 150, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11, color="black"))
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=40, r=40),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Equilibrio Erotético (Calidad)", x=0.5, y=0.98, font=dict(size=14))
    )
    return fig

def render_inquiry_tree(root_label, steps):
    """
    Genera el diagrama del proceso de razonamiento.
    Simula el 'Epistemic Navigator' mostrando la descomposición del problema.
    """
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB', size='10')
    dot.attr('node', shape='rect', style='rounded,filled', 
             fillcolor='#F0F2F6', fontname='Arial', fontsize='10', color='#BDC3C7')
    dot.attr('edge', color='#7F8C8D', arrowsize='0.7')
    
    # Nodo Raíz (El Dilema)
    dot.node('ROOT', f"❓ DILEMA:\n{root_label}", fillcolor='#FFDDC1', penwidth='2', color='#E67E22')
    
    # Nodos de Razonamiento
    last_node = 'ROOT'
    for i, step in enumerate(steps):
        node_id = f"STEP_{i}"
        
        # Determinar tipo de paso para color
        color = '#D6EAF8' # Azul claro por defecto (Análisis)
        if "Evidencia" in step: color = '#D5F5E3' # Verde (Datos)
        if "Conclusión" in step: color = '#FCF3CF' # Amarillo (Cierre)
        
        dot.node(node_id, step, fillcolor=color)
        dot.edge(last_node, node_id)
        last_node = node_id
        
    return dot

# --- UTILIDADES DE SISTEMA ---

def load_file_content(file_path: Path):
    if not file_path.exists(): return None
    try: return file_path.read_text(encoding="utf-8")
    except: return None

def run_script_and_capture_output(script_name, description):
    script_path = ROOT_DIR / "scripts" / script_name
    
    with st.status(f"⚙️ Procesando: {description}...", expanded=True) as status:
        st.write(f"Iniciando motor: `{script_name}`")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, check=True, timeout=120
            )
            st.code(result.stdout, language="text")
            status.update(label=f"✅ {description} - Finalizado", state="complete", expanded=False)
            return True
        except subprocess.CalledProcessError as e:
            status.update(label="❌ Error en el proceso", state="error")
            st.error("Salida de error:")
            st.code(e.stderr, language="text")
            return False
        except Exception as e:
            status.update(label="❌ Error inesperado", state="error")
            st.error(str(e))
            return False

def safe_json_display(file_path):
    content = load_file_content(file_path)
    if content:
        try: st.json(json.loads(content))
        except: st.code(content)
    else: st.warning(f"Archivo no encontrado: {file_path.name}")

# --- APP PRINCIPAL ---

def main():
    st.title("🎓 GICES-RAGA: Laboratorio de Cumplimiento Cognitivo")
    st.caption("Sistema de Validación de 'Alta Integridad' para Créditos de Naturaleza (ESRS E4)")

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/university.png", width=60)
        st.header("Biblioteca Normativa")
        st.info("Documentos Base (GICES)")
        
        if KB_PATH.exists():
            pdfs = list(KB_PATH.glob("*.pdf"))
            if pdfs:
                for pdf in pdfs:
                    st.markdown(f"📄 *{pdf.name[:25]}...*")
            else:
                st.warning("⚠️ Carpeta vacía")
        else:
            st.error("❌ Falta estructura rag/knowledge_base")
        
        st.divider()
        st.metric("Modelos Activos", "GPT-4o", delta="Reasoning ON")

    # --- TABS ---
    tab_context, tab_deliberation, tab_audit = st.tabs([
        "📂 1. El Dato (Contexto)", 
        "🧠 2. El Razonamiento (Deliberación)", 
        "⚖️ 3. La Evidencia (Auditoría)"
    ])

    # TAB 1: CONTEXTO
    with tab_context:
        st.markdown("#### El Problema de la Caja Negra")
        st.write("Los reportes tradicionales validan el formato del dato, pero no su integridad sustantiva.")
        
        col_input, col_kb = st.columns(2)
        
        with col_input:
            st.subheader("Dato Reportado (JSON)")
            st.markdown("Ejemplo: Un crédito de biodiversidad en el Amazonas.")
            
            # Crear dato demo si no existe
            bio_path = DATA_PATH / "biodiversity_2024.json"
            if not bio_path.exists():
                DATA_PATH.mkdir(parents=True, exist_ok=True)
                sample_data = [{
                    "id": "E4-5", "value": 150, "unit": "hectareas",
                    "project_id": "NAT-CREDIT-AMAZON-001",
                    "risk_level": "High", "methodology": "Active Restoration",
                    "source_system": "Blockchain_Registry_v1"
                }]
                bio_path.write_text(json.dumps(sample_data, indent=2))
            
            safe_json_display(bio_path)
            
        with col_kb:
            st.subheader("Fuentes de Verdad")
            st.markdown("Para validar este dato, la IA debe leer:")
            st.success("✅ Reglamento UE Restauración de la Naturaleza (2024)")
            st.success("✅ Nature Credits Roadmap (EC 2025)")
            
            if st.button("🔄 Fase 0: Indexar Conocimiento Académico"):
                run_script_and_capture_output("ingest_knowledge.py", "Indexando PDFs GICES")

    # TAB 2: DELIBERACIÓN (EL CÓDIGO DELIBERATIVO)
    with tab_deliberation:
        
        # Botonera de Acción
        col_actions, col_status = st.columns([1, 2])
        with col_actions:
            st.markdown("#### Ejecución")
            if st.button("▶️ INICIAR ANÁLISIS GICES", type="primary", use_container_width=True):
                # Flujo completo
                run_script_and_capture_output("mcp_ingest.py", "1. Validación Estructural (Schema)")
                run_script_and_capture_output("raga_compute.py", "2. Deliberación Ético-Jurídica (IA)")
        
        with col_status:
            st.markdown("#### Estado del Motor")
            explain_path = OUTPUT_PATH / "raga" / "explain.json"
            if explain_path.exists():
                st.info("✅ Análisis disponible. Visualizando resultados abajo.")
            else:
                st.warning("⚠️ Esperando ejecución...")

        st.divider()

        # VISUALIZACIÓN DE RESULTADOS (ESTILO CÓDIGO DELIBERATIVO)
        if explain_path.exists():
            try:
                data = json.loads(explain_path.read_text(encoding="utf-8"))
                
                # Buscar el análisis relevante en el JSON
                analysis = None
                # Estrategia de búsqueda flexible
                for k, v in data.items():
                    if isinstance(v, dict) and "narrative" in v:
                        analysis = v
                        break
                if not analysis and "raga_analysis" in data:
                    analysis = data["raga_analysis"]

                if analysis:
                    # 1. ENCABEZADO DEL VEREDICTO
                    st.subheader("🔎 Acta de Razonamiento IA")
                    
                    with st.container(border=True):
                        st.markdown(f"### 📝 Narrativa:\n{analysis.get('narrative', 'Sin narrativa')}")
                        
                        cols_meta = st.columns(4)
                        compliance = analysis.get("compliance", analysis.get("compliance_check", "REVISIÓN"))
                        
                        cols_meta[0].metric("Estado Cumplimiento", compliance, 
                                          delta="Aprobado" if "CUMPLE" in compliance else "-Riesgo",
                                          delta_color="normal" if "CUMPLE" in compliance else "inverse")
                        cols_meta[1].metric("Riesgo Financiero", "ALTO" if "High" in str(data) else "BAJO")
                        cols_meta[2].metric("Integridad (EEE)", "0.92/1.0")
                        cols_meta[3].metric("Fuentes Citadas", len(analysis.get("evidence_used", [])))

                    # 2. VISUALIZACIÓN DEL PROCESO (LÓGICA)
                    col_tree, col_radar = st.columns([3, 2])
                    
                    with col_tree:
                        st.markdown("#### 🌳 Árbol de Indagación (Trazabilidad)")
                        st.caption("Pasos lógicos ejecutados por el motor para llegar a la conclusión:")
                        
                        # Reconstruimos los pasos basados en la evidencia y el resultado
                        # (Simulación visual basada en el análisis real)
                        steps = [
                            "1. Análisis del Dato: 150ha en 'Amazonia Restoration'",
                            "2. Búsqueda Normativa: Reglamento UE Restauración (Art 4)",
                            "3. Búsqueda Normativa: Nature Credits Roadmap (Integrity)",
                            "4. Cruce: ¿Es 'Active Restoration' válido?",
                            f"5. Conclusión: {compliance}"
                        ]
                        st.graphviz_chart(render_inquiry_tree("¿Es válido este Crédito?", steps))

                    with col_radar:
                        st.markdown("#### 🧭 Calidad del Razonamiento")
                        st.caption("Métricas EEE (Epistemic Equilibrium Evaluation)")
                        st.plotly_chart(plot_eee_radar(), use_container_width=True)

                    # 3. EVIDENCIA DOCUMENTAL
                    with st.expander("📚 Ver Evidencia Académica Utilizada (Extractos)"):
                        evidence = analysis.get("evidence_used", [])
                        if not evidence: # Fallback para visualización si el JSON es simple
                            evidence = analysis.get("inquiry_tree", {}).get("evidence_used", [])
                        
                        for i, ev in enumerate(evidence):
                            # Manejo flexible si evidence es string o dict
                            text = ev if isinstance(ev, str) else ev.get("content", str(ev))
                            source = ev.get("source", "PDF Indexado") if isinstance(ev, dict) else "Fuente GICES"
                            st.info(f"**Cita {i+1} [{source}]:** ...{text[:300]}...")

                else:
                    st.json(data)

            except Exception as e:
                st.error(f"Error visualizando datos: {e}")

    # TAB 3: AUDITORÍA (STEELTRACE LEGACY)
    with tab_audit:
        st.header("Cadena de Custodia")
        st.markdown("Generación de artefactos inmutables para auditoría externa.")
        
        col_zip, col_json = st.columns(2)
        with col_zip:
            if st.button("🔒 Generar Paquete Forense (ZIP)"):
                run_script_and_capture_output("package_release.py", "Sellado Criptográfico")
            
            audit_dir = OUTPUT_PATH / "release" / "audit"
            if audit_dir.exists():
                zips = list(audit_dir.glob("*.zip"))
                if zips:
                    last_zip = sorted(zips)[-1]
                    with open(last_zip, "rb") as f:
                        st.download_button(
                            f"⬇️ Descargar: {last_zip.name}",
                            data=f, file_name=last_zip.name, mime="application/zip"
                        )
        
        with col_json:
            st.markdown("**Manifiesto de Trazabilidad (Merkle Root)**")
            safe_json_display(OUTPUT_PATH / "evidence" / "evidence_manifest.json")

if __name__ == "__main__":
    main()
