from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from models.data_models import Client, Product


@dataclass
class ConversationTurn:
    """Turnos de conversación."""
    timestamp: datetime
    user_message: str
    assistant_response: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Sesión de conversación."""
    session_id: str
    created_at: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    active_client: Optional[Client] = None
    active_product: Optional[Product] = None
    session_context: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """Gestor de conversaciones con memoria y contexto."""
    
    def __init__(self, max_turns_memory: int = 10):
        """
        Inicializa el gestor de conversaciones.
        
        Args:
            max_turns_memory: Número máximo de turnos a mantener en memoria
        """
        self.max_turns_memory = max_turns_memory
        self.sessions: Dict[str, ConversationSession] = {}
        self.current_session_id: Optional[str] = None
    
    def start_session(self, session_id: str) -> ConversationSession:
        """
        Inicia una nueva sesión de conversación.
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Nueva sesión de conversación
        """
        session = ConversationSession(
            session_id=session_id,
            created_at=datetime.now()
        )
        
        self.sessions[session_id] = session
        self.current_session_id = session_id
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Obtiene una sesión existente."""
        return self.sessions.get(session_id)
    
    def get_current_session(self) -> Optional[ConversationSession]:
        """Obtiene la sesión actual."""
        if self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None
    
    def add_turn(
        self, 
        session_id: str,
        user_message: str,
        assistant_response: str,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Añade un turno de conversación a la sesión.
        
        Args:
            session_id: ID de la sesión
            user_message: Mensaje del usuario
            assistant_response: Respuesta del asistente
            context: Contexto del turno
            metadata: Metadatos adicionales
        """
        session = self.get_session(session_id)
        if not session:
            session = self.start_session(session_id)
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message=user_message,
            assistant_response=assistant_response,
            context=context or {},
            metadata=metadata or {}
        )
        
        session.turns.append(turn)
        
        # Mantener solo los últimos N turnos
        if len(session.turns) > self.max_turns_memory:
            session.turns = session.turns[-self.max_turns_memory:]
        
        # Actualizar contexto de sesión
        self._update_session_context(session, context or {})
    
    def get_conversation_history(
        self, 
        session_id: str, 
        format_for_llm: bool = False
    ) -> List[Dict[str, str]]:
        """
        Obtiene el historial de conversación.
        
        Args:
            session_id: ID de la sesión
            format_for_llm: Si formatear para el LLM
            
        Returns:
            Historial de conversación
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        if format_for_llm:
            # Formato para OpenAI ChatCompletion
            history = []
            for turn in session.turns[-5:]:  # Últimos 5 turnos
                history.append({"role": "user", "content": turn.user_message})
                history.append({"role": "assistant", "content": turn.assistant_response})
            return history
        else:
            # Formato simple
            return [
                {
                    "timestamp": turn.timestamp.isoformat(),
                    "user": turn.user_message,
                    "assistant": turn.assistant_response
                }
                for turn in session.turns
            ]
    
    def set_active_client(self, session_id: str, client: Client) -> None:
        """Establece el cliente activo para la sesión."""
        session = self.get_session(session_id)
        if session:
            session.active_client = client
            session.session_context['active_client_id'] = client.client_id
    
    def set_active_product(self, session_id: str, product: Product) -> None:
        """Establece el producto activo para la sesión."""
        session = self.get_session(session_id)
        if session:
            session.active_product = product
            session.session_context['active_product_id'] = product.product_id
    
    def get_active_client(self, session_id: str) -> Optional[Client]:
        """Obtiene el cliente activo de la sesión."""
        session = self.get_session(session_id)
        return session.active_client if session else None
    
    def get_active_product(self, session_id: str) -> Optional[Product]:
        """Obtiene el producto activo de la sesión."""
        session = self.get_session(session_id)
        return session.active_product if session else None
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Genera un resumen de la sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Resumen de la sesión
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        # Analizar los turnos para extraer información relevante
        topics_discussed = set()
        products_mentioned = set()
        clients_mentioned = set()
        
        for turn in session.turns:
            context = turn.context
            if 'products' in context:
                for product in context['products']:
                    products_mentioned.add(product.product_id)
            
            if 'clients' in context:
                for client in context['clients']:
                    clients_mentioned.add(client.client_id)
            
            # Identificar temas por palabras clave
            message_lower = turn.user_message.lower()
            if any(word in message_lower for word in ['talla', 'size', 'ajuste']):
                topics_discussed.add('size_recommendation')
            if any(word in message_lower for word in ['buscar', 'producto', 'mostrar']):
                topics_discussed.add('product_search')
        
        return {
            'session_id': session_id,
            'created_at': session.created_at.isoformat(),
            'total_turns': len(session.turns),
            'topics_discussed': list(topics_discussed),
            'products_mentioned': list(products_mentioned),
            'clients_mentioned': list(clients_mentioned),
            'active_client': session.active_client.client_id if session.active_client else None,
            'active_product': session.active_product.product_id if session.active_product else None,
            'last_activity': session.turns[-1].timestamp.isoformat() if session.turns else None
        }
    
    def clear_session(self, session_id: str) -> None:
        """Limpia una sesión específica."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if self.current_session_id == session_id:
            self.current_session_id = None
    
    def clear_all_sessions(self) -> None:
        """Limpia todas las sesiones."""
        self.sessions.clear()
        self.current_session_id = None
    
    def _update_session_context(self, session: ConversationSession, turn_context: Dict[str, Any]) -> None:
        """Actualiza el contexto global de la sesión basado en el turno actual."""
        # Actualizar contadores de menciones
        if 'mention_counts' not in session.session_context:
            session.session_context['mention_counts'] = {
                'products': {},
                'clients': {},
                'intents': {}
            }
        
        # Contar menciones de productos
        if 'products' in turn_context:
            for product in turn_context['products']:
                product_id = product.product_id
                session.session_context['mention_counts']['products'][product_id] = \
                    session.session_context['mention_counts']['products'].get(product_id, 0) + 1
        
        # Contar menciones de clientes
        if 'clients' in turn_context:
            for client in turn_context['clients']:
                client_id = client.client_id
                session.session_context['mention_counts']['clients'][client_id] = \
                    session.session_context['mention_counts']['clients'].get(client_id, 0) + 1
        
        # Contar intenciones
        if 'intent' in turn_context:
            intent = turn_context['intent']
            session.session_context['mention_counts']['intents'][intent] = \
                session.session_context['mention_counts']['intents'].get(intent, 0) + 1
        
        # Actualizar último contexto relevante
        session.session_context['last_context'] = turn_context
    
    def get_context_suggestions(self, session_id: str) -> Dict[str, Any]:
        """
        Genera sugerencias basadas en el contexto de la sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Sugerencias contextuales
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        suggestions = {
            'next_questions': [],
            'related_products': [],
            'related_clients': []
        }
        
        # Analizar patrones de conversación
        mention_counts = session.session_context.get('mention_counts', {})
        
        # Sugerir preguntas basadas en el contexto
        if session.active_client and not session.active_product:
            suggestions['next_questions'].append(
                "¿Qué producto te interesa para recomendarte una talla?"
            )
        elif session.active_product and not session.active_client:
            suggestions['next_questions'].append(
                "¿Para qué cliente necesitas la recomendación de talla?"
            )
        elif session.active_client and session.active_product:
            suggestions['next_questions'].extend([
                "¿Te gustaría ver tallas alternativas?",
                "¿Necesitas información sobre el ajuste?",
                "¿Quieres comparar con otros productos similares?"
            ])
        
        # Productos más mencionados
        if 'products' in mention_counts:
            most_mentioned_products = sorted(
                mention_counts['products'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            suggestions['related_products'] = [pid for pid, _ in most_mentioned_products]
        
        # Clientes más mencionados
        if 'clients' in mention_counts:
            most_mentioned_clients = sorted(
                mention_counts['clients'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            suggestions['related_clients'] = [cid for cid, _ in most_mentioned_clients]
        
        return suggestions