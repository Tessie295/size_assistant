import re
from typing import List, Dict, Tuple, Optional
from models.data_models import Client, Product
from data.data_loader import DataLoader


class RAGService:
    """Recuperación de información con ayuda del contexto - RAG."""
    
    def __init__(self, data_loader: DataLoader):
        """
        Inicializa el servicio RAG.
        
        Args:
            data_loader: Instancia del cargador de datos
        """
        self.data_loader = data_loader
        
        # Patrones para identificar entidades en las consultas
        self.product_patterns = [
            r'producto\s+([A-Z]\d+)',
            r'P(\d+)',
            r'abrigo',
            r'prenda',
            r'producto',
            r'camisa',
            r'pantalón',
            r'vestido'
        ]
        
        self.client_patterns = [
            r'cliente\s+([A-Z]\d+)',
            r'C(\d+)',
            r'user(\d+)',
            r'usuario\s+(\d+)',
            r'mi\s+perfil',
            r'para\s+mí'
        ]
        
        # Palabras clave para diferentes tipos de consultas
        self.size_keywords = [
            'talla', 'size', 'ajuste', 'fit', 'medida', 'dimensión',
            'qué talla', 'cuál talla', 'recomienda', 'recomendación'
        ]
        
        self.search_keywords = [
            'buscar', 'encontrar', 'ver', 'mostrar', 'listar',
            'qué productos', 'cuáles productos', 'productos disponibles'
        ]
    
    def parse_query(self, query: str) -> Dict[str, any]:
        """
        Parsea la consulta del usuario para extraer intención y entidades.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con información parseada
        """
        query_lower = query.lower()
        
        result = {
            'intent': self._identify_intent(query_lower),
            'product_ids': self._extract_product_ids(query),
            'client_ids': self._extract_client_ids(query),
            'keywords': self._extract_keywords(query_lower),
            'original_query': query
        }
        
        return result
    
    def retrieve_context(self, parsed_query: Dict[str, any]) -> Dict[str, any]:
        """
        Recupera el contexto relevante basado en la consulta parseada.
        
        Args:
            parsed_query: Consulta parseada
            
        Returns:
            Contexto relevante para la consulta
        """
        context = {
            'clients': [],
            'products': [],
            'intent': parsed_query['intent'],
            'confidence': 0.0
        }
        
        # Recuperar clientes
        if parsed_query['client_ids']:
            for client_id in parsed_query['client_ids']:
                client = self.data_loader.get_client(client_id)
                if client:
                    context['clients'].append(client)
                    context['confidence'] += 0.3
        
        # Recuperar productos
        if parsed_query['product_ids']:
            for product_id in parsed_query['product_ids']:
                product = self.data_loader.get_product(product_id)
                if product:
                    context['products'].append(product)
                    context['confidence'] += 0.3
        
        # Si no hay IDs específicos, buscar por palabras clave
        if not context['products'] and parsed_query['keywords']:
            search_terms = ' '.join(parsed_query['keywords'])
            found_products = self.data_loader.search_products(search_terms, limit=5)
            context['products'].extend(found_products)
            context['confidence'] += 0.2 if found_products else 0.0
        
        # Ajustar confianza
        context['confidence'] = min(1.0, context['confidence'])
        
        return context
    
    def find_similar_clients(self, target_client: Client, limit: int = 3) -> List[Tuple[Client, float]]:
        """
        Encuentra clientes similares basado en medidas y preferencias.
        
        Args:
            target_client: Cliente objetivo
            limit: Número máximo de clientes similares
            
        Returns:
            Lista de tuplas (cliente, similitud)
        """
        similarities = []
        target_measurements = target_client.body_measurements
        
        for client in self.data_loader.get_all_clients():
            if client.client_id == target_client.client_id:
                continue
            
            similarity = self._calculate_client_similarity(target_client, client)
            similarities.append((client, similarity))
        
        # Ordenar por similitud descendente
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def get_relevant_purchase_history(
        self, 
        client: Client, 
        product: Product
    ) -> List[Dict[str, any]]:
        """
        Obtiene historial de compras relevante para un producto específico.
        
        Args:
            client: Cliente
            product: Producto
            
        Returns:
            Lista de compras relevantes con análisis
        """
        relevant_purchases = []
        
        for purchase in client.purchase_history:
            # Buscar el producto de la compra
            purchase_product = self.data_loader.get_product(purchase.product_id)
            
            if not purchase_product:
                continue
            
            # Calcular relevancia basada en similitud del producto
            relevance = self._calculate_product_similarity(product, purchase_product)
            
            relevant_purchases.append({
                'purchase': purchase,
                'product': purchase_product,
                'relevance': relevance,
                'analysis': self._analyze_purchase_feedback(purchase.fit_feedback)
            })
        
        # Ordenar por relevancia
        relevant_purchases.sort(key=lambda x: x['relevance'], reverse=True)
        
        return relevant_purchases
    
    def _identify_intent(self, query: str) -> str:
        """Identifica la intención de la consulta."""
        if any(keyword in query for keyword in self.size_keywords):
            return 'size_recommendation'
        elif any(keyword in query for keyword in self.search_keywords):
            return 'product_search'
        elif 'ayuda' in query or 'help' in query:
            return 'help'
        else:
            return 'general'
    
    def _extract_product_ids(self, query: str) -> List[str]:
        """Extrae IDs de productos de la consulta."""
        product_ids = []
        
        for pattern in self.product_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                
                # Normalizar ID del producto
                if match.isdigit():
                    product_id = f"P{match.zfill(3)}"
                else:
                    product_id = match.upper()
                
                if product_id not in product_ids:
                    product_ids.append(product_id)
        
        return product_ids
    
    def _extract_client_ids(self, query: str) -> List[str]:
        """Extrae IDs de clientes de la consulta."""
        client_ids = []
        
        for pattern in self.client_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                
                # Normalizar ID del cliente
                if match.isdigit():
                    client_id = f"C{match.zfill(4)}"
                else:
                    client_id = match.upper()
                
                if client_id not in client_ids:
                    client_ids.append(client_id)
        
        return client_ids
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrae palabras clave relevantes de la consulta."""
        # Palabras clave relacionadas con ropa y ajuste
        clothing_keywords = [
            'abrigo', 'camisa', 'pantalón', 'vestido', 'blusa', 'falda',
            'chaqueta', 'suéter', 'jersey', 'camiseta', 'polo',
            'algodón', 'lana', 'lino', 'poliéster', 'seda',
            'slim', 'regular', 'loose', 'oversized', 'tailored',
            'ajustado', 'holgado', 'entallado'
        ]
        
        found_keywords = []
        words = query.split()
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in clothing_keywords:
                found_keywords.append(clean_word)
        
        return found_keywords
    
    def _calculate_client_similarity(self, client1: Client, client2: Client) -> float:
        """Calcula similitud entre dos clientes."""
        # Similitud de medidas corporales (peso: 50%)
        m1 = client1.body_measurements
        m2 = client2.body_measurements
        
        bust_diff = abs(m1.bust_cm - m2.bust_cm)
        waist_diff = abs(m1.waist_cm - m2.waist_cm)
        hips_diff = abs(m1.hips_cm - m2.hips_cm)
        
        # Convertir diferencias a similitudes (0-1)
        bust_sim = max(0, 1 - bust_diff / 50)  # Normalizar por rango típico
        waist_sim = max(0, 1 - waist_diff / 40)
        hips_sim = max(0, 1 - hips_diff / 50)
        
        measurements_sim = (bust_sim + waist_sim + hips_sim) / 3
        
        # Similitud de altura (peso: 20%)
        height_diff = abs(client1.height_cm - client2.height_cm)
        height_sim = max(0, 1 - height_diff / 50)
        
        # Similitud de preferencias de ajuste (peso: 20%)
        pref_sim = 1.0 if client1.preferred_fit == client2.preferred_fit else 0.5
        
        # Similitud de edad (peso: 10%)
        age_diff = abs(client1.age - client2.age)
        age_sim = max(0, 1 - age_diff / 50)
        
        # Similitud total ponderada
        total_similarity = (
            measurements_sim * 0.5 +
            height_sim * 0.2 +
            pref_sim * 0.2 +
            age_sim * 0.1
        )
        
        return total_similarity
    
    def _calculate_product_similarity(self, product1: Product, product2: Product) -> float:
        """Calcula similitud entre dos productos."""
        similarity = 0.0
        
        # Mismo tipo de ajuste (peso alto)
        if product1.fit == product2.fit:
            similarity += 0.4
        
        # Mismo material (peso medio)
        if product1.fabric == product2.fabric:
            similarity += 0.3
        
        # Similitud en tabla de tallas (peso bajo)
        # Comparar talla M como referencia
        try:
            m1 = product1.size_chart.M
            m2 = product2.size_chart.M
            
            bust_diff = abs(m1.bust_cm - m2.bust_cm)
            waist_diff = abs(m1.waist_cm - m2.waist_cm)
            hips_diff = abs(m1.hips_cm - m2.hips_cm)
            
            avg_diff = (bust_diff + waist_diff + hips_diff) / 3
            size_sim = max(0, 1 - avg_diff / 20)  # Normalizar
            
            similarity += size_sim * 0.3
        except:
            pass
        
        return min(1.0, similarity)
    
    def _analyze_purchase_feedback(self, feedback: str) -> Dict[str, any]:
        """Analiza el feedback de una compra."""
        feedback_lower = feedback.lower()
        
        analysis = {
            'sentiment': 'neutral',
            'fit_issue': None,
            'satisfaction': 0.5
        }
        
        if 'perfect' in feedback_lower or 'comfortable' in feedback_lower:
            analysis['sentiment'] = 'positive'
            analysis['satisfaction'] = 0.9
        elif 'too tight' in feedback_lower:
            analysis['sentiment'] = 'negative'
            analysis['fit_issue'] = 'too_small'
            analysis['satisfaction'] = 0.2
        elif 'too loose' in feedback_lower:
            analysis['sentiment'] = 'negative'
            analysis['fit_issue'] = 'too_large'
            analysis['satisfaction'] = 0.3
        elif 'did not like' in feedback_lower:
            analysis['sentiment'] = 'negative'
            analysis['satisfaction'] = 0.1
        
        return analysis