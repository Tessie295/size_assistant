"""
Cargador de datos corregido para el sistema de recomendaciones.
"""

import json
import os
from typing import Dict, List, Optional
from models.data_models import Client, Product


class DataLoader:
    """Clase para cargar y gestionar los datos de clientes y productos."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Inicializa el cargador de datos.
        
        Args:
            data_dir: Directorio donde se encuentran los archivos JSON
        """
        self.data_dir = data_dir
        self.clients: Dict[str, Client] = {}
        self.products: Dict[str, Product] = {}
        self._loaded = False
        self._load_data()
    
    def is_loaded(self) -> bool:
        """Verifica si los datos fueron cargados correctamente."""
        return self._loaded and len(self.clients) > 0 and len(self.products) > 0
    
    def _load_data(self) -> None:
        """Carga los datos de clientes y productos desde los archivos JSON."""
        try:
            self._load_clients()
            self._load_products()
            self._loaded = True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            self._loaded = False
    
    def _load_clients(self) -> None:
        """Carga los datos de clientes."""
        client_file = os.path.join(self.data_dir, "client_profiles.json")
        try:
            with open(client_file, 'r', encoding='utf-8') as f:
                clients_data = json.load(f)
            
            for client_data in clients_data:
                client = Client.from_dict(client_data)
                self.clients[client.client_id] = client
                
            print(f"✅ Cargados {len(self.clients)} clientes")
            
        except FileNotFoundError:
            print(f"❌ No se encontró el archivo {client_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON de clientes: {e}")
            raise
    
    def _load_products(self) -> None:
        """Carga los datos de productos."""
        product_file = os.path.join(self.data_dir, "product_catalog.json")
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            for product_data in products_data:
                product = Product.from_dict(product_data)
                self.products[product.product_id] = product
                
            print(f"✅ Cargados {len(self.products)} productos")
            
        except FileNotFoundError:
            print(f"❌ No se encontró el archivo {product_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON de productos: {e}")
            raise
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Obtiene un cliente por su ID.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Cliente encontrado o None
        """
        return self.clients.get(client_id)
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtiene un producto por su ID.
        
        Args:
            product_id: ID del producto
            
        Returns:
            Producto encontrado o None
        """
        return self.products.get(product_id)
    
    def search_products(self, query: str, limit: int = 5) -> List[Product]:
            """
            Busca productos por nombre, ID, material o ajuste.
            
            Args:
                query: Término de búsqueda
                limit: Número máximo de resultados
                
            Returns:
                Lista de productos encontrados
            """
            query = query.lower().strip()
            results = []
            
            # Mapeo de términos en español a inglés
            term_mapping = {
                'ajuste': 'fit',
                'material': 'fabric',
                'algodón': 'cotton',
                'lana': 'wool',
                'lino': 'linen',
                'poliéster': 'polyester',
                'mezcla': 'blend'
            }
            
            # Normalizar términos de búsqueda
            search_terms = [query]
            for esp_term, eng_term in term_mapping.items():
                if esp_term in query:
                    search_terms.append(query.replace(esp_term, eng_term))
            
            # Buscar en todos los productos
            for product in self.products.values():
                product_score = 0
                
                for search_term in search_terms:
                    # Búsqueda exacta por ID
                    if search_term == product.product_id.lower():
                        product_score += 100
                        break
                    
                    # Búsqueda en nombre
                    if search_term in product.name.lower():
                        product_score += 50
                    
                    # Búsqueda en ajuste (fit)
                    if search_term in product.fit.lower():
                        product_score += 30
                    
                    # Búsqueda en material (fabric)
                    if search_term in product.fabric.lower():
                        product_score += 30
                    
                    # Búsqueda por palabras parciales
                    search_words = search_term.split()
                    for word in search_words:
                        if len(word) > 2:  # Evitar palabras muy cortas
                            if word in product.name.lower():
                                product_score += 10
                            if word in product.fit.lower():
                                product_score += 15
                            if word in product.fabric.lower():
                                product_score += 15
                
                if product_score > 0:
                    results.append((product, product_score))
            
            # Ordenar por puntuación y retornar los mejores resultados
            results.sort(key=lambda x: x[1], reverse=True)
            return [product for product, score in results[:limit]]
    
    def search_clients(self, query: str, limit: int = 5) -> List[Client]:
        """
        Busca clientes por nombre o ID.
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de clientes encontrados
        """
        query = query.lower()
        results = []
        
        for client in self.clients.values():
            if (query in client.name.lower() or 
                query in client.client_id.lower()):
                results.append(client)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_clients(self) -> List[Client]:
        """Retorna todos los clientes."""
        return list(self.clients.values())
    
    def get_all_products(self) -> List[Product]:
        """Retorna todos los productos."""
        return list(self.products.values())
    
    def get_client_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de los clientes."""
        fit_preferences = {}
        for client in self.clients.values():
            fit = client.preferred_fit
            fit_preferences[fit] = fit_preferences.get(fit, 0) + 1
        
        return {
            "total_clients": len(self.clients),
            "fit_preferences": fit_preferences
        }
    
    def get_product_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de los productos."""
        fit_types = {}
        fabrics = {}
        
        for product in self.products.values():
            fit = product.fit
            fabric = product.fabric
            
            fit_types[fit] = fit_types.get(fit, 0) + 1
            fabrics[fabric] = fabrics.get(fabric, 0) + 1
        
        return {
            "total_products": len(self.products),
            "fit_types": fit_types,
            "fabrics": fabrics
        }