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
        self._load_data()
    
    def _load_data(self) -> None:
        """Carga los datos de clientes y productos desde los archivos JSON."""
        self._load_clients()
        self._load_products()
    
    def _load_clients(self) -> None:
        """Carga los datos de clientes."""
        client_file = os.path.join(self.data_dir, "client_profiles.json")
        try:
            with open(client_file, 'r', encoding='utf-8') as f:
                clients_data = json.load(f)
            
            for client_data in clients_data:
                client = Client.from_dict(client_data)
                self.clients[client.client_id] = client
                
            print(f"Cargados {len(self.clients)} clientes")
            
        except FileNotFoundError:
            print(f"No se encontró el archivo {client_file}")
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de clientes: {e}")
    
    def _load_products(self) -> None:
        """Carga los datos de productos."""
        product_file = os.path.join(self.data_dir, "product_catalog.json")
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            for product_data in products_data:
                product = Product.from_dict(product_data)
                self.products[product.product_id] = product
                
            print(f"Cargados {len(self.products)} productos")
            
        except FileNotFoundError:
            print(f"No se encontró el archivo {product_file}")
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de productos: {e}")
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Obtener un cliente por su ID.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Cliente encontrado o None
        """
        return self.clients.get(client_id)
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtener un producto por su ID.
        
        Args:
            product_id: ID del producto
            
        Returns:
            Producto encontrado o None
        """
        return self.products.get(product_id)
    
    def search_products(self, query: str, limit: int = 5) -> List[Product]:
        """
        Buscar productos por nombre o ID.
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de productos encontrados
        """
        query = query.lower()
        results = []
        
        for product in self.products.values():
            if (query in product.name.lower() or 
                query in product.product_id.lower() or
                query in product.fabric.lower() or
                query in product.fit.lower()):
                results.append(product)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def search_clients(self, query: str, limit: int = 5) -> List[Client]:
        """
        Buscar clientes por nombre o ID.
        
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
        """Devuelve todos los clientes."""
        return list(self.clients.values())
    
    def get_all_products(self) -> List[Product]:
        """Devuelve todos los productos."""
        return list(self.products.values())
    
    def get_client_stats(self) -> Dict[str, int]:
        """Devolver estadísticas de los clientes."""
        fit_preferences = {}
        for client in self.clients.values():
            fit = client.preferred_fit
            fit_preferences[fit] = fit_preferences.get(fit, 0) + 1
        
        return {
            "total_clients": len(self.clients),
            "fit_preferences": fit_preferences
        }
    
    def get_product_stats(self) -> Dict[str, int]:
        """Calcular estadísticas de los productos."""
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