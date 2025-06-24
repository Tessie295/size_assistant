import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from models.data_models import Client, Product, SizeRecommendation

# Cargar variables de entorno
load_dotenv()


class LLMService:
    """Servicio LLM simplificado con fallbacks."""
    
    def __init__(self):
        """Inicializa el servicio LLM."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = self._check_openai_availability()
        
        if self.use_openai:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                print("✅ OpenAI disponible")
            except ImportError:
                print("⚠️ OpenAI no instalado, usando respuestas locales")
                self.use_openai = False
            except Exception as e:
                print(f"⚠️ Error configurando OpenAI: {e}")
                self.use_openai = False
        else:
            print("⚠️ Usando respuestas locales (sin OpenAI)")
    
    def _check_openai_availability(self) -> bool:
        """Verifica si OpenAI está disponible."""
        if not self.api_key:
            return False
        if "tu_api_key_aqui" in self.api_key.lower():
            return False
        if len(self.api_key) < 20:
            return False
        return True
    
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
        """
        if self.use_openai:
            try:
                return self._generate_openai_response(
                    user_query, client, product, recommendation, conversation_history
                )
            except Exception as e:
                print(f"⚠️ Error con OpenAI, usando respuesta local: {e}")
                return self._generate_local_response(client, product, recommendation)
        else:
            return self._generate_local_response(client, product, recommendation)
    
    def _generate_openai_response(
        self,
        user_query: str,
        client: Client,
        product: Product,
        recommendation: SizeRecommendation,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Genera respuesta usando OpenAI."""
        # Construir contexto
        context = self._build_context(client, product, recommendation)
        
        # PROMPT
        messages = [
            {
                "role": "system", 
                "content": "Eres un asistente especializado en recomendaciones de tallas de ropa. "
                          "Sé amable, profesional y da explicaciones claras basadas en datos."
            }
        ]
        
        # Añadir historial si existe
        if conversation_history:
            messages.extend(conversation_history[-3:])  # Últimos 3 turnos
        
        # Añadir consulta actual
        messages.append({
            "role": "user",
            "content": f"""
            Pregunta: "{user_query}"
            
            Información disponible:
            {context}
            
            Por favor, genera una respuesta natural que incluya:
            1. La talla recomendada
            2. Una explicación del por qué
            3. Información adicional relevante
            """
        })
        
        # Llamar a OpenAI
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_local_response(
        self, 
        client: Client, 
        product: Product, 
        recommendation: SizeRecommendation
    ) -> str:
        """Genera respuesta local sin OpenAI."""
        
        # Análisis de la recomendación
        confidence_text = "alta" if recommendation.confidence > 0.8 else "media" if recommendation.confidence > 0.6 else "moderada"
        
        # Análisis de medidas
        client_measurements = client.body_measurements
        size_measurements = product.size_chart.get_size_measurements(recommendation.recommended_size)
        
        # Construir respuesta personalizada
        response_parts = []
        
        # Saludo personalizado
        response_parts.append(f"¡Hola {client.name}!")
        
        # Recomendación principal
        response_parts.append(
            f"Para el producto {product.name} ({product.product_id}), "
            f"te recomiendo la talla **{recommendation.recommended_size}** "
            f"con una confianza {confidence_text} ({recommendation.confidence:.1%})."
        )
        
        # Explicación basada en medidas
        bust_diff = abs(client_measurements.bust_cm - size_measurements.bust_cm)
        waist_diff = abs(client_measurements.waist_cm - size_measurements.waist_cm)
        
        if bust_diff <= 3 and waist_diff <= 3:
            response_parts.append("📏 Tus medidas se ajustan perfectamente a esta talla.")
        elif bust_diff <= 5 and waist_diff <= 5:
            response_parts.append("📏 Tus medidas son muy compatibles con esta talla.")
        else:
            response_parts.append("📏 Esta talla se adapta bien a tu tipo de cuerpo.")
        
        # Información sobre el ajuste del producto
        fit_info = {
            "Slim": "ajuste entallado que realza la silueta",
            "Regular": "ajuste clásico y cómodo",
            "Loose": "ajuste holgado y relajado",
            "Tailored": "ajuste estructurado y elegante",
            "Oversized": "ajuste amplio y moderno"
        }
        
        if product.fit in fit_info:
            response_parts.append(f"👔 Este producto tiene un {fit_info[product.fit]}.")
        
        # Información sobre el material
        fabric_info = {
            "Cotton": "El algodón es transpirable y cómodo para uso diario.",
            "Linen": "El lino es fresco y perfecto para climas cálidos.",
            "Wool": "La lana es ideal para mantener el calor y la elegancia.",
            "Polyester": "El poliéster es duradero y mantiene su forma.",
            "Blend": "Esta mezcla ofrece lo mejor de varios materiales."
        }
        
        if product.fabric in fabric_info:
            response_parts.append(f"🧵 {fabric_info[product.fabric]}")
        
        # Tallas alternativas
        if recommendation.alternative_sizes:
            alternatives_text = ", ".join(recommendation.alternative_sizes)
            response_parts.append(f"🔄 Como alternativas, también podrías considerar las tallas: {alternatives_text}.")
        
        # Consideraciones especiales
        if client.preferred_fit.lower() != product.fit.lower():
            if client.preferred_fit.lower() == "slim" and product.fit.lower() in ["regular", "loose"]:
                response_parts.append("💡 Dado que prefieres un ajuste más entallado, podrías considerar una talla más pequeña.")
            elif client.preferred_fit.lower() == "loose" and product.fit.lower() in ["slim", "tailored"]:
                response_parts.append("💡 Si buscas un ajuste más holgado, una talla más grande podría ser más cómoda.")
        
        # Mensaje de cierre
        response_parts.append("¿Te gustaría más detalles sobre algún aspecto específico de esta recomendación?")
        
        return " ".join(response_parts)
    
    def generate_product_search_response(self, user_query: str, found_products: List[Product]) -> str:
        """Genera respuesta para búsqueda de productos."""
        if not found_products:
            return "No encontré productos que coincidan con tu búsqueda. ¿Podrías ser más específico?"
        
        if len(found_products) == 1:
            product = found_products[0]
            return (f"Encontré el producto **{product.name}** ({product.product_id}). "
                   f"Es un {product.fit.lower()} de {product.fabric.lower()}. "
                   f"¿Te gustaría una recomendación de talla para este producto?")
        
        # Para múltiples productos, crear una lista organizada
        response_parts = []
        
        # Determinar el criterio de búsqueda
        query_lower = user_query.lower()
        if 'slim' in query_lower:
            response_parts.append("**🔍 Productos con ajuste Slim:**")
        elif 'regular' in query_lower:
            response_parts.append("**🔍 Productos con ajuste Regular:**")
        elif 'oversized' in query_lower:
            response_parts.append("**🔍 Productos con ajuste Oversized:**")
        elif 'loose' in query_lower:
            response_parts.append("**🔍 Productos con ajuste Loose:**")
        elif 'tailored' in query_lower:
            response_parts.append("**🔍 Productos con ajuste Tailored:**")
        elif any(material in query_lower for material in ['lana', 'wool']):
            response_parts.append("**🧵 Productos de Lana:**")
        elif any(material in query_lower for material in ['algodón', 'cotton']):
            response_parts.append("**🧵 Productos de Algodón:**")
        elif any(material in query_lower for material in ['lino', 'linen']):
            response_parts.append("**🧵 Productos de Lino:**")
        else:
            response_parts.append(f"**🔍 Productos encontrados ({len(found_products)}):**")
        
        response_parts.append("")  # Línea vacía
        
        # Agrupar productos por características si hay muchos
        if len(found_products) > 8:
            # Agrupar por ajuste
            fit_groups = {}
            for product in found_products:
                fit = product.fit
                if fit not in fit_groups:
                    fit_groups[fit] = []
                fit_groups[fit].append(product)
            
            for fit_type, products in fit_groups.items():
                response_parts.append(f"**{fit_type}:**")
                for product in products[:5]:  # Máximo 5 por grupo
                    response_parts.append(f"• **{product.name}** ({product.product_id}) - {product.fabric}")
                if len(products) > 5:
                    response_parts.append(f"... y {len(products) - 5} más")
                response_parts.append("")
        else:
            # Lista simple para pocos productos
            for product in found_products:
                fabric_info = f"Material: {product.fabric}"
                fit_info = f"Ajuste: {product.fit}"
                response_parts.append(f"• **{product.name}** ({product.product_id})")
                response_parts.append(f"  └ {fit_info}, {fabric_info}")
        
        response_parts.append("")
        response_parts.append("💡 **¿Qué te gustaría hacer?**")
        response_parts.append("• Especifica un cliente para obtener recomendación de talla")
        response_parts.append("• Pregunta por un producto específico")
        response_parts.append("• Solicita una visualización: *'Muestra [producto] en [color] para [cliente]'*")
        
        return "\n".join(response_parts)
    
    def generate_general_response(self, user_query: str, context: str = "") -> str:
        """Genera respuesta general."""
        if self.use_openai:
            try:
                messages = [
                    {
                        "role": "system", 
                        "content": "Eres un asistente de tallas de ropa. Sé útil y profesional."
                    },
                    {
                        "role": "user", 
                        "content": f"Pregunta: {user_query}\n{context if context else ''}"
                    }
                ]
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=200,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"⚠️ Error con OpenAI: {e}")
                pass
        
        # Respuesta local por defecto
        return (
            "¡Hola! Soy tu asistente de tallas. Para ayudarte mejor, puedo:\n\n"
            "📏 **Recomendar tallas** - Dime el cliente (ej: C0001) y producto (ej: P001)\n"
            "🔍 **Buscar productos** - Describe qué buscas\n"
            "🖼️ **Generar visualizaciones** - Añade 'muestra' o 'ver imagen'\n\n"
            "¿Cómo puedo ayudarte hoy?"
        )
    
    def _build_context(
        self, 
        client: Client, 
        product: Product, 
        recommendation: SizeRecommendation
    ) -> str:
        """Construye contexto para el LLM."""
        context_parts = [
            f"Cliente: {client.name} ({client.client_id})",
            f"Medidas: Busto {client.body_measurements.bust_cm}cm, "
            f"Cintura {client.body_measurements.waist_cm}cm, "
            f"Cadera {client.body_measurements.hips_cm}cm",
            f"Altura: {client.height_cm}cm",
            f"Preferencia: {client.preferred_fit}",
            f"Producto: {product.name} ({product.product_id})",
            f"Tipo: {product.fit}, Material: {product.fabric}",
            f"Talla recomendada: {recommendation.recommended_size}",
            f"Confianza: {recommendation.confidence:.1%}",
            f"Alternativas: {', '.join(recommendation.alternative_sizes) if recommendation.alternative_sizes else 'Ninguna'}"
        ]
        
        return "\n".join(context_parts)