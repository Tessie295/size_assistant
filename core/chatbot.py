import uuid
from typing import Dict, Any, List, Optional, Tuple
from data.data_loader import DataLoader
from engine.size_recommendation_engine import SizeRecommendationEngine
from services.llm_service import LLMService
from services.rag_service import RAGService
from services.conversation_manager import ConversationManager
from models.data_models import Client, Product, SizeRecommendation


class SizingChatbot:
    """Chatbot principal para recomendaciones de tallas."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Inicializa el chatbot con todos sus componentes.
        
        Args:
            data_dir: Directorio con los datos JSON
        """

        self.data_loader = DataLoader(data_dir)
        self.recommendation_engine = SizeRecommendationEngine()
        self.llm_service = LLMService()
        self.rag_service = RAGService(self.data_loader)
        self.conversation_manager = ConversationManager()
        
        self.is_initialized = self._check_initialization()
    
    def _check_initialization(self) -> bool:
        """Verificación de las inicializaciones"""
        try:
            if len(self.data_loader.clients) == 0 or len(self.data_loader.products) == 0:
                print("Los datos no estan cargados de forma correcta")
                return False
            
            print(f"Chatbot inicializado correctamente")
            print(f"   - {len(self.data_loader.clients)} clientes cargados")
            print(f"   - {len(self.data_loader.products)} productos cargados")
            return True
            
        except Exception as e:
            print(f"Error en la inicialización: {e}")
            return False
    
    def start_conversation(self, session_id: Optional[str] = None) -> str:
        """
        Inicia de conversación.
        
        Args:
            session_id: ID de sesión opcional (se genera automaticamente si no se pone uno
            manualmente)
            
        Returns:
            ID de la sesión creada
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.conversation_manager.start_session(session_id)
        
        # Mensaje Inicial
        welcome_message = """
        ¡Hola! 👋 Soy tu asistente personal de tallas. 
        
        Puedo ayudarte a encontrar la talla perfecta para cualquier prenda. 
        Solo necesito saber:
        - ¿Qué producto te interesa?
        - ¿Para qué cliente es la recomendación?
        
        Puedes preguntarme cosas como:
        • "¿Qué talla me recomiendas para el producto P001?"
        • "Busco un abrigo para el cliente C0001"
        • "¿Cuál es la mejor talla para User5 del producto P025?"
        """
        
        self.conversation_manager.add_turn(
            session_id=session_id,
            user_message="[INICIO_CONVERSACION]",
            assistant_response=welcome_message,
            metadata={"turn_type": "welcome"}
        )
        
        return session_id
    
    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Flujo de la conversación: mensaje - respuesta
        
        Args:
            message: Mensaje del usuario
            session_id: ID de la sesión
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        if not self.is_initialized:
            return {
                "response": "Lo siento, el sistema no está inicializado correctamente. "
                           "Por favor, verifica la configuración.",
                "error": True
            }
        
        try:
            # 1. Parsear la consulta con RAG
            parsed_query = self.rag_service.parse_query(message)
            
            # 2. Recuperar contexto relevante
            context = self.rag_service.retrieve_context(parsed_query)
            
            # 3. Procesar según la intención
            response_data = self._process_by_intent(
                message, session_id, parsed_query, context
            )
            
            # 4. Añadir turno a la conversación
            self.conversation_manager.add_turn(
                session_id=session_id,
                user_message=message,
                assistant_response=response_data["response"],
                context=context,
                metadata=response_data.get("metadata", {})
            )
            
            return response_data
            
        except Exception as e:
            error_response = f"Lo siento, ocurrió un error al procesar tu mensaje: {str(e)}"
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
        """Procesa el mensaje según la intención detectada e nel usuario."""
        
        intent = context.get('intent', 'general')
        
        if intent == 'size_recommendation':
            return self._handle_size_recommendation(message, session_id, context)
        elif intent == 'product_search':
            return self._handle_product_search(message, session_id, context)
        elif intent == 'help':
            return self._handle_help_request(message, session_id)
        else:
            return self._handle_general_query(message, session_id, context)
    
    def _handle_size_recommendation(
        self, 
        message: str, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gestión para la ecomendación de tallas."""
        
        clients = context.get('clients', [])
        products = context.get('products', [])
        
        # Usar contexto de sesión si no hay información explícita
        session = self.conversation_manager.get_session(session_id)
        
        if not clients and session and session.active_client:
            clients = [session.active_client]
        
        if not products and session and session.active_product:
            products = [session.active_product]
        
        # Verificar que se tiene la información necesaria
        if not clients:
            return {
                "response": "Para darte una recomendación de talla, necesito saber para qué cliente es. "
                           "¿Podrías especificar el ID del cliente (ej: C0001) o buscar uno?",
                "needs_client": True
            }
        
        if not products:
            return {
                "response": "Para recomendarte una talla, necesito saber qué producto te interesa. "
                           "¿Podrías especificar el ID del producto (ej: P001) o buscar uno?",
                "needs_product": True
            }
        
        # Tomar el primer cliente y producto encontrados
        client = clients[0]
        product = products[0]
        
        # Actualizar contexto de sesión
        self.conversation_manager.set_active_client(session_id, client)
        self.conversation_manager.set_active_product(session_id, product)
        
        # Generar recomendación técnica
        recommendation = self.recommendation_engine.recommend_size(client, product)
        
        # Obtener historial de conversación para el LLM
        conversation_history = self.conversation_manager.get_conversation_history(
            session_id, format_for_llm=True
        )
        
        # Generar respuesta con LLM
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
                "response": "No encontré productos que coincidan con tu búsqueda. "
                           "¿Podrías ser más específico? Puedes buscar por nombre, ID (ej: P001), "
                           "material (algodón, lana) o tipo de ajuste (slim, regular).",
                "products_found": 0
            }
        
        # Generar respuesta con LLM
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
    
    def _handle_help_request(self, message: str, session_id: str) -> Dict[str, Any]:
        """Maneja solicitudes de ayuda."""
        
        help_response = """
        ¡Estoy aquí para ayudarte! 🤗
        
        **¿Qué puedo hacer por ti?**
        
        📏 **Recomendaciones de talla:**
        - "¿Qué talla me recomiendas para el producto P001?"
        - "Talla para User5 del abrigo P025"
        
        🔍 **Buscar productos:**
        - "Busca abrigos de lana"
        - "Productos con ajuste slim"
        - "Mostrame productos disponibles"
        
        👤 **Información de clientes:**
        - Los clientes están identificados como C0001, C0002, etc.
        - También puedes usar User1, User2, etc.
        
        🛍️ **Información de productos:**
        - Los productos están identificados como P001, P002, etc.
        - Puedes buscar por material, tipo de ajuste, etc.
        
        **Ejemplos de preguntas:**
        - "¿Qué talla debería elegir el cliente C0001 para el producto P005?"
        - "Busca productos de algodón para una persona con preferencia slim"
        - "Recomienda talla para User10 en cualquier abrigo disponible"
        """
        
        return {
            "response": help_response,
            "metadata": {
                "intent": "help",
                "success": True
            }
        }
    
    def _handle_general_query(
        self, 
        message: str, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Maneja consultas generales."""
        
        # Usar LLM para respuesta general con contexto
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
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Obtiene información de la sesión actual."""
        return self.conversation_manager.get_session_summary(session_id)
    
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