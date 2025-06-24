import streamlit as st
import uuid
import base64
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Asistente de Tallas",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #9c27b0;
    }
    
    .recommendation-box {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    
    .visual-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    
    .status-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #6c757d;
    }
    
    .quick-action-btn {
        margin: 0.25rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar chatbot
@st.cache_resource
def init_chatbot():
    """Inicializa el chatbot una sola vez."""
    try:
        from core.chatbot import SizingChatbot
        chatbot = SizingChatbot()
        return chatbot
    except ImportError as e:
        st.error(f"Error importando chatbot: {e}")
        return None
    except Exception as e:
        st.error(f"Error inicializando chatbot: {e}")
        return None

def init_session_state():
    """Inicializa las variables de estado de la sesión."""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = init_chatbot()
    
    if 'session_id' not in st.session_state and st.session_state.chatbot:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chatbot.start_conversation(st.session_state.session_id)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_recommendation' not in st.session_state:
        st.session_state.current_recommendation = None
    
    if 'current_visual' not in st.session_state:
        st.session_state.current_visual = None
    
    if 'message_counter' not in st.session_state:
        st.session_state.message_counter = 0

def display_system_status():
    """Estado del sistema"""
    st.markdown("### 🔧 Estado del Sistema")
    
    if not st.session_state.chatbot:
        st.markdown('<div class="status-error">❌ Sistema: No disponible</div>', unsafe_allow_html=True)
        st.markdown("""
        **Para solucionar:**
        1. Verifica que `client_profiles.json` y `product_catalog.json` estén en `data/`
        2. Ejecuta `python test_final.py`
        3. Instala dependencias: `pip install -r requirements_visual.txt`
        """)
        return False
    
    if not st.session_state.chatbot.is_initialized:
        st.markdown('<div class="status-error">❌ Chatbot: No inicializado</div>', unsafe_allow_html=True)
        return False
    
    # Estado del chatbot
    st.markdown('<div class="status-success">✅ Chatbot: Operativo</div>', unsafe_allow_html=True)
    
    # Información de datos
    data_loader = st.session_state.chatbot.data_loader
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👥 Clientes", len(data_loader.clients))
    with col2:
        st.metric("🛍️ Productos", len(data_loader.products))
    
    # Estado LLM
    llm_type = "OpenAI" if st.session_state.chatbot.llm_service.use_openai else "Local"
    if llm_type == "OpenAI":
        st.markdown('<div class="status-success">✅ LLM: OpenAI conectado</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⚠️ LLM: Modo local (sin OpenAI)</div>', unsafe_allow_html=True)
    
    # Estado visual
    if (st.session_state.chatbot.visual_service and 
        st.session_state.chatbot.visual_service.is_available()):
        st.markdown('<div class="status-success">✅ Visual: Operativo</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⚠️ Visual: PIL no disponible</div>', unsafe_allow_html=True)
        if st.button("📦 Instalar Pillow", key="install_pillow"):
            st.code("pip install Pillow")
    
    return True

def display_message(role: str, content: str):
    """Muestra un mensaje en el chat."""
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "🧑‍💼" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.title()}:</strong><br>
        {content.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

def display_recommendation(rec_data: dict):
    """Muestra una recomendación de talla."""
    if not rec_data:
        return
    
    confidence = rec_data.get('confidence', 0)
    confidence_color = "#4caf50" if confidence > 0.8 else "#ff9800" if confidence > 0.6 else "#f44336"
    
    st.markdown(f"""
    <div class="recommendation-box">
        <h4>📏 Recomendación de Talla</h4>
        <div style="display: flex; align-items: center; margin: 1rem 0;">
            <div style="font-size: 2rem; margin-right: 1rem;">👕</div>
            <div>
                <p style="margin: 0; font-size: 1.2rem;"><strong>Talla recomendada: {rec_data.get('size', 'N/A')}</strong></p>
                <p style="margin: 0; color: {confidence_color};"><strong>Confianza: {confidence:.1%}</strong></p>
            </div>
        </div>
        <p><strong>Alternativas:</strong> {', '.join(rec_data.get('alternatives', [])) or 'Ninguna'}</p>
    </div>
    """, unsafe_allow_html=True)

def display_visual_content(visual_data: dict, message_id: int):
    """Muestra el contenido visual generado."""
    if not visual_data:
        return
        
    if not visual_data.get('success'):
        st.error(f"❌ Error generando imagen: {visual_data.get('error', 'Error desconocido')}")
        return
    
    st.markdown("""
    <div class="visual-box">
        <h4>🖼️ Visualización Generada</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar la imagen
    if visual_data.get('base64'):
        try:
            from PIL import Image
            
            # Decodificar base64
            img_data = base64.b64decode(visual_data['base64'])
            img = Image.open(BytesIO(img_data))
            
            # Mostrar imagen centrada
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(
                    img, 
                    caption=f"👤 {visual_data.get('client_id')} | 👕 {visual_data.get('product_id')} | 📏 {visual_data.get('size')} | 🎨 {visual_data.get('color', 'azul').title()}",
                    use_container_width=True
                )
            
            # Información adicional
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Imagen guardada: `{visual_data.get('filename')}`")
            with col2:
                # Usar un key único para cada botón basado en message_id
                if st.button("🔄 Generar otra imagen", key=f"regen_image_{message_id}"):
                    st.info("💡 Prueba con otro color: 'Muestra el mismo producto en rojo'")
            
        except Exception as e:
            st.error(f"Error mostrando imagen: {e}")
    else:
        st.warning("⚠️ No se pudo generar la visualización")

# def create_quick_actions():
#     """Crea botones de acción rápida."""
#     st.markdown("### 🚀 Acciones Rápidas")
    
#     # Ejemplos básicos
#     st.markdown("**📏 Recomendaciones:**")
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("👤 C0001 + 👕 P001", key="quick1", help="¿Qué talla del producto P001 para el cliente C0001?"):
#             return "¿Qué talla del producto P001 para el cliente C0001?"
    
#     with col2:
#         if st.button("👤 User5 + 👕 P025", key="quick2", help="Talla para User5 del producto P025"):
#             return "¿Qué talla del producto P025 para User5?"
    
#     # Ejemplos visuales si están disponibles
#     if (st.session_state.chatbot and 
#         st.session_state.chatbot.visual_service and 
#         st.session_state.chatbot.visual_service.is_available()):
        
#         st.markdown("**🖼️ Visualizaciones:**")
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             if st.button("🔵 P001 azul C0001", key="visual1"):
#                 return "Muestra el producto P001 en azul para el cliente C0001"
        
#         with col2:
#             if st.button("🔴 P005 rojo C0002", key="visual2"):
#                 return "Ver imagen del cliente C0002 con el producto P005 en rojo"
        
#         with col3:
#             if st.button("🟢 P010 verde User3", key="visual3"):
#                 return "Muestra P010 en verde para User3"
    
#     # Búsquedas
#     st.markdown("**🔍 Búsquedas:**")
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("🧵 Productos de lana", key="search1"):
#             return "Busca productos de lana"
    
#     with col2:
#         if st.button("📐 Ajuste slim", key="search2"):
#             return "Productos con ajuste slim"
    
#     return None

# def create_color_picker():
#     """Crea un selector de colores visual."""
#     st.markdown("### 🎨 Colores Disponibles")
    
#     colors = {
#         "🔵": "azul", "🔴": "rojo", "🟢": "verde", "⚫": "negro", 
#         "⚪": "blanco", "🩶": "gris", "🌸": "rosa", "🟡": "amarillo",
#         "🟣": "morado", "🟠": "naranja"
#     }
    
#     cols = st.columns(5)
#     selected_color = None
    
#     for i, (emoji, color) in enumerate(colors.items()):
#         with cols[i % 5]:
#             if st.button(f"{emoji} {color.title()}", key=f"color_{color}"):
#                 selected_color = color
    
#     if selected_color:
#         st.session_state.selected_color = selected_color
#         st.success(f"Color seleccionado: {selected_color.title()}")
#         return selected_color
    
#     return None

def main():
    """Función principal de la aplicación."""
    
    # Inicializar estado
    init_session_state()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>👗 Asistente Inteligente de Tallas</h1>
        <p>Sistema avanzado de recomendaciones con IA y visualización</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout principal
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Área principal del chat
        st.markdown("### 💬 Conversación")
        
        # Verificar estado del sistema
        if not display_system_status():
            st.stop()
        
        # Mostrar mensajes existentes
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                display_message(message["role"], message["content"])
                
                # Mostrar recomendación si existe
                if message["role"] == "assistant" and "recommendation" in message:
                    display_recommendation(message["recommendation"])
                
                # Mostrar contenido visual si existe (con ID único)
                if message["role"] == "assistant" and "visual" in message:
                    display_visual_content(message["visual"], i)
        
        # Input del usuario
        st.markdown("---")
        
        # Usar formulario para mejor UX
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Tu mensaje:",
                placeholder="Ej: Muestra el producto P001 en azul para el cliente C0001",
                height=80,
                help="Puedes usar IDs como C0001, P001 o User1, User2, etc."
            )
            
            col_send, col_clear, col_help = st.columns([2, 1, 1])
            
            with col_send:
                send_button = st.form_submit_button("📤 Enviar", use_container_width=True)
            
            with col_clear:
                if st.form_submit_button("🗑️ Limpiar", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.current_recommendation = None
                    st.session_state.current_visual = None
                    st.session_state.message_counter = 0
                    st.rerun()
            
            with col_help:
                if st.form_submit_button("❓ Ayuda", use_container_width=True):
                    user_input = "ayuda"
                    send_button = True
        
        # Acciones rápidas
        # quick_message = create_quick_actions()
        # if quick_message:
        #     user_input = quick_message
        #     send_button = True
        
        # Procesar mensaje
        if send_button and user_input:
            # Incrementar contador de mensajes
            st.session_state.message_counter += 1
            
            # Añadir mensaje del usuario
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat(),
                "id": st.session_state.message_counter
            })
            
            # Procesar con el chatbot
            with st.spinner("🤖 Procesando tu consulta..."):
                try:
                    response_data = st.session_state.chatbot.process_message(
                        user_input, st.session_state.session_id
                    )
                except Exception as e:
                    response_data = {
                        "response": f"Lo siento, ocurrió un error: {str(e)}",
                        "error": True
                    }
            
            # Incrementar contador para respuesta del asistente
            st.session_state.message_counter += 1
            
            # Añadir respuesta del asistente
            assistant_message = {
                "role": "assistant",
                "content": response_data.get("response", "Error generando respuesta"),
                "timestamp": datetime.now().isoformat(),
                "id": st.session_state.message_counter
            }
            
            # Añadir información adicional
            if "recommendation" in response_data:
                assistant_message["recommendation"] = response_data["recommendation"]
                st.session_state.current_recommendation = response_data["recommendation"]
            
            if "visual" in response_data:
                assistant_message["visual"] = response_data["visual"]
                st.session_state.current_visual = response_data["visual"]
            
            st.session_state.messages.append(assistant_message)
            st.rerun()
    
    with col2:
        # Sidebar con información y controles
        st.markdown("### ℹ️ Panel de Control")
        
        # Información de la sesión
        if st.session_state.chatbot:
            session_info = st.session_state.chatbot.get_session_info(st.session_state.session_id)
            
            with st.expander("📊 Sesión Actual", expanded=True):
                st.metric("💬 Mensajes", len(st.session_state.messages))
                st.metric("🔗 Sesión", st.session_state.session_id[:8] + "...")
                
                if session_info.get('active_client'):
                    st.info(f"👤 Cliente Activo: **{session_info['active_client']}**")
                
                if session_info.get('active_product'):
                    st.info(f"👕 Producto Activo: **{session_info['active_product']}**")
        
        # Última recomendación
        if st.session_state.current_recommendation:
            with st.expander("📏 Última Recomendación", expanded=True):
                rec = st.session_state.current_recommendation
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Talla", rec.get('size', 'N/A'))
                with col2:
                    st.metric("Confianza", f"{rec.get('confidence', 0):.1%}")
                
                if rec.get('alternatives'):
                    st.write("**Alternativas:**")
                    for alt in rec['alternatives']:
                        st.write(f"• {alt}")
        
        # Última visualización
        if st.session_state.current_visual and st.session_state.current_visual.get('success'):
            with st.expander("🖼️ Última Visualización", expanded=True):
                visual = st.session_state.current_visual
                
                st.write(f"**Cliente:** {visual.get('client_id', 'N/A')}")
                st.write(f"**Producto:** {visual.get('product_id', 'N/A')}")
                st.write(f"**Talla:** {visual.get('size', 'N/A')}")
                st.write(f"**Color:** {visual.get('color', 'N/A')}")
                
                if st.button("🔄 Regenerar", key="regen_last"):
                    last_visual_cmd = f"Muestra {visual.get('product_id')} en {visual.get('color')} para {visual.get('client_id')}"
                    st.session_state.message_counter += 1
                    st.session_state.messages.append({
                        "role": "user",
                        "content": last_visual_cmd,
                        "timestamp": datetime.now().isoformat(),
                        "id": st.session_state.message_counter
                    })
                    st.rerun()
        
        # Selector de colores
        # create_color_picker()
        
        # Datos disponibles
        with st.expander("📋 Datos del Sistema"):
            if st.session_state.chatbot:
                clients = st.session_state.chatbot.get_available_clients(3)
                products = st.session_state.chatbot.get_available_products(3)
                
                st.markdown("**👥 Clientes (muestra):**")
                for client in clients:
                    st.write(f"• `{client['id']}` - {client['name']} ({client['preferred_fit']}, {client['height_cm']}cm)")
                
                st.markdown("**🛍️ Productos (muestra):**")
                for product in products:
                    st.write(f"• `{product['id']}` - {product['name']} ({product['fit']}, {product['fabric']})")
        
        # Ejemplos y ayuda
        with st.expander("💡 Ejemplos de Consultas"):
            st.markdown("""
            **📏 Recomendaciones básicas:**
            - ¿Qué talla para C0001 del P001?
            - Talla para User5 del producto P025
            
            **🖼️ Con visualización:**
            - Muestra P001 en azul para C0001
            - Ver imagen de C0002 con P010
            - P005 en rojo para User3
            
            **🔍 Búsquedas:**
            - Busca productos de lana
            - Productos con ajuste slim
            - Qué tiene User2
            """)
        
        # Controles de sesión
        st.markdown("---")
        st.markdown("### ⚙️ Controles")
        
        if st.button("🆕 Nueva Sesión", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            if st.session_state.chatbot:
                st.session_state.chatbot.start_conversation(st.session_state.session_id)
            st.session_state.messages = []
            st.session_state.current_recommendation = None
            st.session_state.current_visual = None
            st.session_state.message_counter = 0
            st.rerun()
        
        if (st.session_state.chatbot and 
            st.session_state.chatbot.visual_service and 
            st.session_state.chatbot.visual_service.is_available()):
            
            if st.button("🧹 Limpiar Imágenes", use_container_width=True):
                try:
                    st.session_state.chatbot.visual_service.cleanup_old_images()
                    st.success("✅ Imágenes antiguas eliminadas")
                except Exception as e:
                    st.error(f"Error limpiando imágenes: {e}")
    
    # Footer con información
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em; padding: 1rem;">
        <strong>Asistente de Tallas v2.0</strong>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()