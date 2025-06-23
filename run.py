#!/usr/bin/env python3
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
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)

if __name__ == "__main__":
    main()
