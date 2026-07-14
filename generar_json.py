import json
import csv

# ============================================
# CONFIGURACIÓN
# ============================================
ARCHIVO_CSV = 'LISTA ORDENADA.csv'
ARCHIVO_SALIDA = 'data.json'

# ============================================
# FUNCIONES
# ============================================
def formatear_id(numero):
    """Convierte un número a 5 dígitos con ceros a la izquierda"""
    return str(numero).zfill(5)

def limpiar_nombre(nombre):
    """Limpia el nombre de caracteres especiales y espacios extras"""
    if not nombre:
        return None
    nombre = nombre.strip()
    # Eliminar comas y puntos extra
    nombre = nombre.replace(',', '')
    nombre = nombre.replace('.', '')
    # Eliminar espacios múltiples
    nombre = ' '.join(nombre.split())
    return nombre

def es_curso_valido(texto):
    """Verifica si el texto es un nombre de curso válido"""
    if not texto:
        return False
    texto = texto.strip().upper()
    cursos_validos = ['ASHANINKA', 'MATSIGENKA', 'INGLES', 'BLOQUE']
    for curso in cursos_validos:
        if curso in texto:
            return True
    return False

def obtener_curso(texto):
    """Extrae el curso del texto del bloque"""
    if not texto:
        return None
    texto = texto.strip().upper()
    
    if 'ASHANINKA' in texto:
        return 'ashaninka'
    elif 'MATSIGENKA' in texto:
        return 'matsigenka'
    elif 'INGLES' in texto or 'BLOQUE' in texto:
        return 'ingles'
    return None

def normalizar_curso(curso):
    """Normaliza el nombre del curso"""
    if not curso:
        return None
    curso = curso.strip().upper()
    if curso == 'INGLES' or curso == 'INGLÉS':
        return 'ingles'
    elif curso == 'ASHANINKA':
        return 'ashaninka'
    elif curso == 'MATSIGENKA':
        return 'matsigenka'
    return None

# ============================================
# PROCESAR CSV
# ============================================
def procesar_csv():
    usuarios = []
    curso_actual = None
    contador_id = 1
    
    try:
        with open(ARCHIVO_CSV, 'r', encoding='utf-8') as f:
            # Usar punto y coma como delimitador
            reader = csv.reader(f, delimiter=';')
            
            for row in reader:
                # Limpiar fila - eliminar celdas vacías al final
                row = [cell.strip() if cell else '' for cell in row]
                
                # Tomar solo las primeras 3 columnas que nos interesan
                col_a = row[0] if len(row) > 0 else ''
                col_b = row[1] if len(row) > 1 else ''
                col_c = row[2] if len(row) > 2 else ''
                
                # Saltar filas vacías
                if not col_a and not col_b and not col_c:
                    continue
                
                # ============================================
                # DETECTAR CURSO (col_a tiene el nombre del curso)
                # ============================================
                if col_a and not col_b:
                    # Verificar si col_a es un curso
                    if es_curso_valido(col_a):
                        nuevo_curso = obtener_curso(col_a)
                        if nuevo_curso:
                            curso_actual = nuevo_curso
                            print(f"📚 Cambiando a curso: {curso_actual}")
                        continue
                    # Si col_a tiene texto y col_b vacío, podría ser curso
                    elif col_a and not col_b:
                        # Verificar si col_a contiene un curso
                        for curso in ['ASHANINKA', 'MATSIGENKA', 'BLOQUE']:
                            if curso in col_a.upper():
                                nuevo_curso = obtener_curso(col_a)
                                if nuevo_curso:
                                    curso_actual = nuevo_curso
                                    print(f"📚 Cambiando a curso: {curso_actual}")
                                break
                        continue
                
                # ============================================
                # DETECTAR CURSO EN COL_C (tiene el curso explícito)
                # ============================================
                if col_c and col_c.strip():
                    curso_normalizado = normalizar_curso(col_c)
                    if curso_normalizado:
                        curso_actual = curso_normalizado
                        print(f"📚 Curso explícito: {curso_actual}")
                
                # ============================================
                # PROCESAR REGISTRO (col_a = número, col_b = nombre)
                # ============================================
                if col_a and col_b:
                    # Verificar si col_a es un número (registro)
                    try:
                        # Limpiar col_a (eliminar espacios y caracteres)
                        num_str = col_a.strip()
                        # Si tiene comas, puntos, etc.
                        num_str = num_str.replace(',', '').replace('.', '')
                        if num_str.isdigit():
                            numero_registro = int(num_str)
                            numero_formateado = str(numero_registro).zfill(5)
                            nombre = limpiar_nombre(col_b)
                            
                            if nombre and curso_actual:
                                # Crear usuario
                                usuario = {
                                    "id": formatear_id(contador_id),
                                    "nombre": nombre,
                                    "contrasena": numero_formateado,
                                    "num_registro": numero_formateado,
                                    "DNI": "",
                                    "curso": curso_actual
                                }
                                usuarios.append(usuario)
                                contador_id += 1
                                print(f"✅ ID {usuario['id']}: {nombre[:30]}... → {curso_actual}")
                    except:
                        # Si falla, no es un registro
                        pass
                    
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ARCHIVO_CSV}")
        print("📌 Asegúrate de que el archivo esté en la misma carpeta")
        return None
    
    # ============================================
    # GUARDAR JSON
    # ============================================
    if not usuarios:
        print("❌ No se encontraron usuarios")
        print("📌 Verifica que el CSV tenga el formato correcto")
        return None
    
    data = {"usuarios": usuarios}
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {len(usuarios)} usuarios procesados")
    print(f"📁 Guardado en: {ARCHIVO_SALIDA}")
    print(f"📊 Último ID: {usuarios[-1]['id']}")
    return data

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("🔄 GENERADOR DE data.json")
    print("=" * 60)
    procesar_csv()