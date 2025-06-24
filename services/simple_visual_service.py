"""
Servicio visual simplificado corregido.
"""

import os
import base64
import time
from io import BytesIO
from typing import Dict, Any, Optional
from pathlib import Path
from models.data_models import Client, Product

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SimpleVisualService:
    """Servicio visual simplificado con capacidades básicas."""
    
    def __init__(self, output_dir: str = "assets/generated"):
        """Inicializa el servicio visual."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Colores disponibles
        self.colors = {
            "azul": (70, 130, 180),
            "rojo": (220, 20, 60),
            "verde": (34, 139, 34),
            "negro": (0, 0, 0),
            "blanco": (255, 255, 255),
            "gris": (128, 128, 128),
            "rosa": (255, 182, 193),
            "amarillo": (255, 215, 0),
            "morado": (147, 112, 219),
            "naranja": (255, 165, 0)
        }
        
        # Configuración del canvas
        self.canvas_size = (400, 600)
        self.avatar_color = (255, 228, 196)  # Color piel
    
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible."""
        return PIL_AVAILABLE
    
    def generate_avatar_image(
        self,
        client: Client,
        product: Product,
        size: str,
        color: str = "azul"
    ) -> Dict[str, Any]:
        """
        Genera una imagen de avatar con la prenda.
        
        Args:
            client: Cliente
            product: Producto
            size: Talla recomendada
            color: Color de la prenda
            
        Returns:
            Diccionario con información de la imagen generada
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "PIL no está disponible"
            }
        
        try:
            # Crear imagen base
            img = Image.new('RGB', self.canvas_size, (240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            # Dibujar avatar base
            self._draw_avatar_base(draw, client)
            
            # Dibujar prenda
            garment_color = self.colors.get(color.lower(), (100, 100, 150))
            self._draw_garment(draw, product, garment_color)
            
            # Añadir información del producto
            self._add_product_info(draw, client, product, size, color)
            
            # Generar nombre del archivo
            timestamp = int(time.time())
            filename = f"{client.client_id}_{product.product_id}_{size}_{color}_{timestamp}.png"
            filepath = self.output_dir / filename
            
            # Guardar imagen
            img.save(filepath, "PNG")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "base64": img_base64,
                "client_id": client.client_id,
                "product_id": product.product_id,
                "size": size,
                "color": color
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _draw_avatar_base(self, draw: ImageDraw.Draw, client: Client):
        """Dibuja el avatar base del cliente."""
        center_x = self.canvas_size[0] // 2
        
        # Calcular proporciones basadas en las medidas del cliente
        height_ratio = min(client.height_cm / 175, 1.2)
        avatar_height = int(self.canvas_size[1] * 0.8 * height_ratio)
        
        # Medidas escaladas
        measurements = client.body_measurements
        scale = self.canvas_size[0] / 120
        
        bust_width = int(measurements.bust_cm * scale * 0.6)
        waist_width = int(measurements.waist_cm * scale * 0.6)
        hips_width = int(measurements.hips_cm * scale * 0.6)
        
        # Posiciones
        start_y = 60
        head_radius = 25
        
        # Dibujar cabeza
        draw.ellipse([
            center_x - head_radius, start_y,
            center_x + head_radius, start_y + head_radius * 2
        ], fill=self.avatar_color, outline=(200, 200, 200))
        
        # Dibujar cuerpo (silueta simplificada)
        torso_top = start_y + head_radius * 2 + 10
        torso_height = int(avatar_height * 0.4)
        
        # Hombros a cintura
        body_points = [
            (center_x - bust_width//2, torso_top),
            (center_x + bust_width//2, torso_top),
            (center_x + waist_width//2, torso_top + torso_height//2),
            (center_x + hips_width//2, torso_top + torso_height),
            (center_x - hips_width//2, torso_top + torso_height),
            (center_x - waist_width//2, torso_top + torso_height//2),
        ]
        
        draw.polygon(body_points, fill=self.avatar_color, outline=(200, 200, 200))
        
        # Dibujar brazos
        arm_width = 15
        arm_length = torso_height * 0.8
        
        # Brazo izquierdo
        draw.rectangle([
            center_x - bust_width//2 - arm_width, torso_top + 20,
            center_x - bust_width//2, torso_top + 20 + arm_length
        ], fill=self.avatar_color, outline=(200, 200, 200))
        
        # Brazo derecho
        draw.rectangle([
            center_x + bust_width//2, torso_top + 20,
            center_x + bust_width//2 + arm_width, torso_top + 20 + arm_length
        ], fill=self.avatar_color, outline=(200, 200, 200))
        
        # Dibujar piernas
        leg_top = torso_top + torso_height
        leg_height = int(avatar_height * 0.5)
        leg_width = hips_width // 3
        
        # Pierna izquierda
        draw.rectangle([
            center_x - leg_width, leg_top,
            center_x - 5, leg_top + leg_height
        ], fill=self.avatar_color, outline=(200, 200, 200))
        
        # Pierna derecha
        draw.rectangle([
            center_x + 5, leg_top,
            center_x + leg_width, leg_top + leg_height
        ], fill=self.avatar_color, outline=(200, 200, 200))
    
    def _draw_garment(self, draw: ImageDraw.Draw, product: Product, color: tuple):
        """Dibuja la prenda sobre el avatar."""
        center_x = self.canvas_size[0] // 2
        
        # Posición de la prenda (sobre el torso)
        garment_top = 120
        garment_width = 120
        garment_height = 140
        
        # Dibujar prenda como rectángulo redondeado
        garment_rect = [
            center_x - garment_width//2, garment_top,
            center_x + garment_width//2, garment_top + garment_height
        ]
        
        draw.rounded_rectangle(garment_rect, radius=10, fill=color, outline=(0, 0, 0), width=2)
        
        # Añadir detalles según el tipo de ajuste
        if product.fit.lower() == "oversized":
            # Hacer la prenda más ancha
            oversized_rect = [
                center_x - garment_width//2 - 20, garment_top,
                center_x + garment_width//2 + 20, garment_top + garment_height + 20
            ]
            draw.rounded_rectangle(oversized_rect, radius=15, fill=color, outline=(0, 0, 0), width=2)
        elif product.fit.lower() == "slim":
            # Hacer la prenda más ajustada
            slim_rect = [
                center_x - garment_width//2 + 10, garment_top,
                center_x + garment_width//2 - 10, garment_top + garment_height - 10
            ]
            draw.rounded_rectangle(slim_rect, radius=8, fill=color, outline=(0, 0, 0), width=2)
        
        # Añadir mangas
        sleeve_width = 25
        sleeve_height = 80
        
        # Manga izquierda
        draw.rounded_rectangle([
            center_x - garment_width//2 - sleeve_width, garment_top + 10,
            center_x - garment_width//2, garment_top + 10 + sleeve_height
        ], radius=5, fill=color, outline=(0, 0, 0))
        
        # Manga derecha
        draw.rounded_rectangle([
            center_x + garment_width//2, garment_top + 10,
            center_x + garment_width//2 + sleeve_width, garment_top + 10 + sleeve_height
        ], radius=5, fill=color, outline=(0, 0, 0))
    
    def _add_product_info(self, draw: ImageDraw.Draw, client: Client, product: Product, size: str, color: str):
        """Añade información del producto a la imagen."""
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        info_lines = [
            f"Cliente: {client.name}",
            f"Producto: {product.name}",
            f"Talla: {size}",
            f"Color: {color.title()}",
            f"Ajuste: {product.fit}",
            f"Material: {product.fabric}"
        ]
        
        # Dibujar información en la parte inferior
        y_start = self.canvas_size[1] - len(info_lines) * 16 - 10
        
        for i, line in enumerate(info_lines):
            y_pos = y_start + i * 16
            draw.text((10, y_pos), line, fill=(0, 0, 0), font=font)
    
    def cleanup_old_images(self, max_age_hours: int = 24):
        """Limpia imágenes antiguas."""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in self.output_dir.glob("*.png"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    print(f"Imagen eliminada: {file_path.name}")
            
            print(f"Limpieza completada en {self.output_dir}")
            
        except Exception as e:
            print(f"Error durante la limpieza: {e}")
    
    def list_generated_images(self) -> list:
        """Lista las imágenes generadas."""
        try:
            return [f.name for f in self.output_dir.glob("*.png")]
        except Exception:
            return []