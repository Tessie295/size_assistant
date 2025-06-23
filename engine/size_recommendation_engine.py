import numpy as np
from typing import Dict, List, Tuple, Optional
from models.data_models import Client, Product, SizeRecommendation, BodyMeasurements


class SizeRecommendationEngine:
    """Motor de recomendación de tallas."""
    
    def __init__(self):
        """Inicialización del motor de recomendación."""
        self.size_order = ["XS", "S", "M", "L", "XL"]
        self.size_to_index = {size: i for i, size in enumerate(self.size_order)}
    
    def recommend_size(self, client: Client, product: Product) -> SizeRecommendation:
        """
        Recomendar una talla para un cliente y producto específicos.
        
        Args:
            client: Cliente para quien recomendar
            product: Producto a recomendar
            
        Returns:
            Recomendación de talla con su justificación
        """
        # 1. Análisis de medidas corporales vs tabla de tallas
        size_fit_scores = self._calculate_size_fit_scores(client, product)
        
        # 2. Análisis del historial de compras
        history_adjustment = self._analyze_purchase_history(client, product)
        
        # 3. Consideración de preferencias de ajuste
        fit_adjustment = self._calculate_fit_preference_adjustment(client, product)
        
        # 4. Combinar todos los factores
        final_scores = self._combine_scores(
            size_fit_scores, 
            history_adjustment, 
            fit_adjustment
        )
        
        # 5. Seleccionar mejor talla y alternativas
        recommended_size = max(final_scores.keys(), key=lambda x: final_scores[x])
        confidence = final_scores[recommended_size]
        
        # Obtener tallas alternativas
        sorted_sizes = sorted(
            final_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        alternative_sizes = [size for size, _ in sorted_sizes[1:3]]
        
        # Construir el razonamiento
        reasoning = self._generate_reasoning(
            client, product, recommended_size, size_fit_scores, 
            history_adjustment, fit_adjustment
        )
        
        # Generar notas sobre el ajuste
        fit_notes = self._generate_fit_notes(client, product, recommended_size)
        
        return SizeRecommendation(
            recommended_size=recommended_size,
            confidence=confidence,
            reasoning=reasoning,
            alternative_sizes=alternative_sizes,
            fit_notes=fit_notes
        )
    
    def _calculate_size_fit_scores(self, client: Client, product: Product) -> Dict[str, float]:
        """Calcula en base a las medidas del cliente como se ajusta cada talla."""
        scores = {}
        client_measurements = client.body_measurements
        
        for size in self.size_order:
            if size not in product.available_sizes:
                scores[size] = 0.0
                continue
                
            size_measurements = product.size_chart.get_size_measurements(size)
            
            # Calcular diferencias normalizadas
            bust_diff = abs(client_measurements.bust_cm - size_measurements.bust_cm)
            waist_diff = abs(client_measurements.waist_cm - size_measurements.waist_cm)
            hips_diff = abs(client_measurements.hips_cm - size_measurements.hips_cm)
            
            # Pesos para cada medida (importancia interpretada al aire)
            bust_weight = 0.4
            waist_weight = 0.35
            hips_weight = 0.25
            
            # Convertir diferencias a scores (menor diferencia = mayor score)
            # Usar función exponencial decreciente
            bust_score = np.exp(-bust_diff / 10)
            waist_score = np.exp(-waist_diff / 8)
            hips_score = np.exp(-hips_diff / 10)
            
            # Score ponderado
            total_score = (
                bust_score * bust_weight +
                waist_score * waist_weight +
                hips_score * hips_weight
            )
            
            scores[size] = total_score
        
        return scores
    
    def _analyze_purchase_history(self, client: Client, product: Product) -> Dict[str, float]:
        """Analiza el historial de compras para ajustar recomendaciones."""
        adjustments = {size: 0.0 for size in self.size_order}
        
        if not client.purchase_history:
            return adjustments
        
        # Analizar patrones en el historial
        size_feedback_patterns = {}
        
        for purchase in client.purchase_history:
            size = purchase.size_purchased
            feedback = purchase.fit_feedback.lower()
            
            if size not in size_feedback_patterns:
                size_feedback_patterns[size] = []
            size_feedback_patterns[size].append(feedback)
        
        # Aplicar ajustes basados en feedback
        for size, feedbacks in size_feedback_patterns.items():
            if size not in self.size_to_index:
                continue
                
            size_index = self.size_to_index[size]
            
            for feedback in feedbacks:
                adjustment_value = 0.1
                
                if "too tight" in feedback:
                    # Si compró talla X y le quedó ajustada, 
                    # subir probabilidad de tallas más grandes
                    for i, target_size in enumerate(self.size_order):
                        if i > size_index:
                            adjustments[target_size] += adjustment_value
                        elif i < size_index:
                            adjustments[target_size] -= adjustment_value
                
                elif "too loose" in feedback:
                    # Si compró talla X y le quedó grande,
                    # subir probabilidad de tallas más pequeñas
                    for i, target_size in enumerate(self.size_order):
                        if i < size_index:
                            adjustments[target_size] += adjustment_value
                        elif i > size_index:
                            adjustments[target_size] -= adjustment_value
                
                elif "perfect" in feedback or "comfortable" in feedback:
                    # Si le quedó bien, reforzar tallas similares
                    adjustments[size] += adjustment_value * 2
                    # Y un poco las adyacentes
                    if size_index > 0:
                        adjustments[self.size_order[size_index - 1]] += adjustment_value * 0.5
                    if size_index < len(self.size_order) - 1:
                        adjustments[self.size_order[size_index + 1]] += adjustment_value * 0.5
        
        return adjustments
    
    def _calculate_fit_preference_adjustment(self, client: Client, product: Product) -> Dict[str, float]:
        """Calcula ajustes basados en preferencias de ajuste del cliente y tipo de prenda."""
        adjustments = {size: 0.0 for size in self.size_order}
        
        client_pref = client.preferred_fit.lower()
        product_fit = product.fit.lower()
        
        # Matriz de compatibilidad entre preferencias del cliente y tipo de prenda
        # (Recomendaciones dadas por la IA)
        compatibility_matrix = {
            ("slim", "slim"): 0.2,
            ("slim", "tailored"): 0.1,
            ("slim", "regular"): -0.05,
            ("slim", "oversized"): -0.15,
            ("regular", "slim"): -0.05,
            ("regular", "tailored"): 0.1,
            ("regular", "regular"): 0.2,
            ("regular", "oversized"): 0.05,
            ("loose", "slim"): -0.15,
            ("loose", "tailored"): -0.1,
            ("loose", "regular"): 0.05,
            ("loose", "oversized"): 0.2,
        }
        
        base_adjustment = compatibility_matrix.get((client_pref, product_fit), 0.0)
        
        # Aplicar ajuste base a todas las tallas
        for size in adjustments:
            adjustments[size] = base_adjustment
        
        # Ajustes específicos según preferencia del cliente
        if client_pref == "slim":
            # Preferir tallas más ajustadas
            adjustments["XS"] += 0.1
            adjustments["S"] += 0.05
            adjustments["L"] -= 0.05
            adjustments["XL"] -= 0.1
        elif client_pref == "loose":
            # Preferir tallas más holgadas
            adjustments["XS"] -= 0.1
            adjustments["S"] -= 0.05
            adjustments["L"] += 0.05
            adjustments["XL"] += 0.1
        
        return adjustments
    
    def _combine_scores(
        self, 
        size_scores: Dict[str, float], 
        history_adj: Dict[str, float], 
        fit_adj: Dict[str, float]
    ) -> Dict[str, float]:
        """Combina todos los scores y ajustes en un score final."""
        final_scores = {}
        
        for size in self.size_order:
            # Score base de medidas (peso más alto)
            base_score = size_scores.get(size, 0.0) * 0.6
            
            # Ajustes del historial (peso medio)
            history_score = history_adj.get(size, 0.0) * 0.25
            
            # Ajustes de preferencia de fit (peso menor)
            fit_score = fit_adj.get(size, 0.0) * 0.15
            
            final_scores[size] = max(0.0, base_score + history_score + fit_score)
        
        return final_scores
    
    def _generate_reasoning(
        self, 
        client: Client, 
        product: Product, 
        recommended_size: str,
        size_scores: Dict[str, float],
        history_adj: Dict[str, float],
        fit_adj: Dict[str, float]
    ) -> str:
        """Genera una explicación textual de por qué se recomienda esta talla."""
        reasoning_parts = []
        
        # Análisis de medidas
        client_measurements = client.body_measurements
        product_measurements = product.size_chart.get_size_measurements(recommended_size)
        
        reasoning_parts.append(
            f"Basándome en tus medidas (busto: {client_measurements.bust_cm}cm, "
            f"cintura: {client_measurements.waist_cm}cm, cadera: {client_measurements.hips_cm}cm), "
            f"la talla {recommended_size} del {product.name} se ajusta mejor a tu cuerpo."
        )
        
        # Análisis del historial
        if client.purchase_history:
            positive_feedback = sum(1 for p in client.purchase_history 
                                  if "perfect" in p.fit_feedback.lower() or "comfortable" in p.fit_feedback.lower())
            if positive_feedback > 0:
                reasoning_parts.append(
                    f"Tu historial muestra que has tenido experiencias positivas con tallas similares."
                )
        
        # Análisis de preferencias
        if client.preferred_fit.lower() == product.fit.lower():
            reasoning_parts.append(
                f"Esta prenda tiene un ajuste {product.fit.lower()}, que coincide con tu preferencia."
            )
        elif client.preferred_fit.lower() == "slim" and product.fit.lower() in ["oversized", "loose"]:
            reasoning_parts.append(
                f"Dado que prefieres un ajuste slim y esta prenda es {product.fit.lower()}, "
                f"podrías considerar una talla más pequeña si buscas un fit más ajustado."
            )
        
        return " ".join(reasoning_parts)
    
    def _generate_fit_notes(self, client: Client, product: Product, recommended_size: str) -> str:
        """Genera notas adicionales sobre el ajuste esperado."""
        notes = []
        
        # Información sobre el modelo de referencia
        model_ref = product.model_reference
        height_diff = client.height_cm - model_ref.height_cm
        
        if abs(height_diff) > 10:
            if height_diff > 0:
                notes.append(f"Eres {height_diff}cm más alta que el modelo de referencia, "
                           f"por lo que la prenda podría quedarte algo más corta.")
            else:
                notes.append(f"Eres {abs(height_diff)}cm más baja que el modelo de referencia, "
                           f"por lo que la prenda podría quedarte algo más larga.")
        
        # Información sobre el tejido
        fabric_notes = {
            "cotton": "El algodón puede encogerse ligeramente tras los primeros lavados.",
            "wool": "La lana puede tener algo de elasticidad y adaptarse mejor al cuerpo.",
            "polyester": "El poliéster mantiene su forma y talla de manera consistente.",
            "linen": "El lino puede ser menos elástico, considera el ajuste cuidadosamente.",
            "blend": "Esta mezcla de tejidos suele ofrecer un buen balance entre comodidad y durabilidad."
        }
        
        fabric_note = fabric_notes.get(product.fabric.lower())
        if fabric_note:
            notes.append(fabric_note)
        
        return " ".join(notes) if notes else "No hay notas adicionales sobre el ajuste."