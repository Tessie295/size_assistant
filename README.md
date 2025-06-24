# 👔 Asistente Inteligente de Tallas

Un chatbot personalizado que utiliza LLM + RAG para recomendar tallas de ropa basándose en perfiles de clientes y catálogos de productos.

## 🚀 Características

- **Recomendaciones Personalizadas**: Análisis de medidas corporales, historial de compras y preferencias
- **Arquitectura RAG**: Búsqueda inteligente en datos estructurados
- **Memoria Conversacional**: Mantiene contexto entre turnos de conversación
- **Interfaz Intuitiva**: Aplicación web con Streamlit
- **Motor de Recomendaciones**: Algoritmo avanzado que combina múltiples factores

## 📁 Estructura del Proyecto

```
sizing-chatbot/
│
├── 📄 app.py                 # Aplicación Streamlit principal
├── 📄 requirements.txt       # Dependencias del proyecto
├── 📄 .env.example          # Ejemplo de configuración
│
├── 📂 data/                 # Datos del sistema
│   ├── client_profiles.json
│   └── product_catalog.json
│
├── 📂 models/               # Modelos de datos
│   └── data_models.py
│
├── 📂 engine/               # Motor de recomendaciones
│   └── size_recommendation_engine.py
│
├── 📂 services/             # Servicios del sistema
│   ├── llm_service.py       # Integración con OpenAI
│   ├── rag_service.py       # Servicio RAG
│   └── conversation_manager.py
│
└── 📂 core/                 # Núcleo del chatbot
    └── chatbot.py
```

## ⚙️ Instalación y Configuración

### 1. Clona el repositorio
```bash
git clone <tu-repositorio>
cd size_assistant
```

### 2. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 3. Configura tu API Key de OpenAI
```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env y añade tu API key
OPENAI_API_KEY=tu_api_key_aqui
```
### 4. Inicia la aplicación
```bash
streamlit run app.py
```

## 🎯 Cómo Usar

### Ejemplos de Consultas

**Recomendaciones de talla:**
- "¿Qué talla me recomiendas para el producto P001?"
- "Talla para el cliente C0001 del abrigo P025"
- "¿Cuál es la mejor talla para User5?"

**Búsqueda de productos:**
- "Busca productos de algodón"
- "Muestra abrigos con ajuste slim"
- "¿Qué productos tienes disponibles?"

**Información general:**
- "¿Cómo funciona el sistema?"
- "Ayuda con las recomendaciones"

### Formato de IDs

- **Clientes**: C0001, C0002, etc. (también User1, User2)
- **Productos**: P001, P002, etc.

## 🧠 Cómo Funciona

### 1. Análisis de Consulta (RAG)
- Parsea la consulta del usuario
- Identifica entidades (clientes, productos)
- Determina la intención (recomendación, búsqueda, ayuda)

### 2. Recuperación de Contexto
- Busca información relevante en los datos
- Encuentra clientes y productos mencionados
- Considera el historial de conversación

### 3. Motor de Recomendaciones
- **Análisis de medidas**: Compara medidas corporales con tabla de tallas
- **Historial de compras**: Aprende de experiencias previas
- **Preferencias de ajuste**: Considera preferencias personales
- **Características del producto**: Tipo de ajuste, material, etc.

### 4. Generación de Respuesta (LLM)
- Utiliza GPT-3.5-turbo para generar respuestas naturales
- Incluye justificaciones técnicas
- Proporciona alternativas y consejos adicionales

## 📊 Algoritmo de Recomendación

El motor de recomendaciones utiliza un enfoque multi-factor:

```python
Score_Final = (
    Score_Medidas * 0.6 +
    Ajuste_Historial * 0.25 +
    Ajuste_Preferencias * 0.15
)
```

### Factores Considerados:

1. **Medidas Corporales (60%)**
   - Diferencia entre medidas del cliente y tabla de tallas
   - Pesos: Busto (40%), Cintura (35%), Cadera (25%)

2. **Historial de Compras (25%)**
   - Feedback de compras anteriores
   - Patrones de satisfacción por talla

3. **Preferencias de Ajuste (15%)**
   - Compatibilidad entre preferencia del cliente y tipo de prenda
   - Ajustes específicos por estilo

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
OPENAI_API_KEY=tu_api_key        # Requerido
OPENAI_MODEL=gpt-3.5-turbo       # Opcional, default: gpt-3.5-turbo
MAX_CONVERSATION_TURNS=10        # Opcional, default: 10
```

### Personalización del Motor
El archivo `engine/size_recommendation_engine.py` permite ajustar:
- Pesos de los factores de recomendación
- Algoritmos de similitud
- Criterios de confianza
