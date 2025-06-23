"""
Script de configuración y verificación del proyecto.
"""

import os
import json
import sys
from pathlib import Path


def create_directory_structure():
    """Crea la estructura de directorios necesaria."""
    directories = [
        "data",
        "models",
        "engine",
        "services", 
        "core"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        # Crear __init__.py para que sean paquetes de Python
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
    
    print("✅ Estructura de directorios creada")


def copy_data_files():
    """Copia los archivos JSON a la carpeta data si no existen."""
    data_dir = Path("data")
    
    # Crear archivos de ejemplo si no existen
    client_file = data_dir / "client_profiles.json"
    product_file = data_dir / "product_catalog.json"
    
    if not client_file.exists():
        print("⚠️  client_profiles.json no encontrado en data/")
        print("   Por favor, copia el archivo client_profiles.json a la carpeta data/")
    
    if not product_file.exists():
        print("⚠️  product_catalog.json no encontrado en data/")
        print("   Por favor, copia el archivo product_catalog.json a la carpeta data/")
    
    if client_file.exists() and product_file.exists():
        print("✅ Archivos de datos encontrados")
        return True
    
    return False


def check_requirements():
    """Verifica que las dependencias estén instaladas."""
    required_packages = [
        "streamlit",
        "openai",
        "pandas",
        "numpy",
        "python-dotenv",
        "scikit-learn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Faltan dependencias:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstala las dependencias con:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True


def check_env_file():
    """Verifica la configuración del archivo .env."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        print("   1. Copia .env.example a .env")
        print("   2. Añade tu API key de OpenAI")
        return False
    
    # Verificar que contenga la API key
    with open(env_file, 'r') as f:
        content = f.read()
        if "OPENAI_API_KEY=" in content and "tu_api_key_aqui" not in content:
            print("✅ Archivo .env configurado")
            return True
        else:
            print("⚠️  API key de OpenAI no configurada en .env")
            return False


def validate_data_files():
    """Valida que los archivos JSON tengan el formato correcto."""
    data_dir = Path("data")
    
    try:
        # Validar client_profiles.json
        with open(data_dir / "client_profiles.json", 'r') as f:
            clients_data = json.load(f)
            if isinstance(clients_data, list) and len(clients_data) > 0:
                print(f"✅ {len(clients_data)} clientes cargados")
            else:
                print("❌ Formato incorrecto en client_profiles.json")
                return False
        
        # Validar product_catalog.json
        with open(data_dir / "product_catalog.json", 'r') as f:
            products_data = json.load(f)
            if isinstance(products_data, list) and len(products_data) > 0:
                print(f"✅ {len(products_data)} productos cargados")
            else:
                print("❌ Formato incorrecto en product_catalog.json")
                return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error en formato JSON: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
        return False


def test_basic_functionality():
    """Prueba la funcionalidad básica del sistema."""
    try:
        from core.chatbot import SizingChatbot
        
        print("🧪 Probando inicialización del chatbot...")
        chatbot = SizingChatbot()
        
        if chatbot.is_initialized:
            print("✅ Chatbot inicializado correctamente")
            
            # Prueba básica
            session_id = chatbot.start_conversation()
            response = chatbot.process_message("¿Qué talla para el cliente C0001 del producto P001?", session_id)
            
            if not response.get("error"):
                print("✅ Prueba básica exitosa")
                return True
            else:
                print(f"❌ Error en prueba básica: {response.get('error_details')}")
                return False
        else:
            print("❌ Error en la inicialización del chatbot")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de funcionalidad: {e}")
        return False


def create_run_script():
    """Crea un script para ejecutar la aplicación."""
    run_script = Path("run.py")
    
    script_content = '''#!/usr/bin/env python3
"""
Script para ejecutar la aplicación Streamlit.
"""

import subprocess
import sys
import os

def main():
    """Ejecuta la aplicación Streamlit."""
    print("🚀 Iniciando el Asistente de Tallas...")
    print("📂 Abriendo en tu navegador...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\n👋 ¡Hasta luego!")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
    
    with open(run_script, 'w') as f:
        f.write(script_content)
    
    # Hacer el script ejecutable en sistemas Unix
    if os.name != 'nt':
        os.chmod(run_script, 0o755)
    
    print("✅ Script de ejecución creado (run.py)")


def main():
    """Función principal de configuración."""
    print("🔧 Configurando el proyecto...")
    print("=" * 50)
    
    # Lista de verificaciones
    checks = [
        ("Estructura de directorios", create_directory_structure),
        ("Archivos de datos", copy_data_files),
        # ("Dependencias", check_requirements),
        ("Configuración .env", check_env_file),
        ("Validación de datos", validate_data_files),
        ("Funcionalidad básica", test_basic_functionality)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        try:
            result = check_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ Error en {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ¡Configuración completada exitosamente!")
        create_run_script()
        print("\n📋 Para ejecutar la aplicación:")
        print("   python run.py")
        print("   o")
        print("   streamlit run app.py")
    else:
        print("❌ Hay problemas en la configuración. Revisa los errores arriba.")
        print("\n📋 Para solucionar:")
        print("   1. Instala dependencias: pip install -r requirements.txt")
        print("   2. Configura .env con tu API key de OpenAI")
        print("   3. Copia los archivos JSON a la carpeta data/")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)