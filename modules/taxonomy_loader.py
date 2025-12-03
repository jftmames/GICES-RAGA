import pandas as pd
from pathlib import Path

def load_esrs_taxonomy(file_path):
    """
    Lee el mapeo oficial de Data Points (Excel/CSV) y extrae las coordenadas de búsqueda.
    Se enfoca en ESRS E4 (Biodiversidad) para la auditoría de ECOACSA.
    """
    path = Path(file_path)
    taxonomy = []
    
    print(f"📚 Cargando taxonomía desde: {path.name}...")
    
    try:
        # Detectar si es Excel o CSV y cargar
        if path.suffix in ['.xlsx', '.xls']:
            # Intentamos leer la pestaña específica de Biodiversidad si existe
            try:
                df = pd.read_excel(path, sheet_name="ESRS E4")
            except:
                # Si falla, leemos la primera o intentamos buscar la columna clave
                df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)

        # Normalizar nombres de columnas (quitar espacios extra)
        df.columns = [c.strip() for c in df.columns]
        
        # Filtrar solo el estándar de Biodiversidad (ESRS E4)
        # Asumimos que la columna se llama 'ESRS' o similar según el archivo oficial
        if 'ESRS' in df.columns:
            df = df[df['ESRS'] == 'E4']
        
        # Iterar sobre las filas para extraer los "Data Points"
        for _, row in df.iterrows():
            # Construimos un ID único: Ej "E4-5 (41 a)"
            dr = str(row.get('DR', '')).strip()
            para = str(row.get('Paragraph', '')).strip()
            full_id = f"{dr} - {para}" if para else dr
            
            # Descripción y Tipo de Dato (Narrativo vs Monetario/Numérico)
            desc = str(row.get('Name', '')).strip()
            dtype = str(row.get('Data Type', '')).strip()
            
            if dr and desc:
                taxonomy.append({
                    "id": full_id,
                    "dr_code": dr,
                    "description": desc,
                    "type": dtype,
                    "source_doc": "ESRS E4"
                })
                
        print(f"✅ Taxonomía cargada: {len(taxonomy)} puntos de control de Biodiversidad encontrados.")
        return taxonomy

    except Exception as e:
        print(f"⚠️ Error crítico leyendo taxonomía: {e}")
        return []

# --- BLOQUE DE PRUEBA (Para verificar que funciona solo) ---
if __name__ == "__main__":
    # Ajusta esta ruta al nombre real de tu archivo subido
    test_path = "data/01_draft-esrs-gri-standards-data-point-mapping.xlsx"
    if Path(test_path).exists():
        data = load_esrs_taxonomy(test_path)
        if data:
            print(f"Ejemplo: {data[0]}")
    else:
        print("⚠️ Archivo de prueba no encontrado. Configura la ruta correcta.")
