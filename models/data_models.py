from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum


class FitType(Enum):
    """Tipos de ajuste de prenda."""
    SLIM = "Slim"
    REGULAR = "Regular"
    LOOSE = "Loose"
    TAILORED = "Tailored"
    OVERSIZED = "Oversized"


class Size(Enum):
    """Tallas disponibles."""
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


@dataclass
class BodyMeasurements:
    """Medidas corporales del cliente."""
    bust_cm: float
    waist_cm: float
    hips_cm: float


@dataclass
class SizeChart:
    """Tabla de tallas para un producto."""
    XS: BodyMeasurements
    S: BodyMeasurements
    M: BodyMeasurements
    L: BodyMeasurements
    XL: BodyMeasurements

    def get_size_measurements(self, size: str) -> BodyMeasurements:
        """Obtener medidas para una talla específica."""
        return getattr(self, size)

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        """Transformar en un diccionario"""
        return {
            size: {
                "bust_cm": getattr(self, size).bust_cm,
                "waist_cm": getattr(self, size).waist_cm,
                "hips_cm": getattr(self, size).hips_cm
            }
            for size in ["XS", "S", "M", "L", "XL"]
        }


@dataclass
class PurchaseHistory:
    """Historial de compra de un cliente."""
    product_id: str
    size_purchased: str
    fit_feedback: str


@dataclass
class ModelReference:
    """Información del modelo que lleva la prenda."""
    height_cm: int
    wearing_size: str


@dataclass
class Product:
    """Información de un producto."""
    product_id: str
    name: str
    available_sizes: List[str]
    size_chart: SizeChart
    fit: str
    fabric: str
    model_reference: ModelReference

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Crea un Product desde un diccionario."""
        size_chart_data = data["size_chart"]
        size_chart = SizeChart(
            XS=BodyMeasurements(**size_chart_data["XS"]),
            S=BodyMeasurements(**size_chart_data["S"]),
            M=BodyMeasurements(**size_chart_data["M"]),
            L=BodyMeasurements(**size_chart_data["L"]),
            XL=BodyMeasurements(**size_chart_data["XL"])
        )
        
        model_ref = ModelReference(**data["model_reference"])
        
        return cls(
            product_id=data["product_id"],
            name=data["name"],
            available_sizes=data["available_sizes"],
            size_chart=size_chart,
            fit=data["fit"],
            fabric=data["fabric"],
            model_reference=model_ref
        )


@dataclass
class Client:
    """Información de un cliente."""
    client_id: str
    name: str
    age: int
    height_cm: int
    weight_kg: float
    body_measurements: BodyMeasurements
    preferred_fit: str
    purchase_history: List[PurchaseHistory]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """Crea un Client desde un diccionario."""
        body_measurements = BodyMeasurements(**data["body_measurements"])
        purchase_history = [
            PurchaseHistory(**purchase) for purchase in data["purchase_history"]
        ]
        
        return cls(
            client_id=data["client_id"],
            name=data["name"],
            age=data["age"],
            height_cm=data["height_cm"],
            weight_kg=data["weight_kg"],
            body_measurements=body_measurements,
            preferred_fit=data["preferred_fit"],
            purchase_history=purchase_history
        )


@dataclass
class SizeRecommendation:
    """Recomendación de talla."""
    recommended_size: str
    confidence: float
    reasoning: str
    alternative_sizes: List[str]
    fit_notes: str