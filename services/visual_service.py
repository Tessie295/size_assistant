import os
import base64
import time
import math
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from models.data_models import Client, Product

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VisualService:
    """Servicio visual para avatares."""
    
    def __init__(self, output_dir: str = "assets/generated"):
        """Inicializa el servicio visual."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Colores con gradientes
        self.colors = {
            "azul": [(70, 130, 180), (100, 149, 237)],        # Steel blue to cornflower blue
            "rojo": [(220, 20, 60), (255, 69, 0)],            # Crimson to red orange
            "verde": [(34, 139, 34), (50, 205, 50)],          # Forest green to lime green
            "negro": [(40, 40, 40), (80, 80, 80)],            # Dark grays instead of pure black
            "blanco": [(245, 245, 245), (255, 255, 255)],     # Off-white to white
            "gris": [(128, 128, 128), (169, 169, 169)],       # Gray to dark gray
            "rosa": [(255, 182, 193), (255, 20, 147)],        # Light pink to deep pink
            "amarillo": [(255, 215, 0), (255, 255, 0)],       # Gold to yellow
            "morado": [(147, 112, 219), (138, 43, 226)],      # Medium orchid to blue violet
            "naranja": [(255, 165, 0), (255, 140, 0)]         # Orange to dark orange
        }
        
        # Configuración del canvas
        self.canvas_size = (400, 600)
        self.avatar_colors = {
            'skin': [(255, 228, 196), (245, 215, 185)],      # Peach puff with variation
            'hair': [(139, 69, 19), (160, 82, 45)],          # Saddle brown
            'eyes': [(70, 130, 180), (100, 149, 237)]        # Blue eyes
        }
    
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
        Genera una imagen de avatar mejorada con la prenda.
        
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
            # Crear imagen base con gradiente de fondo
            img = self._create_background()
            draw = ImageDraw.Draw(img)
            
            # Calcular proporciones del avatar
            avatar_props = self._calculate_realistic_proportions(client)
            
            # Dibujar avatar con mejor anatomía
            self._draw_realistic_avatar(draw, client, avatar_props)
            
            # Dibujar prenda con mejor ajuste
            garment_colors = self.colors.get(color.lower(), [(100, 100, 150), (120, 120, 170)])
            self._draw_realistic_garment(draw, product, garment_colors, avatar_props)
            
            # Añadir efectos y sombras
            img = self._add_lighting_effects(img)
            
            # Añadir información del producto con mejor tipografía
            self._add_enhanced_product_info(draw, client, product, size, color)
            
            # Generar nombre del archivo
            timestamp = int(time.time())
            filename = f"{client.client_id}_{product.product_id}_{size}_{color}_{timestamp}.png"
            filepath = self.output_dir / filename
            
            # Guardar imagen
            img.save(filepath, "PNG", quality=95)
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG', quality=95)
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
    
    def _create_background(self) -> Image.Image:
        """Crea un fondo con gradiente sutil."""
        img = Image.new('RGB', self.canvas_size, (240, 245, 250))
        
        # Crear gradiente sutil
        for y in range(self.canvas_size[1]):
            # Gradiente de azul muy claro a gris muy claro
            ratio = y / self.canvas_size[1]
            r = int(240 + (245 - 240) * ratio)
            g = int(245 + (248 - 245) * ratio)
            b = int(250 + (252 - 250) * ratio)
            
            for x in range(self.canvas_size[0]):
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    def _calculate_realistic_proportions(self, client: Client) -> Dict[str, Any]:
        """Calcula proporciones realistas del avatar basadas en las medidas del cliente."""
        # Normalizar altura (170cm = referencia)
        height_ratio = client.height_cm / 170
        avatar_height = int(self.canvas_size[1] * 0.75 * height_ratio)
        
        # Calcular proporciones corporales realistas
        measurements = client.body_measurements
        
        # Usar golden ratio y proporciones humanas reales
        head_size = avatar_height // 8  # Cabeza = 1/8 de altura total
        neck_height = head_size // 4
        torso_height = int(avatar_height * 0.45)  # 45% de altura
        legs_height = int(avatar_height * 0.45)   # 45% de altura
        
        # Escalado más realista para el ancho
        scale_factor = self.canvas_size[0] / 140
        
        # Proporciones más anatómicas
        bust_width = int(measurements.bust_cm * scale_factor * 0.55)
        waist_width = int(measurements.waist_cm * scale_factor * 0.55)
        hips_width = int(measurements.hips_cm * scale_factor * 0.55)
        shoulder_width = int(bust_width * 1.2)  # Hombros más anchos que el busto
        
        # Posicionamiento centrado
        center_x = self.canvas_size[0] // 2
        start_y = 40
        
        return {
            'center_x': center_x,
            'start_y': start_y,
            'avatar_height': avatar_height,
            'head_size': head_size,
            'neck_height': neck_height,
            'torso_height': torso_height,
            'legs_height': legs_height,
            'bust_width': bust_width,
            'waist_width': waist_width,
            'hips_width': hips_width,
            'shoulder_width': shoulder_width,
            'scale_factor': scale_factor
        }
    
    def _draw_realistic_avatar(self, draw: ImageDraw.Draw, client: Client, props: Dict[str, Any]):
        """Dibuja un avatar más realista con mejor anatomía."""
        center_x = props['center_x']
        start_y = props['start_y']
        
        # Colores de piel con gradiente
        skin_color1, skin_color2 = self.avatar_colors['skin']
        
        # 1. CABEZA más realista
        head_radius = props['head_size'] // 2
        head_y = start_y + head_radius
        
        # Cabeza con forma más ovalada
        head_bbox = [
            center_x - head_radius, start_y,
            center_x + head_radius, head_y + int(head_radius * 1.3)
        ]
        draw.ellipse(head_bbox, fill=skin_color1, outline=(200, 180, 160), width=2)
        
        # Rasgos faciales básicos
        self._draw_facial_features(draw, center_x, start_y + head_radius, head_radius)
        
        # 2. CUELLO proporcionado
        neck_top = head_bbox[3]
        neck_bottom = neck_top + props['neck_height']
        neck_width = head_radius // 2
        
        draw.rectangle([
            center_x - neck_width, neck_top,
            center_x + neck_width, neck_bottom
        ], fill=skin_color1, outline=(200, 180, 160))
        
        # 3. TORSO con forma anatómica
        torso_top = neck_bottom
        torso_bottom = torso_top + props['torso_height']
        
        # Crear puntos para forma de torso más realista
        torso_points = self._calculate_torso_points(
            center_x, torso_top, torso_bottom, props
        )
        
        draw.polygon(torso_points, fill=skin_color1, outline=(200, 180, 160), width=2)
        
        # 4. BRAZOS más naturales
        self._draw_realistic_arms(draw, center_x, torso_top, props, skin_color1)
        
        # 5. PIERNAS proporcionadas
        self._draw_realistic_legs(draw, center_x, torso_bottom, props, skin_color1)
    
    def _draw_facial_features(self, draw: ImageDraw.Draw, center_x: int, center_y: int, head_radius: int):
        """Dibuja rasgos faciales básicos."""
        # Ojos
        eye_y = center_y - head_radius // 4
        eye_size = head_radius // 6
        
        # Ojo izquierdo
        draw.ellipse([
            center_x - head_radius//3 - eye_size, eye_y - eye_size//2,
            center_x - head_radius//3 + eye_size, eye_y + eye_size//2
        ], fill=(255, 255, 255), outline=(0, 0, 0))
        
        # Pupila izquierda
        draw.ellipse([
            center_x - head_radius//3 - eye_size//2, eye_y - eye_size//4,
            center_x - head_radius//3 + eye_size//2, eye_y + eye_size//4
        ], fill=(70, 130, 180))
        
        # Ojo derecho
        draw.ellipse([
            center_x + head_radius//3 - eye_size, eye_y - eye_size//2,
            center_x + head_radius//3 + eye_size, eye_y + eye_size//2
        ], fill=(255, 255, 255), outline=(0, 0, 0))
        
        # Pupila derecha
        draw.ellipse([
            center_x + head_radius//3 - eye_size//2, eye_y - eye_size//4,
            center_x + head_radius//3 + eye_size//2, eye_y + eye_size//4
        ], fill=(70, 130, 180))
        
        # Nariz simple
        nose_y = center_y
        draw.ellipse([
            center_x - 2, nose_y - 3,
            center_x + 2, nose_y + 3
        ], fill=(240, 200, 180))
        
        # Boca
        mouth_y = center_y + head_radius // 3
        draw.arc([
            center_x - head_radius//4, mouth_y - 5,
            center_x + head_radius//4, mouth_y + 5
        ], start=0, end=180, fill=(200, 100, 100), width=2)
    
    def _calculate_torso_points(self, center_x: int, torso_top: int, torso_bottom: int, props: Dict[str, Any]) -> list:
        """Calcula puntos para un torso."""
        shoulder_w = props['shoulder_width'] // 2
        bust_w = props['bust_width'] // 2
        waist_w = props['waist_width'] // 2
        hips_w = props['hips_width'] // 2
        
        torso_height = torso_bottom - torso_top
        
        # Puntos del torso con curvas más naturales
        points = [
            # Hombros
            (center_x - shoulder_w, torso_top + torso_height * 0.1),
            (center_x + shoulder_w, torso_top + torso_height * 0.1),
            
            # Bajada hacia busto
            (center_x + bust_w, torso_top + torso_height * 0.3),
            
            # Cintura
            (center_x + waist_w, torso_top + torso_height * 0.65),
            
            # Caderas
            (center_x + hips_w, torso_bottom),
            (center_x - hips_w, torso_bottom),
            
            # Cintura izquierda
            (center_x - waist_w, torso_top + torso_height * 0.65),
            
            # Busto izquierdo
            (center_x - bust_w, torso_top + torso_height * 0.3),
        ]
        
        return points
    
    def _draw_realistic_arms(self, draw: ImageDraw.Draw, center_x: int, torso_top: int, props: Dict[str, Any], skin_color: tuple):
        """Dibuja brazos."""
        shoulder_w = props['shoulder_width'] // 2
        arm_length = int(props['torso_height'] * 0.8)
        arm_width = int(props['scale_factor'] * 8)
        
        # Brazo izquierdo
        arm_left_x = center_x - shoulder_w
        self._draw_single_arm(draw, arm_left_x, torso_top + 20, arm_width, arm_length, skin_color, "left")
        
        # Brazo derecho
        arm_right_x = center_x + shoulder_w
        self._draw_single_arm(draw, arm_right_x, torso_top + 20, arm_width, arm_length, skin_color, "right")
    
    def _draw_single_arm(self, draw: ImageDraw.Draw, x: int, y: int, width: int, length: int, color: tuple, side: str):
        """Dibuja un brazo individual con articulaciones."""
        # Brazo superior
        upper_arm_length = length // 2
        if side == "left":
            draw.rectangle([x - width, y, x, y + upper_arm_length], fill=color, outline=(200, 180, 160))
            # Antebrazo
            draw.rectangle([x - width, y + upper_arm_length, x, y + length], fill=color, outline=(200, 180, 160))
        else:
            draw.rectangle([x, y, x + width, y + upper_arm_length], fill=color, outline=(200, 180, 160))
            # Antebrazo
            draw.rectangle([x, y + upper_arm_length, x + width, y + length], fill=color, outline=(200, 180, 160))
        
        # Mano simple
        hand_size = width // 2
        if side == "left":
            draw.ellipse([x - width - hand_size//2, y + length - hand_size//2, 
                         x - width + hand_size//2, y + length + hand_size//2], fill=color)
        else:
            draw.ellipse([x + width - hand_size//2, y + length - hand_size//2,
                         x + width + hand_size//2, y + length + hand_size//2], fill=color)
    
    def _draw_realistic_legs(self, draw: ImageDraw.Draw, center_x: int, torso_bottom: int, props: Dict[str, Any], skin_color: tuple):
        """Dibuja piernas."""
        leg_width = int(props['hips_width'] // 3)
        leg_length = props['legs_height']
        thigh_length = leg_length // 2
        
        # Pierna izquierda
        left_leg_center = center_x - leg_width // 2
        
        # Muslo izquierdo
        draw.rectangle([
            left_leg_center - leg_width//2, torso_bottom,
            left_leg_center + leg_width//2, torso_bottom + thigh_length
        ], fill=skin_color, outline=(200, 180, 160))
        
        # Pantorrilla izquierda (más estrecha)
        calf_width = int(leg_width * 0.8)
        draw.rectangle([
            left_leg_center - calf_width//2, torso_bottom + thigh_length,
            left_leg_center + calf_width//2, torso_bottom + leg_length
        ], fill=skin_color, outline=(200, 180, 160))
        
        # Pierna derecha
        right_leg_center = center_x + leg_width // 2
        
        # Muslo derecho
        draw.rectangle([
            right_leg_center - leg_width//2, torso_bottom,
            right_leg_center + leg_width//2, torso_bottom + thigh_length
        ], fill=skin_color, outline=(200, 180, 160))
        
        # Pantorrilla derecha
        draw.rectangle([
            right_leg_center - calf_width//2, torso_bottom + thigh_length,
            right_leg_center + calf_width//2, torso_bottom + leg_length
        ], fill=skin_color, outline=(200, 180, 160))
        
        # Pies simples
        foot_width = leg_width
        foot_height = leg_width // 2
        
        # Pie izquierdo
        draw.ellipse([
            left_leg_center - foot_width//2, torso_bottom + leg_length - foot_height//2,
            left_leg_center + foot_width//2, torso_bottom + leg_length + foot_height//2
        ], fill=(101, 67, 33))  # Color zapato
        
        # Pie derecho
        draw.ellipse([
            right_leg_center - foot_width//2, torso_bottom + leg_length - foot_height//2,
            right_leg_center + foot_width//2, torso_bottom + leg_length + foot_height//2
        ], fill=(101, 67, 33))  # Color zapato
    
    def _draw_realistic_garment(self, draw: ImageDraw.Draw, product: Product, colors: list, props: Dict[str, Any]):
        """Dibuja la prenda."""
        center_x = props['center_x']
        color1, color2 = colors
        
        # Calcular posición de la prenda según el torso
        torso_top = props['start_y'] + props['head_size'] + props['neck_height']
        
        # Ajustar según el tipo de fit del producto
        fit_multiplier = self._get_fit_multiplier(product.fit)
        
        garment_width = int(props['bust_width'] * fit_multiplier)
        garment_height = int(props['torso_height'] * 0.9)
        
        # Crear gradiente para la prenda
        self._draw_garment_with_gradient(draw, center_x, torso_top, garment_width, garment_height, colors, product)
        
        # Añadir detalles según el tipo de prenda
        self._add_garment_details(draw, center_x, torso_top, garment_width, garment_height, product, color1)
        
        # Dibujar mangas mejoradas
        self._draw_realistic_sleeves(draw, center_x, torso_top, props, colors, product)
    
    def _get_fit_multiplier(self, fit: str) -> float:
        """Obtiene el multiplicador de ajuste según el tipo de fit."""
        fit_multipliers = {
            'Slim': 0.9,
            'Tailored': 1.0,
            'Regular': 1.1,
            'Loose': 1.3,
            'Oversized': 1.5
        }
        return fit_multipliers.get(fit, 1.0)
    
    def _draw_garment_with_gradient(self, draw: ImageDraw.Draw, center_x: int, top: int, width: int, height: int, colors: list, product: Product):
        """Dibuja la prenda principal con gradiente."""
        color1, color2 = colors
        
        # Crear efecto de gradiente vertical
        for i in range(height):
            ratio = i / height
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            
            current_color = (r, g, b)
            
            # Variar el ancho para crear forma más natural
            current_width = width - int(abs(i - height//2) * 0.1)
            
            draw.rectangle([
                center_x - current_width//2, top + i,
                center_x + current_width//2, top + i + 1
            ], fill=current_color)
        
        # Contorno de la prenda
        draw.rectangle([
            center_x - width//2, top,
            center_x + width//2, top + height
        ], outline=(max(0, color1[0]-40), max(0, color1[1]-40), max(0, color1[2]-40)), width=2)
    
    def _add_garment_details(self, draw: ImageDraw.Draw, center_x: int, top: int, width: int, height: int, product: Product, color: tuple):
        """Añade detalles específicos según el tipo de prenda."""
        # Cuello/escote
        neck_width = width // 4
        neck_depth = height // 8
        
        # Escote en V o redondo
        draw.arc([
            center_x - neck_width, top - neck_depth//2,
            center_x + neck_width, top + neck_depth
        ], start=0, end=180, fill=(max(0, color[0]-20), max(0, color[1]-20), max(0, color[2]-20)), width=3)
        
        # Detalles según el ajuste
        if product.fit == 'Tailored':
            # Líneas de sastre
            draw.line([center_x - width//3, top + height//4, center_x - width//4, top + height//2], 
                     fill=(max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30)), width=2)
            draw.line([center_x + width//4, top + height//2, center_x + width//3, top + height//4], 
                     fill=(max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30)), width=2)
        
        elif 'Cotton' in product.fabric or 'Linen' in product.fabric:
            # Textura de tela natural (puntos sutiles)
            for i in range(5):
                for j in range(8):
                    x = center_x - width//2 + (width * j // 8) + (i % 2) * 10
                    y = top + (height * i // 5)
                    if center_x - width//2 < x < center_x + width//2:
                        draw.point((x, y), fill=(max(0, color[0]-15), max(0, color[1]-15), max(0, color[2]-15)))
    
    def _draw_realistic_sleeves(self, draw: ImageDraw.Draw, center_x: int, torso_top: int, props: Dict[str, Any], colors: list, product: Product):
        """Dibuja mangas más realistas."""
        color1, color2 = colors
        sleeve_length = int(props['torso_height'] * 0.6)
        sleeve_width = int(props['scale_factor'] * 12)
        
        # Ajustar según el fit
        fit_multiplier = self._get_fit_multiplier(product.fit)
        sleeve_width = int(sleeve_width * fit_multiplier)
        
        shoulder_w = props['shoulder_width'] // 2
        
        # Manga izquierda con gradiente
        left_sleeve_x = center_x - shoulder_w
        self._draw_single_sleeve(draw, left_sleeve_x - sleeve_width, torso_top + 15, 
                                sleeve_width, sleeve_length, colors, "left")
        
        # Manga derecha con gradiente  
        right_sleeve_x = center_x + shoulder_w
        self._draw_single_sleeve(draw, right_sleeve_x, torso_top + 15,
                                sleeve_width, sleeve_length, colors, "right")
    
    def _draw_single_sleeve(self, draw: ImageDraw.Draw, x: int, y: int, width: int, length: int, colors: list, side: str):
        """Dibuja una manga individual con gradiente."""
        color1, color2 = colors
        
        for i in range(length):
            ratio = i / length
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            
            current_color = (r, g, b)
            current_width = width - int(i * 0.1)  # Manga se estrecha ligeramente
            
            draw.rectangle([x, y + i, x + current_width, y + i + 1], fill=current_color)
        
        # Contorno de la manga
        draw.rectangle([x, y, x + width, y + length], 
                      outline=(max(0, color1[0]-40), max(0, color1[1]-40), max(0, color1[2]-40)), width=2)
    
    def _add_lighting_effects(self, img: Image.Image) -> Image.Image:
        """Añade efectos de iluminación sutil."""
        # Crear una máscara de luz sutil desde arriba-izquierda
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Luz sutil desde arriba
        for y in range(img.height // 3):
            alpha = int(10 * (1 - y / (img.height // 3)))
            for x in range(img.width):
                if alpha > 0:
                    overlay.putpixel((x, y), (255, 255, 255, alpha))
        
        # Combinar con la imagen original
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        return img.convert('RGB')
    
    def _add_enhanced_product_info(self, draw: ImageDraw.Draw, client: Client, product: Product, size: str, color: str):
        """Añade información del producto con mejor tipografía."""
        try:
            # Intentar cargar fuentes mejoradas
            try:
                title_font = ImageFont.truetype("arial.ttf", 14)
                body_font = ImageFont.truetype("arial.ttf", 11)
            except:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
            
            # Información organizada
            info_sections = [
                ("👤 Cliente", client.name),
                ("👕 Producto", f"{product.name} ({product.product_id})"),
                ("📏 Talla", size),
                ("🎨 Color", color.title()),
                ("✂️ Ajuste", product.fit),
                ("🧵 Material", product.fabric)
            ]
            
            # Fondo semitransparente para el texto
            text_bg_height = len(info_sections) * 20 + 20
            text_bg_y = self.canvas_size[1] - text_bg_height - 10
            
            draw.rectangle([
                5, text_bg_y,
                self.canvas_size[0] - 5, self.canvas_size[1] - 5
            ], fill=(255, 255, 255, 200), outline=(200, 200, 200))
            
            # Dibujar información con mejor formato
            y_pos = text_bg_y + 10
            
            for emoji_label, value in info_sections:
                draw.text((10, y_pos), f"{emoji_label}: {value}", 
                         fill=(60, 60, 60), font=body_font)
                y_pos += 18
                
        except Exception as e:
            # Fallback a método simple si hay errores
            self._add_simple_product_info(draw, client, product, size, color)
    
    def _add_simple_product_info(self, draw: ImageDraw.Draw, client: Client, product: Product, size: str, color: str):
        """Método de fallback para información del producto."""
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        info_lines = [
            f"Cliente: {client.name}",
            f"Producto: {product.name}",
            f"Talla: {size}",
            f"Color: {color.title()}",
            f"Ajuste: {product.fit}",
            f"Material: {product.fabric}"
        ]
        
        # Fondo para el texto
        text_height = len(info_lines) * 15 + 10
        draw.rectangle([
            5, self.canvas_size[1] - text_height - 5,
            self.canvas_size[0] - 5, self.canvas_size[1] - 5
        ], fill=(255, 255, 255, 180), outline=(150, 150, 150))
        
        # Dibujar texto
        y_start = self.canvas_size[1] - text_height
        for i, line in enumerate(info_lines):
            y_pos = y_start + i * 15
            draw.text((10, y_pos), line, fill=(50, 50, 50), font=font)
    
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
    
    def create_style_comparison(self, client: Client, product: Product, sizes: list, colors: list) -> Dict[str, Any]:
        """Crea una comparación de estilos con múltiples tallas y colores."""
        if not self.is_available():
            return {"success": False, "error": "PIL no disponible"}
        
        try:
            # Crear canvas más grande para comparación
            comparison_width = len(sizes) * (self.canvas_size[0] + 20)
            comparison_height = len(colors) * (self.canvas_size[1] + 20)
            
            comparison_img = Image.new('RGB', (comparison_width, comparison_height), (250, 250, 250))
            
            for color_idx, color in enumerate(colors):
                for size_idx, size in enumerate(sizes):
                    # Generar imagen individual
                    single_result = self.generate_avatar_image(client, product, size, color)
                    
                    if single_result.get('success'):
                        # Cargar imagen generada
                        img_data = base64.b64decode(single_result['base64'])
                        single_img = Image.open(BytesIO(img_data))
                        
                        # Calcular posición en el grid
                        x_pos = size_idx * (self.canvas_size[0] + 20)
                        y_pos = color_idx * (self.canvas_size[1] + 20)
                        
                        comparison_img.paste(single_img, (x_pos, y_pos))
                        
                        # Añadir etiquetas
                        draw = ImageDraw.Draw(comparison_img)
                        try:
                            font = ImageFont.truetype("arial.ttf", 16)
                        except:
                            font = ImageFont.load_default()
                        
                        label = f"{size} - {color.title()}"
                        draw.text((x_pos + 10, y_pos + 10), label, fill=(0, 0, 0), font=font)
            
            # Guardar imagen de comparación
            timestamp = int(time.time())
            filename = f"comparison_{client.client_id}_{product.product_id}_{timestamp}.png"
            filepath = self.output_dir / filename
            comparison_img.save(filepath, "PNG", quality=95)
            
            # Convertir a base64
            buffer = BytesIO()
            comparison_img.save(buffer, format='PNG', quality=95)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "base64": img_base64,
                "comparison_type": "style_grid"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}