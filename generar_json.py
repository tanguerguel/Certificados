import json
import re
import zipfile
import xml.etree.ElementTree as ET
import base64
import json

# ============================================
# CONFIGURACIÓN
# ============================================
ARCHIVO_EXCEL = 'LISTA ORDENADA.xlsx'
ARCHIVO_SALIDA = 'data.json'
DNI_POR_DEFECTO = "12345678"  # DNI vacío por defecto

# ============================================
# FUNCIONES
# ============================================
def leer_excel_sin_pandas(archivo):
    try:
        with zipfile.ZipFile(archivo, 'r') as zip_ref:
            strings = []
            try:
                with zip_ref.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    namespace = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in root.findall('.//ns:si', namespace):
                        t = si.find('.//ns:t', namespace)
                        if t is not None:
                            strings.append(t.text if t.text else '')
                        else:
                            text_parts = []
                            for t in si.findall('.//ns:t', namespace):
                                if t.text:
                                    text_parts.append(t.text)
                            strings.append(''.join(text_parts) if text_parts else '')
            except:
                pass
            
            with zip_ref.open('xl/worksheets/sheet1.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                namespace = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                
                rows = []
                for row in root.findall('.//ns:row', namespace):
                    row_data = []
                    for cell in row.findall('.//ns:c', namespace):
                        cell_value = ''
                        cell_type = cell.get('t')
                        if cell_type == 's':
                            v = cell.find('.//ns:v', namespace)
                            if v is not None and v.text:
                                try:
                                    idx = int(v.text)
                                    if idx < len(strings):
                                        cell_value = strings[idx]
                                except:
                                    cell_value = v.text
                        else:
                            v = cell.find('.//ns:v', namespace)
                            if v is not None and v.text:
                                cell_value = v.text
                        row_data.append(cell_value)
                    rows.append(row_data)
                return rows
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return None

def limpiar_nombre(nombre):
    if not nombre:
        return None
    nombre = str(nombre).strip()
    nombre = nombre.replace(',', '')
    nombre = nombre.replace('.', '')
    nombre = ' '.join(nombre.split())
    return nombre

def limpiar_dni(dni):
    if not dni:
        return DNI_POR_DEFECTO
    dni = str(dni).strip()
    dni = re.sub(r'[^0-9]', '', dni)
    if not dni:
        return DNI_POR_DEFECTO
    return dni

def obtener_curso(texto):
    if not texto:
        return None
    texto = str(texto).strip().upper()
    if 'ASHANINKA' in texto:
        return 'ashaninka'
    elif 'MATSIGENKA' in texto:
        return 'matsigenka'
    elif 'INGLES' in texto or 'INGLÉS' in texto:
        return 'ingles'
    elif 'QUECHUA' in texto:
            return 'quechua'
    elif 'BLOQUE' in texto:
        return 'ingles'
    return None

def es_numero_registro(valor):
    if not valor:
        return False
    try:
        num = int(str(valor).strip().replace(',', '').replace('.', ''))
        return True
    except:
        return False

def obtener_numero_registro(valor):
    if not valor:
        return None
    try:
        return int(str(valor).strip().replace(',', '').replace('.', ''))
    except:
        return None

def formatear_id(numero):
    return str(numero).zfill(5)

# ============================================
# PROCESAR EXCEL
# ============================================
def procesar_excel():
    print("=" * 60)
    print("🔄 GENERADOR DE data.json")
    print("=" * 60)
    print(f"📌 DNI por defecto: '{DNI_POR_DEFECTO}'")
    print("")
    
    rows = leer_excel_sin_pandas(ARCHIVO_EXCEL)
    if not rows:
        print("❌ No se pudo leer el archivo Excel")
        return None
    
    print(f"✅ Archivo {ARCHIVO_EXCEL} leído correctamente")
    print(f"📊 Filas totales: {len(rows)}")
    
    # Mostrar primeras filas para depuración
    print("\n📋 Primeras filas del Excel:")
    for i in range(min(5, len(rows))):
        print(f"   Fila {i}: {rows[i]}")
    print("")
    
    usuarios = []
    curso_actual = None
    contador_id = 1
    primer_registro_encontrado = False
    
    for i, row in enumerate(rows):
        # Asegurar que la fila tenga al menos 7 columnas
        while len(row) < 7:
            row.append('')
        
        col_orden = row[0] if row[0] else None
        col_nombre = row[1] if row[1] else None
        col_obs = row[2] if row[2] else None
        col_detalle = row[3] if len(row) > 3 and row[3] else None
        col_dni = row[4] if len(row) > 4 and row[4] else None
        col_estado_qr = row[5] if len(row) > 5 and row[5] else None
        col_curso = row[6] if len(row) > 6 and row[6] else None
        
        # ============================================
        # DETECTAR CURSO (solo si no es cabecera)
        # ============================================
        # Si la fila tiene "ORDEN DE" es la cabecera, la saltamos
        if col_orden and "ORDEN" in str(col_orden).upper():
            print("📋 Saltando cabecera...")
            continue
        
        # Detectar curso en col_curso
        if col_curso:
            curso_detectado = obtener_curso(col_curso)
            if curso_detectado:
                curso_actual = curso_detectado
                print(f"📚 Curso: {curso_actual} (fila {i+1})")
        
        # Detectar curso en col_orden (bloques como "MATSIGENKA", "BLOQUE F")
        if col_orden and not col_nombre:
            curso_detectado = obtener_curso(col_orden)
            if curso_detectado:
                curso_actual = curso_detectado
                print(f"📚 Cambiando a curso: {curso_actual} (fila {i+1})")
                continue
        
        # ============================================
        # PROCESAR REGISTRO
        # ============================================
        if col_orden and col_nombre:
            if es_numero_registro(col_orden):
                numero = obtener_numero_registro(col_orden)
                if numero and curso_actual:
                    numero_formateado = str(numero).zfill(5)
                    nombre = limpiar_nombre(col_nombre)
                    dni = limpiar_dni(col_dni)
                    
                    # Saltar si tiene observación
                    if col_obs and str(col_obs).strip() != '':
                        print(f"⏭️ Saltando: {nombre} (OBSERVADO: {col_obs})")
                        continue
                    
                    if nombre:
                        usuario = {
                            "id": formatear_id(contador_id),
                            "nombre": nombre,
                            "contrasena": numero_formateado,
                            "num_registro": numero_formateado,
                            "DNI": dni,
                            "curso": curso_actual
                        }
                        usuarios.append(usuario)
                        contador_id += 1
                        
                        if not primer_registro_encontrado:
                            primer_registro_encontrado = True
                            print(f"✅ PRIMER REGISTRO: ID {usuario['id']}: {nombre}")
                        
                        # Mostrar cada 10 registros
                        if contador_id % 10 == 0:
                            dni_mostrar = dni if dni else "(vacío)"
                            print(f"   ... ID {usuario['id']}: {nombre[:30]} → {curso_actual} (DNI: {dni_mostrar})")
    
    # ============================================
    # GUARDAR JSON
    # ============================================
    if not usuarios:
        print("❌ No se encontraron usuarios")
        return None
    
    data = {"usuarios": usuarios}
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ {len(usuarios)} usuarios procesados")
    print(f"📁 Guardado en: {ARCHIVO_SALIDA}")
    print(f"📊 Primer usuario: {usuarios[0]['nombre']} (ID: {usuarios[0]['id']})")
    print(f"📊 Último usuario: {usuarios[-1]['nombre']} (ID: {usuarios[-1]['id']})")
    print("=" * 60)
    return data

# ============================================
# GENERAR OFUSCACION
# ============================================

def generar_archivo_ofuscado():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = f.read()
        
        encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        
        with open('data.enc', 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print("✅ data.enc generado automáticamente")
    except Exception as e:
        print(f"⚠️ No se pudo generar data.enc: {e}")
# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    procesar_excel()