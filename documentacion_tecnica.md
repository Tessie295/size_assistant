# Documentación Técnica: Asistente Inteligente de Tallas

## Descripción de la Arquitectura

### Arquitectura General
El sistema implementa una arquitectura **RAG (Retrieval-Augmented Generation)** modular que combina un motor de recomendaciones técnico con capacidades conversacionales de LLM. La arquitectura se compone de cinco capas principales:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                     │
├─────────────────────────────────────────────────────────────┤
│                Core Chatbot Orchestrator                    │
├─────────────────────────────────────────────────────────────┤
│  RAG Service  │  LLM Service  │  Conversation Manager       │
├─────────────────────────────────────────────────────────────┤
│           Size Recommendation Engine                        │
├─────────────────────────────────────────────────────────────┤
│           Data Layer (JSON + Data Models)                   │
└─────────────────────────────────────────────────────────────┘
```

### Componentes:

Dentro de los componentes más importantes encontramos el Servicio RAG (RAGService). Esta diseñado con un enfoque híbrido que combina técnicas clásicas de NLP con búsqueda estructurada. Utiliza expresiones regulares para ayudarse a extraer información de los clientes y productos almacenados, mediante keywords definidas como "talla", "fit", "mostrar" intenta descubrir la intencionalidad del mensaje por parte del usuario. Además recupera información relevante de los json disponibles.
Tiene en cuenta la similitud en las medidas de los clientes/productos, así como el historial de compras de los clientes si esta disponible.

Otros servicios importantes son:
- El motor de recomendaciones: un algoritmo multi-factor que combina medidas corporales, historial de compras y preferencias. Se le han añadido unas ponderaciones a ojo a cada uno de estos factores para establecer unos scores de relevancia que ayuden con las recomendaciones.

- El modelo LLM: se ha utilizado OpenAI GPT-3.5-turbo con el objetivo de equilibrar el coste con el rendimiento. Este modelo no es de lo más avanzados actualmente pero si tiene un buen rendimiento y resulta económico para las pruebas realizadas.

- Gestor de conversaciones: permite establecer turnos de conversación, mantener un seguimiento entre los clientes y productos de los cuáles se estan haciendo preguntas, así como construir una memoria de sesión (aunque esta no se almacene si se reinicia el servicio)

### Stack Tecnológico
**Frontend**: Streamlit - Prototipado rápido y interfaz conversacional intuitiva
**Datos**: JSON + Pydantic - Flexibilidad para prototipo, validación de tipos
**ML**: NumPy + Scikit-learn - Procesamiento numérico eficiente y algoritmos probados

## Supuestos y Limitaciones

Los datos proporcionados son básicos, aún así se asume que tanto las medidas corporales, como las tablas de tallas son precisas y coherentes.
El idioma para el cual se ha diseñado la aplicación es el español.
La generación de imágenes con OpenCV es muy básica, pero al no disponer de una GPU era la opción más viable.
Tampoco disponemos una base de datos que permita manejar los datos de forma más coḿoda que en JSON y almacenar información de sesión al reiniciar la app.

## Posibles Mejoras

Generar imágenes con modelos más especializados como Stable Diffusion, creación de una base de datos en PostgresSQL por ejemplo, crear un sistema de feedback para mejorar las respuestas del RAG...
