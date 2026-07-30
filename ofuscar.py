import json
import base64

# ============================================
# OFUSCAR DATA.JSON
# ============================================
def ofuscar_json():
    try:
        # 1. Leer el archivo data.json
        print("📖 Leyendo data.json...")
        with open('data.json', 'r', encoding='utf-8') as f:
            data = f.read()
        
        # 2. Codificar en Base64
        print("🔒 Codificando en Base64...")
        encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        
        # 3. Guardar como data.enc
        print("💾 Guardando data.enc...")
        with open('data.enc', 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print("✅ data.enc generado correctamente")
        print(f"📊 Tamaño original: {len(data)} caracteres")
        print(f"📊 Tamaño ofuscado: {len(encoded)} caracteres")
        
        # 4. Opcional: Mostrar los primeros 100 caracteres
        print(f"🔑 Muestra: {encoded[:50]}...")
        
    except FileNotFoundError:
        print("❌ Error: No se encontró data.json")
        print("📌 Asegúrate de que data.json existe en la misma carpeta")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🔐 OFUSCADOR DE DATA.JSON")
    print("=" * 50)
    ofuscar_json()