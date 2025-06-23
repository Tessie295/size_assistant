"""
Aplicación Streamlit para el chatbot de recomendaciones de tallas.
"""

import streamlit as st
import uuid
import json
from datetime import datetime
from core.chatbot import SizingChatbot


# Configuración de la página
st.set_page_config(
    page_title="Asistente de Tallas",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    
    .recommendation-box {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Función para inicializar el estado de la sesión
@st.cache_resource
def init_chatbot():
    """Inicializa el chatbot una sola vez."""
    return SizingChatbot()


def init_session_state():
    """Inicializa las variables de estado de la sesión."""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = init_chatbot()
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chatbot.start_conversation(st.session_state.session_id)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_recommendation' not in st.session_state:
        st.session_state.current_recommendation = None


def display_message(role: str, content: str, metadata: dict = None):
    """Muestra un mensaje en el chat."""
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "🧑‍💼" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.title()}:</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)


def display_recommendation(rec_data: dict):
    """Muestra una recomendación de talla de forma destacada."""
    if not rec_data:
        return
    
    st.markdown(f"""
    <div class="recommendation-box">
        <h4>📏 Recomendación de Talla</h4>
        <p><strong>Talla recomendada:</strong> {rec_data.get('size', 'N/A')}</p>
        <p><strong>Confianza:</strong> {rec_data.get('confidence', 0):.1%}</p>
        <p><strong>Alternativas:</strong> {', '.join(rec_data.get('alternatives', []))}</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Función principal de la aplicación."""
    
    # Inicializar estado
    init_session_state()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>👔 Asistente Inteligente de Tallas</h1>
        <p>Tu chatbot personal para encontrar la talla perfecta</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Área principal del chat
        st.markdown("### 💬 Conversación")
        
        # Contenedor para los mensajes
        chat_container = st.container()
        
        # Mostrar mensajes existentes
        with chat_container:
            for message in st.session_state.messages:
                display_message(
                    role=message["role"],
                    content=message["content"],
                    metadata=message.get("metadata")
                )
                
                # Mostrar recomendación si existe
                if message["role"] == "assistant" and "recommendation" in message:
                    display_recommendation(message["recommendation"])
        
        # Input del usuario
        with st.form(key="chat_form", clear_on_submit=True):
            col_input, col_button = st.columns([4, 1])
            
            with col_input:
                user_input = st.text_input(
                    "Escribe tu mensaje:",
                    placeholder="Ej: ¿Qué talla me recomiendas para el producto P001?",
                    label_visibility="collapsed"
                )
            
            with col_button:
                submit_button = st.form_submit_button("Enviar", use_container_width=True)
        
        # Procesar mensaje del usuario
        if submit_button and user_input:
            # Añadir mensaje del usuario
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Procesar con el chatbot
            with st.spinner("Pensando..."):
                response_data = st.session_state.chatbot.process_message(
                    user_input, st.session_state.session_id
                )
            
            # Añadir respuesta del asistente
            assistant_message = {
                "role": "assistant",
                "content": response_data["response"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Añadir información adicional si existe
            if "recommendation" in response_data:
                assistant_message["recommendation"] = response_data["recommendation"]
                st.session_state.current_recommendation = response_data["recommendation"]
            
            if "products" in response_data:
                assistant_message["products"] = response_data["products"]
            
            st.session_state.messages.append(assistant_message)
            
            # Rerun para mostrar la nueva respuesta
            st.rerun()
    
    with col2:
        # Sidebar con información adicional
        st.markdown("### ℹ️ Información de la Sesión")
        
        # Información de la sesión actual
        session_info = st.session_state.chatbot.get_session_info(st.session_state.session_id)
        
        with st.expander("📊 Estado de la Sesión"):
            st.write(f"**ID de Sesión:** {st.session_state.session_id[:8]}...")
            st.write(f"**Mensajes:** {len(st.session_state.messages)}")
            
            if session_info.get('active_client'):
                st.write(f"**Cliente Activo:** {session_info['active_client']}")
            
            if session_info.get('active_product'):
                st.write(f"**Producto Activo:** {session_info['active_product']}")
        
        # Recomendación actual
        if st.session_state.current_recommendation:
            with st.expander("📏 Última Recomendación", expanded=True):
                rec = st.session_state.current_recommendation
                st.metric("Talla Recomendada", rec.get('size', 'N/A'))
                st.metric("Confianza", f"{rec.get('confidence', 0):.1%}")
                
                if rec.get('alternatives'):
                    st.write("**Alternativas:**")
                    for alt in rec['alternatives']:
                        st.write(f"• {alt}")
        
        # Ejemplos de consultas
        with st.expander("💡 Ejemplos de Consultas"):
            st.markdown("""
            **Recomendaciones de talla:**
            - ¿Qué talla para el cliente C0001 del producto P001?
            - Talla para User5 en el abrigo P025
            
            **Búsqueda de productos:**
            - Busca productos de algodón
            - Muestra abrigos con ajuste slim
            
            **Información general:**
            - ¿Cómo funciona el sistema?
            - Ayuda con las recomendaciones
            """)
        
        # Clientes disponibles
        with st.expander("👥 Clientes Disponibles"):
            clients = st.session_state.chatbot.get_available_clients(limit=5)
            for client in clients:
                st.write(f"**{client['id']}** - {client['name']}")
                st.write(f"Preferencia: {client['preferred_fit']}, Altura: {client['height_cm']}cm")
                st.write("---")
        
        # Productos disponibles
        with st.expander("🛍️ Productos Disponibles"):
            products = st.session_state.chatbot.get_available_products(limit=5)
            for product in products:
                st.write(f"**{product['id']}** - {product['name']}")
                st.write(f"Ajuste: {product['fit']}, Material: {product['fabric']}")
                st.write("---")
        
        # Controles de sesión
        st.markdown("### ⚙️ Controles")
        
        col_clear, col_new = st.columns(2)
        
        with col_clear:
            if st.button("🗑️ Limpiar Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_recommendation = None
                st.rerun()
        
        with col_new:
            if st.button("🆕 Nueva Sesión", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.chatbot.start_conversation(st.session_state.session_id)
                st.session_state.messages = []
                st.session_state.current_recommendation = None
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        🤖 Asistente de Tallas v1.0 | Desarrollado con Streamlit y OpenAI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()