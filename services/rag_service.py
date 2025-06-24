import re
from typing import List, Dict, Tuple, Optional
from models.data_models import Client, Product
from data.data_loader import DataLoader


class RAGService:
    """Servicio para recuperar información relevante del contexto."""
    
    def __init__(self, data_loader: DataLoader):
        """
        Inicializa el servicio RAG.
        
        Args:
            data_loader: Instancia del cargador de datos
        """
        self.data_loader = data_loader
        
        # Patrones mejorados para identificar entidades
        self.product_patterns = [
            r'\bP(\d{3})\b',  # P001, P002, etc.
            r'\bP(\d{1,2})\b',  # P1, P2, etc.
            r'producto\s+P(\d+)',
            r'product\s*(\d+)',
        ]
        
        self.client_patterns = [
            r'\bC(\d{4})\b',  # C0001, C0002, etc.
            r'\bC(\d{1,3})\b',  # C1, C01, etc.
            r'cliente\s+C(\d+)',
            r'client\s+C(\d+)',
            r'\bUser(\d+)\b',  # User1, User2, etc.
            r'usuario\s+(\d+)',
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
        
        # Palabras clave visuales
        self.visual_keywords = [
            'muestra', 'enseña', 'ver', 'imagen', 'visual', 'visualizar',
            'cómo se ve', 'como queda', 'genera', 'avatar'
        ]
        
        # Palabras de continuación de conversación
        self.continuation_keywords = [
            'si', 'sí', 'yes', 'vale', 'ok', 'okay', 'perfecto',
            'claro', 'por favor', 'hazlo', 'genéralo', 'muéstralo'
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
            'original_query': query,
            'has_visual_intent': any(keyword in query_lower for keyword in self.visual_keywords),
            'is_continuation': self._is_continuation_query(query_lower)
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
            'confidence': 0.0,
            'has_visual_intent': parsed_query.get('has_visual_intent', False),
            'is_continuation': parsed_query.get('is_continuation', False)
        }
        
        # Recuperar clientes
        client_ids = parsed_query['client_ids']
        print(f"🔍 Buscando clientes: {client_ids}")
        
        for client_id in client_ids:
            client = self.data_loader.get_client(client_id)
            if client:
                context['clients'].append(client)
                context['confidence'] += 0.3
                print(f"✅ Cliente encontrado: {client_id} - {client.name}")
            else:
                print(f"❌ Cliente no encontrado: {client_id}")
        
        # Recuperar productos
        product_ids = parsed_query['product_ids']
        print(f"🔍 Buscando productos: {product_ids}")
        
        for product_id in product_ids:
            product = self.data_loader.get_product(product_id)
            if product:
                context['products'].append(product)
                context['confidence'] += 0.3
                print(f"✅ Producto encontrado: {product_id} - {product.name}")
            else:
                print(f"❌ Producto no encontrado: {product_id}")
        
        # Si no hay IDs específicos, buscar por palabras clave
        if not context['products'] and parsed_query['keywords'] and parsed_query['intent'] == 'product_search':
            search_terms = ' '.join(parsed_query['keywords'])
            found_products = self.data_loader.search_products(search_terms, limit=10)
            context['products'].extend(found_products)
            context['confidence'] += 0.2 if found_products else 0.0
            print(f"🔍 Búsqueda por palabras clave '{search_terms}': {len(found_products)} productos")
        
        # Búsqueda específica por características de productos
        if not context['products'] and parsed_query['intent'] == 'product_search':
            # Buscar por ajuste específico
            query_lower = parsed_query['original_query'].lower()
            
            # Buscar productos por ajuste
            fit_terms = ['slim', 'regular', 'oversized', 'loose', 'tailored']
            for fit_term in fit_terms:
                if fit_term in query_lower:
                    matching_products = [p for p in self.data_loader.get_all_products() 
                                       if fit_term.lower() in p.fit.lower()]
                    context['products'].extend(matching_products[:10])
                    context['confidence'] += 0.3
                    print(f"🔍 Búsqueda por ajuste '{fit_term}': {len(matching_products)} productos")
                    break
            
            # Buscar por material
            fabric_terms = ['cotton', 'wool', 'linen', 'polyester', 'blend', 'algodón', 'lana']
            for fabric_term in fabric_terms:
                if fabric_term in query_lower and not context['products']:
                    matching_products = [p for p in self.data_loader.get_all_products() 
                                       if fabric_term.lower() in p.fabric.lower()]
                    context['products'].extend(matching_products[:10])
                    context['confidence'] += 0.3
                    print(f"🔍 Búsqueda por material '{fabric_term}': {len(matching_products)} productos")
                    break
        
        # Ajustar confianza
        context['confidence'] = min(1.0, context['confidence'])
        
        print(f"📊 Contexto final: {len(context['clients'])} clientes, {len(context['products'])} productos")
        
        return context
    
    def _identify_intent(self, query: str) -> str:
        """Identifica la intención de la consulta."""
        # Primero verificar si es una continuación de conversación
        if self._is_continuation_query(query):
            return 'size_recommendation'  # Asumir que quiere continuar con recomendación
        
        # Verificar si es una búsqueda de productos (más específico)
        if any(keyword in query for keyword in self.search_keywords):
            return 'product_search'
        
        # Patrones específicos de búsqueda de productos
        search_patterns = [
            r'productos?\s+(con|de|que)',  # "productos con", "productos de"
            r'busca\w*\s+productos?',     # "buscar productos"
            r'encuentra?\w*\s+productos?', # "encontrar productos"
            r'muestra\w*\s+productos?',   # "mostrar productos"
            r'lista\w*\s+productos?',     # "listar productos"
            r'qué productos?',            # "qué productos"
            r'cuáles? productos?',        # "cuáles productos"
        ]
        
        for pattern in search_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return 'product_search'
        
        # Si menciona características de productos sin cliente específico, es búsqueda
        if any(keyword in query for keyword in ['ajuste', 'material', 'fabric', 'fit', 'slim', 'regular', 'oversized', 'loose', 'tailored']):
            # Solo si no hay un cliente específico mencionado
            if not self._extract_client_ids(query):
                return 'product_search'
        
        if any(keyword in query for keyword in self.size_keywords):
            return 'size_recommendation'
        elif any(keyword in query for keyword in self.visual_keywords):
            return 'size_recommendation'  # Visual también implica recomendación
        elif 'ayuda' in query or 'help' in query:
            return 'help'
        else:
            return 'general'
    
    def _is_continuation_query(self, query: str) -> bool:
        """Verifica si la consulta es una continuación de conversación."""
        query_clean = query.strip().lower()
        
        # Consultas muy cortas que suelen ser continuaciones
        if len(query_clean) <= 10 and any(keyword in query_clean for keyword in self.continuation_keywords):
            return True
        
        # Patrones específicos de continuación
        continuation_patterns = [
            r'^(si|sí|yes|vale|ok|okay)\s*$',
            r'^(por favor|hazlo|genéralo|muéstralo)$',
            r'^(claro|perfecto|correcto)$'
        ]
        
        for pattern in continuation_patterns:
            if re.match(pattern, query_clean):
                return True
        
        return False
    
    def _extract_product_ids(self, query: str) -> List[str]:
        """Extrae IDs de productos de la consulta."""
        product_ids = []
        
        for pattern in self.product_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                # Normalizar ID del producto
                if match.isdigit():
                    # Formatear con ceros a la izquierda si es necesario
                    if len(match) == 1:
                        product_id = f"P00{match}"
                    elif len(match) == 2:
                        product_id = f"P0{match}"
                    elif len(match) == 3:
                        product_id = f"P{match}"
                    else:
                        product_id = f"P{match}"
                else:
                    product_id = f"P{match}"
                
                if product_id not in product_ids:
                    product_ids.append(product_id)
        
        return product_ids
    
    def _extract_client_ids(self, query: str) -> List[str]:
        """Extrae IDs de clientes de la consulta."""
        client_ids = []
        
        for pattern in self.client_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                # Normalizar ID del cliente
                if match.isdigit():
                    # Para User1, User2, etc.
                    if 'user' in pattern.lower():
                        # Mapear User1 -> C0001, User2 -> C0002, etc.
                        user_num = int(match)
                        if user_num <= 100:  # Límite razonable
                            client_id = f"C{user_num:04d}"
                        else:
                            continue
                    else:
                        # Formatear con ceros a la izquierda
                        if len(match) == 1:
                            client_id = f"C000{match}"
                        elif len(match) == 2:
                            client_id = f"C00{match}"
                        elif len(match) == 3:
                            client_id = f"C0{match}"
                        elif len(match) == 4:
                            client_id = f"C{match}"
                        else:
                            client_id = f"C{match}"
                else:
                    client_id = f"C{match}"
                
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
            'ajustado', 'holgado', 'entallado',
            'azul', 'rojo', 'verde', 'negro', 'blanco', 'gris', 'rosa',
            'cotton', 'wool', 'blend', 'polyester'
        ]
        
        found_keywords = []
        words = query.split()
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in clothing_keywords:
                found_keywords.append(clean_word)
        
        return found_keywords
    
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