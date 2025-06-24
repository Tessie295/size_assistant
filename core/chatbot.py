import uuid
from typing import Dict, Any, Optional, List
from data.data_loader import DataLoader
from engine.size_recommendation_engine import SizeRecommendationEngine
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.conversation_manager import ConversationManager
from models.data_models import Client, Product, SizeRecommendation


from services.visual_service import VisualService
VISUAL_AVAILABLE = True

class SizingChatbot:
    """Chatbot para recomendaciones de tallas."""
    
    def __init__(self, data_dir: str = "data"):
        """Inicializa el chatbot con todos sus componentes."""
        # Inicializar componentes básicos
        self.data_loader = DataLoader(data_dir)
        self.recommendation_engine = SizeRecommendationEngine()
        self.llm_service = LLMService()
        self.rag_service = RAGService(self.data_loader)
        self.conversation_manager = ConversationManager()
        
        # Inicializar servicio visual si está disponible
        self.visual_service = None
        if VISUAL_AVAILABLE:
            try:
                self.visual_service = VisualService()
                if not self.visual_service.is_available():
                    print("⚠️ Servicio visual: PIL no disponible")
                else:
                    print("✅ Servicio visual: Disponible")
            except Exception as e:
                print(f"⚠️ Error inicializando servicio visual: {e}")
        
        # Estado del chatbot
        self.is_initialized = self._check_initialization()
    
    def _check_initialization(self) -> bool:
        """Verifica que todos los componentes estén correctamente inicializados."""
        try:
            if not self.data_loader.is_loaded():
                print("❌ Datos no cargados correctamente")
                return False
            
            print(f"✅ Chatbot inicializado correctamente")
            print(f"   - {len(self.data_loader.clients)} clientes")
            print(f"   - {len(self.data_loader.products)} productos") 
            print(f"   - LLM: {'OpenAI' if self.llm_service.use_openai else 'Local'}")
            print(f"   - Visual: {'✅' if self.visual_service and self.visual_service.is_available() else '❌'}")
            return True
            
        except Exception as e:
            print(f"❌ Error en la inicialización: {e}")
            return False
    
    def start_conversation(self, session_id: Optional[str] = None) -> str:
        """Inicia una nueva conversación."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.conversation_manager.start_session(session_id)
        
        # Mensaje de bienvenida
        welcome_message = (
            "¡Hola! 👋 Soy tu asistente personal de tallas.\n\n"
            "Puedo ayudarte a encontrar la talla perfecta para cualquier prenda."
        )
        
        if self.visual_service and self.visual_service.is_available():
            welcome_message += " También puedo generar visualizaciones de cómo te queda la ropa."
        
        welcome_message += (
            "\n\n**Ejemplos de consultas:**\n"
            "• \"¿Qué talla del producto P001 para el cliente C0001?\"\n"
            "• \"Busca productos de lana\""
        )
        
        if self.visual_service and self.visual_service.is_available():
            welcome_message += "\n• \"Muestra P005 en azul para C0002\""
        
        self.conversation_manager.add_turn(
            session_id=session_id,
            user_message="[INICIO_CONVERSACION]",
            assistant_response=welcome_message,
            metadata={"turn_type": "welcome"}
        )
        
        return session_id
    
    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Procesa un mensaje del usuario y genera una respuesta."""
        if not self.is_initialized:
            return {
                "response": "Lo siento, el sistema no está inicializado correctamente. "
                           "Por favor, verifica que los archivos de datos estén en la carpeta 'data/'.",
                "error": True
            }
        
        try:
            print(f"\n🔍 Procesando: '{message}'")
            
            # 1. Parsear la consulta con RAG
            parsed_query = self.rag_service.parse_query(message)
            print(f"📋 Productos: {parsed_query['product_ids']}, Clientes: {parsed_query['client_ids']}")
            
            # 2. Recuperar contexto relevante
            context = self.rag_service.retrieve_context(parsed_query)
            print(f"📊 Contexto: {len(context['clients'])} clientes, {len(context['products'])} productos")
            
            # 3. Procesar según la intención
            response_data = self._process_by_intent(message, session_id, parsed_query, context)
            
            # 4. Añadir contenido visual si se solicita y es posible
            if (parsed_query.get('has_visual_intent', False) and 
                self.visual_service and 
                self.visual_service.is_available() and
                response_data.get('recommendation') and
                response_data.get('client') and
                response_data.get('product')):
                
                print("🖼️ Generando contenido visual...")
                visual_result = self._generate_visual_content(message, response_data)
                if visual_result and visual_result.get('success'):
                    response_data['visual'] = visual_result
                    response_data['response'] += "\n\n🖼️ He generado una visualización de cómo te queda la prenda."
                elif visual_result:
                    print(f"⚠️ Error visual: {visual_result.get('error')}")
            
            # 5. Añadir turno a la conversación
            self.conversation_manager.add_turn(
                session_id=session_id,
                user_message=message,
                assistant_response=response_data["response"],
                context=context,
                metadata=response_data.get("metadata", {})
            )
            
            print("✅ Mensaje procesado exitosamente")
            return response_data
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            import traceback
            traceback.print_exc()
            
            # Respuesta de fallback
            error_response = (
                "Lo siento, ocurrió un error al procesar tu mensaje. "
                "¿Podrías intentar reformular tu consulta? Por ejemplo: "
                "'¿Qué talla del producto P001 para el cliente C0001?'"
            )
            
            return {
                "response": error_response,
                "error": True,
                "error_details": str(e)
            }
    
    def _process_by_intent(
        self, 
        message: str, 
        session_id: str, 
        parsed_query: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Procesa el mensaje según la intención identificada."""
        
        intent = context.get('intent', 'general')
        print(f"🎯 Intención: {intent}")
        
        if intent == 'size_recommendation':
            return self._handle_size_recommendation(message, session_id, context)
        elif intent == 'product_search':
            return self._handle_product_search(message, session_id, context)
        elif intent == 'help':
            return self._handle_help_request()
        else:
            return self._handle_general_query(message, context)
    
    def _handle_size_recommendation(
        self, 
        message: str, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Maneja solicitudes de recomendación de talla."""
        
        clients = context.get('clients', [])
        products = context.get('products', [])
        
        # Intentar usar contexto de sesión si no hay información explícita
        session = self.conversation_manager.get_session(session_id)
        
        if not clients and session and session.active_client:
            clients = [session.active_client]
        
        if not products and session and session.active_product:
            products = [session.active_product]
        
        # Verificar información necesaria
        if not clients:
            return {
                "response": (
                    "Para darte una recomendación de talla, necesito saber para qué cliente es. "
                    "Por favor, especifica el ID del cliente (ejemplo: C0001, C0002, etc.) "
                    "o usa User seguido del número (ejemplo: User1, User2)."
                ),
                "needs_client": True,
                "metadata": {"intent": "size_recommendation", "missing": "client"}
            }
        
        if not products:
            return {
                "response": (
                    "Para recomendarte una talla, necesito saber qué producto te interesa. "
                    "Por favor, especifica el ID del producto (ejemplo: P001, P002, etc.)."
                ),
                "needs_product": True,
                "metadata": {"intent": "size_recommendation", "missing": "product"}
            }
        
        # Procesar recomendación
        client = clients[0]
        product = products[0]
        
        print(f"✅ Procesando: {client.name} + {product.name}")
        
        # Actualizar contexto de sesión
        self.conversation_manager.set_active_client(session_id, client)
        self.conversation_manager.set_active_product(session_id, product)
        
        try:
            # Generar recomendación técnica
            recommendation = self.recommendation_engine.recommend_size(client, product)
            print(f"📏 Recomendación: {recommendation.recommended_size} (conf: {recommendation.confidence:.1%})")
            
            # Generar respuesta con LLM
            conversation_history = self.conversation_manager.get_conversation_history(
                session_id, format_for_llm=True
            )
            
            response = self.llm_service.generate_recommendation_response(
                user_query=message,
                client=client,
                product=product,
                recommendation=recommendation,
                conversation_history=conversation_history
            )
            
            return {
                "response": response,
                "recommendation": {
                    "size": recommendation.recommended_size,
                    "confidence": recommendation.confidence,
                    "alternatives": recommendation.alternative_sizes
                },
                "client": {
                    "id": client.client_id,
                    "name": client.name
                },
                "product": {
                    "id": product.product_id,
                    "name": product.name
                },
                "metadata": {
                    "intent": "size_recommendation",
                    "success": True
                }
            }
            
        except Exception as e:
            print(f"❌ Error en recomendación: {e}")
            return {
                "response": (
                    f"Encontré al cliente {client.name} y el producto {product.name}, "
                    f"pero hubo un error generando la recomendación. "
                    f"Por favor, inténtalo de nuevo."
                ),
                "error": True,
                "error_details": str(e)
            }
    
    def _handle_product_search(
        self, 
        message: str, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Maneja búsquedas de productos."""
        
        products = context.get('products', [])
        
        if not products:
            # Intentar búsqueda más amplia
            search_terms = " ".join(context.get('keywords', []))
            if search_terms:
                products = self.data_loader.search_products(search_terms, limit=5)
        
        if not products:
            return {
                "response": (
                    "No encontré productos que coincidan con tu búsqueda. "
                    "Puedes buscar por ID (ejemplo: P001), material (algodón, lana) "
                    "o tipo de ajuste (slim, regular). "
                    "¿Podrías ser más específico?"
                ),
                "products_found": 0,
                "metadata": {"intent": "product_search", "success": False}
            }
        
        # Generar respuesta
        response = self.llm_service.generate_product_search_response(message, products)
        
        return {
            "response": response,
            "products": [
                {
                    "id": p.product_id,
                    "name": p.name,
                    "fit": p.fit,
                    "fabric": p.fabric
                }
                for p in products[:5]
            ],
            "products_found": len(products),
            "metadata": {
                "intent": "product_search",
                "success": True
            }
        }
    
    def _handle_help_request(self) -> Dict[str, Any]:
        """Maneja solicitudes de ayuda."""
        
        help_response = (
            "¡Estoy aquí para ayudarte! 🤗\n\n"
            "**¿Qué puedo hacer por ti?**\n\n"
            "📏 **Recomendaciones de talla:**\n"
            "• \"¿Qué talla del producto P001 para el cliente C0001?\"\n"
            "• \"Talla para User5 del producto P025\"\n\n"
            "🔍 **Buscar productos:**\n"
            "• \"Busca productos de lana\"\n"
            "• \"Productos con ajuste slim\"\n\n"
        )
        
        if self.visual_service and self.visual_service.is_available():
            help_response += (
                "🖼️ **Visualizaciones:**\n"
                "• \"Muestra P001 en azul para C0001\"\n"
                "• \"Ver imagen de User2 con P025\"\n\n"
                "🎨 **Colores disponibles:**\n"
                "azul, rojo, verde, negro, blanco, gris, rosa, amarillo, morado, naranja\n\n"
            )
        
        help_response += (
            "**Formato de IDs:**\n"
            "• Clientes: C0001, C0002, etc. (o User1, User2, etc.)\n"
            "• Productos: P001, P002, etc."
        )
        
        return {
            "response": help_response,
            "metadata": {
                "intent": "help",
                "success": True
            }
        }
    
    def _handle_general_query(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja consultas generales."""
        
        # Construir contexto para el LLM
        context_str = ""
        if context.get('clients'):
            context_str += f"Clientes mencionados: {[c.name for c in context['clients']]}\n"
        if context.get('products'):
            context_str += f"Productos mencionados: {[p.name for p in context['products']]}\n"
        
        response = self.llm_service.generate_general_response(message, context_str)
        
        return {
            "response": response,
            "metadata": {
                "intent": "general",
                "success": True
            }
        }
    
    def _generate_visual_content(self, message: str, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Genera contenido visual si se solicita."""
        try:
            # Obtener objetos completos
            client = self.data_loader.get_client(response_data['client']['id'])
            product = self.data_loader.get_product(response_data['product']['id'])
            
            if not client or not product:
                return None
            
            # Extraer color del mensaje
            color = self._extract_color_from_message(message)
            
            # Generar imagen
            visual_result = self.visual_service.generate_avatar_image(
                client=client,
                product=product,
                size=response_data['recommendation']['size'],
                color=color
            )
            
            return visual_result if visual_result.get('success') else visual_result
            
        except Exception as e:
            print(f"❌ Error generando contenido visual: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_color_from_message(self, message: str) -> str:
        """Extrae el color mencionado en el mensaje."""
        colors = ['azul', 'rojo', 'verde', 'negro', 'blanco', 'gris', 'rosa', 'amarillo', 'morado', 'naranja']
        
        message_lower = message.lower()
        for color in colors:
            if color in message_lower:
                return color
        
        return 'azul'  # Color por defecto
    
    # Métodos de utilidad
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Obtiene información de la sesión actual."""
        base_info = self.conversation_manager.get_session_summary(session_id)
        base_info['visual_enabled'] = self.visual_service and self.visual_service.is_available()
        base_info['llm_type'] = 'openai' if self.llm_service.use_openai else 'local'
        return base_info
    
    def clear_session(self, session_id: str) -> None:
        """Limpia una sesión específica."""
        self.conversation_manager.clear_session(session_id)
    
    def get_available_clients(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene lista de clientes disponibles."""
        clients = self.data_loader.get_all_clients()[:limit]
        return [
            {
                "id": c.client_id,
                "name": c.name,
                "preferred_fit": c.preferred_fit,
                "height_cm": c.height_cm
            }
            for c in clients
        ]
    
    def get_available_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene lista de productos disponibles."""
        products = self.data_loader.get_all_products()[:limit]
        return [
            {
                "id": p.product_id,
                "name": p.name,
                "fit": p.fit,
                "fabric": p.fabric,
                "available_sizes": p.available_sizes
            }
            for p in products
        ]
    
    def test_basic_functionality(self) -> bool:
        """Prueba la funcionalidad básica del chatbot."""
        try:
            session_id = self.start_conversation()
            response = self.process_message("¿Qué talla del producto P001 para el cliente C0001?", session_id)
            return not response.get('error', False)
        except Exception as e:
            print(f"❌ Error en prueba básica: {e}")
            return False