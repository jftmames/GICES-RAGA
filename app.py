import streamlit as st
import subprocess
import os
import sys
import json
from pathlib import Path

# --- Configuración General ---
st.set_page_config(
    page_title="SteelTrace CSRD Pipeline",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir la ruta base del proyecto y asegurar el CWD
ROOT_DIR = Path(__file__).parent.resolve()
os.chdir(ROOT_DIR)

DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
try:
    SAMPLE_FILES = [f.name for f in DATA_PATH.glob("*.json")]
except FileNotFoundError:
    SAMPLE_FILES = []

# Listado de scripts del pipeline en orden de ejecución
PIPELINE_SCRIPTS = [
    "mcp_ingest.py",
    "shacl_validate.py",
    "raga_compute.py",
    "eee_gate.py",
    "xbrl_generate.py",
    "evidence_build.py",
    "hitl_kappa.py",
    "package_release.py"
]

# --- Utilidades ---

def load_file_content(file_path: Path):
    """Carga y retorna el contenido de un archivo como texto (UTF-8) o None si no existe."""
    try:
        # Retorna la cadena de texto
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception as e:
        return f"Error al leer {file_path.name}: {e}"

def run_script_and_capture_output(script_name):
    """
    Ejecuta un script del pipeline usando sys.executable para asegurar el entorno.
    """
    script_path = ROOT_DIR / "scripts" / script_name
    
    # 1. Mostrar la información de ejecución
    with st.spinner(f"Ejecutando script: **{script_name}**..."):
        # Muestra el path del intérprete de Streamlit
        st.code(f"Comando: {sys.executable} {script_name}", language="bash")

        try:
            # Usar sys.executable para que encuentre todas las dependencias
            result = subprocess.run(
                [sys.executable, str(script_path)], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=60
            )
            st.success(f"✅ Ejecución de **{script_name}** completada con éxito.")
            st.info("Salida del script (STDOUT):")
            st.code(result.stdout, language="text")
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Ejecución de **{script_name}** FALLIDA con código de retorno {e.returncode}.")
            st.text("STDOUT:")
            st.code(e.stdout, language="text")
            st.text("STDERR (El error principal):")
            st.code(e.stderr, language="text")
            return None
            
        except FileNotFoundError:
            st.error(f"❌ Error: No se encontró el script **{script_name}**. Verifique que existe en la carpeta `scripts/`.")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado al ejecutar **{script_name}**: {e}")
            return None

def safe_json_display(content):
    """Muestra contenido JSON o un mensaje de advertencia si es None o inválido."""
    if content is None:
        st.warning("Archivo de salida aún no generado o no encontrado. Ejecuta el paso correspondiente.")
        return
    try:
        # Intenta cargar la cadena como objeto JSON (requerido por st.json)
        st.json(json.loads(content))
    except json.JSONDecodeError:
        st.warning("Contenido no es JSON válido. Mostrando como texto simple:")
        st.code(content, language="text")
    except Exception:
         st.code(content, language="text")

# --- Interfaz de Streamlit ---

def main():
    st.title("⚙️ SteelTrace: Pipeline de Procesamiento CSRD")
    st.markdown("Guía interactiva para la consultora: inspección de datos y ejecución paso a paso del pipeline de trazabilidad y gobernanza.")

    data_tab, pipeline_tab = st.tabs(["📂 1. Datos de Entrada (Data Inspection)", "⚙️ 2. Pipeline Interactivo (Ejecución y Artefactos)"])

    # ----------------------------------------
    # PESTAÑA 1: DATOS DE ENTRADA
    # ----------------------------------------
    with data_tab:
        st.header("Inspección de Archivos de Muestra")
        st.markdown("Los archivos JSON en `data/samples/` son la fuente de datos (E1, S1, G1).")
        
        st.sidebar.header("Archivos de Muestra")
        selected_file_name = st.sidebar.selectbox(
            "Selecciona un archivo JSON:",
            SAMPLE_FILES,
            index=0 if SAMPLE_FILES else 0
        )
        
        if selected_file_name and SAMPLE_FILES:
            file_path = DATA_PATH / selected_file_name
            st.subheader(f"Contenido de: `{selected_file_name}`")
            
            content = load_file_content(file_path)
            if content:
                try:
                    st.json(json.loads(content))
                except:
                    st.code(content, language="json")

            with st.expander("Ver Contrato/Schema Relacionado (`contracts/`):"):
                if "energy" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "erp_energy.schema.json"
                elif "hr" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "hr_people.schema.json"
                elif "ethics" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "ethics_cases.schema.json"
                else:
                    schema_path = None
                
                if schema_path and schema_path.exists():
                    st.code(load_file_content(schema_path), language="json")
                else:
                    st.warning(f"Esquema no disponible.")
        elif not SAMPLE_FILES:
             st.warning("No se encontraron archivos de muestra en `data/samples/`. Verifique la estructura del repositorio.")


    # ----------------------------------------
    # PESTAÑA 2: PIPELINE INTERACTIVO
    # ----------------------------------------
    with pipeline_tab:
        st.header("Ejecución Paso a Paso del Pipeline de Gobernanza")
        st.markdown("Presiona los botones en orden para generar los artefactos de cumplimiento.")

        if 'execution_logs' not in st.session_state:
            st.session_state.execution_logs = {}
        
        for i, script in enumerate(PIPELINE_SCRIPTS):
            st.subheader(f"Paso {i+1}: {script}")
            
            if st.button(f"▶️ Ejecutar {script}", key=f"run_btn_{i}", type="secondary", help="Ejecuta el script y muestra los logs de salida."):
                run_script_and_capture_output(script)
        
        st.divider()

        # --- VISUALIZACIÓN DE ARTEFACTOS GENERADOS ---
        st.header("Artefactos de Salida Clave")
        st.markdown("Revisa los reportes generados después de ejecutar los pasos.")

        # 1. Reporte DQ y Linaje (Paso 1)
        with st.expander("✅ Ingesta/Data Quality (DQ) y Linaje"):
            safe_json_display(load_file_content(OUTPUT_PATH / "data" / "dq_report.json"))
            st.code(load_file_content(OUTPUT_PATH / "data" / "lineage.jsonl"), language="json")

        # 2. Validación Semántica (Paso 2)
        with st.expander("✅ Validación SHACL y Grafo RDF (Trazabilidad Semántica)"):
            validation_content = load_file_content(OUTPUT_PATH / "ontology" / "validation.log")
            linaje_content = load_file_content(OUTPUT_PATH / "ontology" / "linaje.ttl")

            st.code(validation_content if validation_content is not None else "Log de validación no generado.", language="markdown")
            
            if linaje_content:
                st.code(linaje_content[:1000], language="turtle")
            else:
                 st.info("El Linaje RDF (TTL) aún no ha sido generado. Ejecute el Paso 2.")

        # 3. KPIs y Explicación RAGA (Paso 3)
        with st.expander("✅ RAGA: KPIs y Explicaciones (Hipótesis/Evidencia)"):
            kpis_content = load_file_content(OUTPUT_PATH / "raga" / "kpis.json")
            explain_content = load_file_content(OUTPUT_PATH / "raga" / "explain.json")
            
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.subheader("KPIs")
                safe_json_display(kpis_content)
            with col_k2:
                st.subheader("Explicación RAGA")
                safe_json_display(explain_content)

        # 4. Decisión del EEE-Gate (Paso 4)
        with st.expander("✅ EEE-Gate: Decisión de Publicación"):
            safe_json_display(load_file_content(OUTPUT_PATH / "ops" / "gate_report.json"))

        # 5. Evidencias y XBRL (Pasos 5 & 6)
        with st.expander("✅ Evidencias (Merkle) y XBRL (Salida Verificable)"):
            st.code(load_file_content(OUTPUT_PATH / "evidence" / "evidence_manifest.json"), language="json")
            
            xbrl_val_content = load_file_content(OUTPUT_PATH / "xbrl" / "validation.log")
            st.code(xbrl_val_content if xbrl_val_content is not None else "Log de validación XBRL no generado.", language="text")

        # 6. HITL Kappa (Paso 7)
        with st.expander("✅ HITL: Acuerdo Inter-Evaluador (Kappa de Cohen)"):
            safe_json_display(load_file_content(OUTPUT_PATH / "ops" / "hitl_kappa.json"))

        # 7. Paquete Final (Paso 8)
        with st.expander("📦 Paquete de Auditoría ZIP"):
            audit_dir = OUTPUT_PATH / "release" / "audit"
            
            if audit_dir.is_dir():
                zip_files = [f for f in audit_dir.glob("*.zip")]
                
                if zip_files:
                    st.success("✅ Paquete de Auditoría ZIP generado. ¡Descarga para auditar!")
                    
                    for zip_file_path in zip_files:
                        try:
                            # Leer el contenido del archivo como bytes (esencial para ZIPs)
                            zip_bytes = zip_file_path.read_bytes()
                            
                            # Crear el botón de descarga para Streamlit
                            st.download_button(
                                label=f"⬇️ Descargar: {zip_file_path.name}",
                                data=zip_bytes,
                                file_name=zip_file_path.name,
                                mime="application/zip",
                                key=zip_file_path.name
                            )
                        except Exception as e:
                            st.error(f"Error al preparar la descarga de {zip_file_path.name}: {e}")
                else:
                    st.info("El directorio de auditoría existe, pero aún no se ha generado el archivo ZIP (Ejecute el Paso 8).")
            else:
                 st.warning("El directorio 'release/audit' aún no ha sido creado. Ejecute los pasos del pipeline.")


# Ejecutar la aplicación principal
if __name__ == "__main__":
    main()
