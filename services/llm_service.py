import openai
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from models.data_models import Client, Product, SizeRecommendation

# Cargar variables de entorno
load_dotenv()


class LLMService:
    """Servicio para generar respuestas usando modelos de lenguaje."""
    
    def __init__(self, model=os.getenv("OPENAI_MODEL")):
        """
        Inicializa el servicio LLM.
        
        Args:
            model: Modelo de OpenAI a utilizar
        """
        self.model = model
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prompts
        self.system_prompt = """
        Eres un asistente especializado en recomendaciones de tallas de ropa. 
        Tu trabajo es ayudar a los clientes a encontrar la talla perfecta basándote en:
        
        1. Sus medidas corporales
        2. Su historial de compras previo
        3. Sus preferencias de ajuste
        4. Las características específicas del producto
        
        Debes ser amable, profesional y dar explicaciones claras y útiles.
        Siempre justifica tus recomendaciones con datos concretos.
        """
    
    def generate_recommendation_response(
        self, 
        user_query: str,
        client: Client,
        product: Product,
        recommendation: SizeRecommendation,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Genera una respuesta conversacional basada en la recomendación técnica.
        
        Args:
            user_query: Pregunta del usuario
            client: Información del cliente
            product: Información del producto
            recommendation: Recomendación técnica generada
            conversation_history: Historial de conversación previo
            
        Returns:
            Respuesta generada por el LLM
        """
        # Construir contexto
        context = self._build_context(client, product, recommendation)
        
        # Construir historial de mensajes
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Añadir historial de conversación si existe
        if conversation_history:
            messages.extend(conversation_history)
        
        # Añadir contexto actual
        messages.append({
            "role": "user", 
            "content": f"""
            Pregunta del cliente: "{user_query}"
            
            Contexto:
            {context}
            
            Por favor, genera una respuesta natural y útil que incluya:
            1. La talla recomendada
            2. Una explicación clara del por qué
            3. Información adicional relevante sobre el ajuste
            4. Alternativas si corresponde
            """
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Lo siento, ha ocurrido un error al procesar tu consulta: {str(e)}"
    
    def generate_product_search_response(
        self, 
        user_query: str, 
        found_products: List[Product]
    ) -> str:
        """
        Genera una respuesta cuando el usuario busca productos.
        
        Args:
            user_query: Consulta del usuario
            found_products: Lista de productos encontrados
            
        Returns:
            Respuesta formateada con los productos
        """
        if not found_products:
            return "No encontré productos que coincidan con tu búsqueda. ¿Podrías ser más específico?"
        
        products_info = []
        for product in found_products[:3]:  # Limitar a 3 productos
            products_info.append(
                f"- **{product.name}** ({product.product_id}): "
                f"Ajuste {product.fit}, material {product.fabric}"
            )
        
        products_text = "\n".join(products_info)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
            El usuario preguntó: "{user_query}"
            
            Productos encontrados:
            {products_text}
            
            Genera una respuesta amable mostrando los productos y preguntando 
            cuál le interesa para poder dar una recomendación de talla.
            """}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Encontré algunos productos pero no pude formatear la respuesta adecuadamente: {products_text}"
    
    def generate_general_response(self, user_query: str, context: str = "") -> str:
        """
        Genera una respuesta general cuando no hay contexto específico.
        
        Args:
            user_query: Pregunta del usuario
            context: Contexto adicional opcional
            
        Returns:
            Respuesta del LLM
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""
            Pregunta: "{user_query}"
            {f"Contexto: {context}" if context else ""}
            
            El usuario parece tener una consulta general sobre tallas o productos.
            Responde de manera útil y guía al usuario sobre cómo puede obtener 
            una recomendación más específica.
            """}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "¡Hola! Soy tu asistente de tallas. Para darte la mejor recomendación, necesito saber qué producto te interesa y quién eres. ¿Podrías contarme más detalles?"
    
    def _build_context(
        self, 
        client: Client, 
        product: Product, 
        recommendation: SizeRecommendation
    ) -> str:
        """
        Construye el contexto para el LLM con información relevante.
        
        Args:
            client: Información del cliente
            product: Información del producto
            recommendation: Recomendación técnica
            
        Returns:
            Contexto formateado como string
        """
        context_parts = []
        
        # Información del cliente
        context_parts.append(f"Cliente: {client.name}")
        context_parts.append(f"Medidas: Busto {client.body_measurements.bust_cm}cm, "
                           f"Cintura {client.body_measurements.waist_cm}cm, "
                           f"Cadera {client.body_measurements.hips_cm}cm")
        context_parts.append(f"Altura: {client.height_cm}cm")
        context_parts.append(f"Preferencia de ajuste: {client.preferred_fit}")
        
        # Información del producto
        context_parts.append(f"Producto: {product.name} ({product.product_id})")
        context_parts.append(f"Tipo de ajuste: {product.fit}")
        context_parts.append(f"Material: {product.fabric}")
        context_parts.append(f"Tallas disponibles: {', '.join(product.available_sizes)}")
        
        # Recomendación
        context_parts.append(f"Talla recomendada: {recommendation.recommended_size}")
        context_parts.append(f"Confianza: {recommendation.confidence:.2f}")
        context_parts.append(f"Razonamiento técnico: {recommendation.reasoning}")
        context_parts.append(f"Notas del ajuste: {recommendation.fit_notes}")
        
        if recommendation.alternative_sizes:
            context_parts.append(f"Tallas alternativas: {', '.join(recommendation.alternative_sizes)}")
        
        # Historial relevante
        if client.purchase_history:
            recent_purchases = client.purchase_history[-3:]  # Últimas 3 compras
            history_summary = []
            for purchase in recent_purchases:
                history_summary.append(f"Producto {purchase.product_id}, "
                                     f"talla {purchase.size_purchased}: {purchase.fit_feedback}")
            context_parts.append(f"Historial reciente: {'; '.join(history_summary)}")
        
        return "\n".join(context_parts)