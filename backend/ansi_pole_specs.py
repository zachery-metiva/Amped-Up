"""
ANSI O5.1-2023 Wood Poles Specifications and Dimensions
This module contains the standard specifications for wood utility poles
according to ANSI O5.1-2023 standards.
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class PoleClass(Enum):
    """ANSI O5.1-2023 Pole Classes"""
    H6 = "H6"
    H5 = "H5"
    H4 = "H4"
    H3 = "H3"
    H2 = "H2"
    H1 = "H1"
    CLASS_1 = "1"
    CLASS_2 = "2"
    CLASS_3 = "3"
    CLASS_4 = "4"
    CLASS_5 = "5"
    CLASS_6 = "6"
    CLASS_7 = "7"
    CLASS_10 = "10"


class WoodSpecies(Enum):
    """Common wood species for utility poles"""
    SOUTHERN_PINE = "Southern Pine"
    DOUGLAS_FIR = "Douglas Fir"
    WESTERN_RED_CEDAR = "Western Red Cedar"
    NORTHERN_WHITE_CEDAR = "Northern White Cedar"
    JACK_PINE = "Jack Pine"
    LODGEPOLE_PINE = "Lodgepole Pine"
    PONDEROSA_PINE = "Ponderosa Pine"
    RED_PINE = "Red Pine"


class TreatmentType(Enum):
    """Pole treatment types"""
    CREOSOTE = "Creosote"
    PENTACHLOROPHENOL = "Pentachlorophenol"
    CCA = "Chromated Copper Arsenate"
    ACZA = "Ammoniacal Copper Zinc Arsenate"
    UNTREATED = "Untreated"


@dataclass
class PoleSpecification:
    """ANSI O5.1-2023 Pole Specification"""
    pole_class: str
    length_ft: float
    min_circumference_top_inches: float
    min_circumference_6ft_from_butt_inches: float
    horizontal_load_lbs: float
    fiber_stress_psi: int = 8000  # Default fiber stress for most species
    
    def get_top_diameter_inches(self) -> float:
        """Calculate top diameter from circumference"""
        return self.min_circumference_top_inches / 3.14159
    
    def get_groundline_diameter_inches(self) -> float:
        """Calculate groundline diameter from circumference"""
        return self.min_circumference_6ft_from_butt_inches / 3.14159


# ANSI O5.1-2023 Standard Specifications
# Horizontal load at 2 feet from top, fiber stress 8000 psi
ANSI_POLE_SPECIFICATIONS: Dict[str, Dict[float, PoleSpecification]] = {
    "H6": {
        20: PoleSpecification("H6", 20, 15.0, 27.0, 11700),
        25: PoleSpecification("H6", 25, 15.0, 27.0, 10200),
        30: PoleSpecification("H6", 30, 15.0, 27.0, 8900),
        35: PoleSpecification("H6", 35, 15.0, 27.0, 7900),
        40: PoleSpecification("H6", 40, 15.0, 27.0, 7100),
        45: PoleSpecification("H6", 45, 15.0, 27.0, 6400),
        50: PoleSpecification("H6", 50, 15.0, 27.0, 5900),
    },
    "H5": {
        20: PoleSpecification("H5", 20, 15.0, 28.5, 13900),
        25: PoleSpecification("H5", 25, 15.0, 28.5, 12100),
        30: PoleSpecification("H5", 30, 15.0, 28.5, 10600),
        35: PoleSpecification("H5", 35, 15.0, 28.5, 9400),
        40: PoleSpecification("H5", 40, 15.0, 28.5, 8500),
        45: PoleSpecification("H5", 45, 15.0, 28.5, 7700),
        50: PoleSpecification("H5", 50, 15.0, 28.5, 7000),
    },
    "H4": {
        20: PoleSpecification("H4", 20, 15.0, 30.0, 16100),
        25: PoleSpecification("H4", 25, 15.0, 30.0, 14000),
        30: PoleSpecification("H4", 30, 15.0, 30.0, 12300),
        35: PoleSpecification("H4", 35, 15.0, 30.0, 10900),
        40: PoleSpecification("H4", 40, 15.0, 30.0, 9800),
        45: PoleSpecification("H4", 45, 15.0, 30.0, 8900),
        50: PoleSpecification("H4", 50, 15.0, 30.0, 8100),
    },
    "H3": {
        20: PoleSpecification("H3", 20, 15.0, 31.5, 18400),
        25: PoleSpecification("H3", 25, 15.0, 31.5, 16000),
        30: PoleSpecification("H3", 30, 15.0, 31.5, 14000),
        35: PoleSpecification("H3", 35, 15.0, 31.5, 12500),
        40: PoleSpecification("H3", 40, 15.0, 31.5, 11200),
        45: PoleSpecification("H3", 45, 15.0, 31.5, 10200),
        50: PoleSpecification("H3", 50, 15.0, 31.5, 9300),
        55: PoleSpecification("H3", 55, 15.0, 31.5, 8500),
        60: PoleSpecification("H3", 60, 15.0, 31.5, 7800),
    },
    "H2": {
        20: PoleSpecification("H2", 20, 15.0, 33.0, 20700),
        25: PoleSpecification("H2", 25, 15.0, 33.0, 18000),
        30: PoleSpecification("H2", 30, 15.0, 33.0, 15800),
        35: PoleSpecification("H2", 35, 15.0, 33.0, 14000),
        40: PoleSpecification("H2", 40, 15.0, 33.0, 12600),
        45: PoleSpecification("H2", 45, 15.0, 33.0, 11500),
        50: PoleSpecification("H2", 50, 15.0, 33.0, 10500),
        55: PoleSpecification("H2", 55, 15.0, 33.0, 9600),
        60: PoleSpecification("H2", 60, 15.0, 33.0, 8800),
        65: PoleSpecification("H2", 65, 15.0, 33.0, 8100),
        70: PoleSpecification("H2", 70, 15.0, 33.0, 7500),
    },
    "H1": {
        20: PoleSpecification("H1", 20, 15.0, 34.5, 23000),
        25: PoleSpecification("H1", 25, 15.0, 34.5, 20000),
        30: PoleSpecification("H1", 30, 15.0, 34.5, 17500),
        35: PoleSpecification("H1", 35, 15.0, 34.5, 15600),
        40: PoleSpecification("H1", 40, 15.0, 34.5, 14000),
        45: PoleSpecification("H1", 45, 15.0, 34.5, 12700),
        50: PoleSpecification("H1", 50, 15.0, 34.5, 11600),
        55: PoleSpecification("H1", 55, 15.0, 34.5, 10700),
        60: PoleSpecification("H1", 60, 15.0, 34.5, 9800),
        65: PoleSpecification("H1", 65, 15.0, 34.5, 9000),
        70: PoleSpecification("H1", 70, 15.0, 34.5, 8300),
        75: PoleSpecification("H1", 75, 15.0, 34.5, 7700),
        80: PoleSpecification("H1", 80, 15.0, 34.5, 7200),
    },
    "1": {
        20: PoleSpecification("1", 20, 27.0, 43.5, 54500),
        25: PoleSpecification("1", 25, 27.0, 43.5, 47400),
        30: PoleSpecification("1", 30, 27.0, 43.5, 41500),
        35: PoleSpecification("1", 35, 27.0, 43.5, 36900),
        40: PoleSpecification("1", 40, 27.0, 43.5, 33200),
        45: PoleSpecification("1", 45, 27.0, 43.5, 30200),
        50: PoleSpecification("1", 50, 27.0, 43.5, 27500),
        55: PoleSpecification("1", 55, 27.0, 43.5, 25300),
        60: PoleSpecification("1", 60, 27.0, 43.5, 23200),
    },
    "2": {
        20: PoleSpecification("2", 20, 25.0, 39.5, 43900),
        25: PoleSpecification("2", 25, 25.0, 39.5, 38200),
        30: PoleSpecification("2", 30, 25.0, 39.5, 33400),
        35: PoleSpecification("2", 35, 25.0, 39.5, 29700),
        40: PoleSpecification("2", 40, 25.0, 39.5, 26700),
        45: PoleSpecification("2", 45, 25.0, 39.5, 24300),
        50: PoleSpecification("2", 50, 25.0, 39.5, 22200),
        55: PoleSpecification("2", 55, 25.0, 39.5, 20400),
        60: PoleSpecification("2", 60, 25.0, 39.5, 18700),
    },
    "3": {
        20: PoleSpecification("3", 20, 23.0, 36.0, 35000),
        25: PoleSpecification("3", 25, 23.0, 36.0, 30500),
        30: PoleSpecification("3", 30, 23.0, 36.0, 26700),
        35: PoleSpecification("3", 35, 23.0, 36.0, 23700),
        40: PoleSpecification("3", 40, 23.0, 36.0, 21300),
        45: PoleSpecification("3", 45, 23.0, 36.0, 19400),
        50: PoleSpecification("3", 50, 23.0, 36.0, 17700),
        55: PoleSpecification("3", 55, 23.0, 36.0, 16300),
        60: PoleSpecification("3", 60, 23.0, 36.0, 14900),
    },
    "4": {
        20: PoleSpecification("4", 20, 21.0, 33.0, 27600),
        25: PoleSpecification("4", 25, 21.0, 33.0, 24000),
        30: PoleSpecification("4", 30, 21.0, 33.0, 21000),
        35: PoleSpecification("4", 35, 21.0, 33.0, 18700),
        40: PoleSpecification("4", 40, 21.0, 33.0, 16800),
        45: PoleSpecification("4", 45, 21.0, 33.0, 15300),
        50: PoleSpecification("4", 50, 21.0, 33.0, 14000),
        55: PoleSpecification("4", 55, 21.0, 33.0, 12800),
        60: PoleSpecification("4", 60, 21.0, 33.0, 11800),
    },
    "5": {
        20: PoleSpecification("5", 20, 19.0, 30.0, 21100),
        25: PoleSpecification("5", 25, 19.0, 30.0, 18400),
        30: PoleSpecification("5", 30, 19.0, 30.0, 16100),
        35: PoleSpecification("5", 35, 19.0, 30.0, 14300),
        40: PoleSpecification("5", 40, 19.0, 30.0, 12900),
        45: PoleSpecification("5", 45, 19.0, 30.0, 11700),
        50: PoleSpecification("5", 50, 19.0, 30.0, 10700),
        55: PoleSpecification("5", 55, 19.0, 30.0, 9800),
        60: PoleSpecification("5", 60, 19.0, 30.0, 9000),
    },
    "6": {
        20: PoleSpecification("6", 20, 17.0, 27.0, 15400),
        25: PoleSpecification("6", 25, 17.0, 27.0, 13400),
        30: PoleSpecification("6", 30, 17.0, 27.0, 11700),
        35: PoleSpecification("6", 35, 17.0, 27.0, 10400),
        40: PoleSpecification("6", 40, 17.0, 27.0, 9400),
        45: PoleSpecification("6", 45, 17.0, 27.0, 8500),
        50: PoleSpecification("6", 50, 17.0, 27.0, 7800),
        55: PoleSpecification("6", 55, 17.0, 27.0, 7200),
        60: PoleSpecification("6", 60, 17.0, 27.0, 6600),
    },
    "7": {
        20: PoleSpecification("7", 20, 15.0, 24.5, 11000),
        25: PoleSpecification("7", 25, 15.0, 24.5, 9600),
        30: PoleSpecification("7", 30, 15.0, 24.5, 8400),
        35: PoleSpecification("7", 35, 15.0, 24.5, 7500),
        40: PoleSpecification("7", 40, 15.0, 24.5, 6700),
        45: PoleSpecification("7", 45, 15.0, 24.5, 6100),
        50: PoleSpecification("7", 50, 15.0, 24.5, 5600),
    },
}


def get_pole_specification(pole_class: str, length_ft: float) -> Optional[PoleSpecification]:
    """
    Get ANSI O5.1-2023 pole specification for given class and length
    
    Args:
        pole_class: Pole class (e.g., "H1", "1", "2", etc.)
        length_ft: Pole length in feet
        
    Returns:
        PoleSpecification if found, None otherwise
    """
    if pole_class in ANSI_POLE_SPECIFICATIONS:
        return ANSI_POLE_SPECIFICATIONS[pole_class].get(length_ft)
    return None


def get_available_lengths(pole_class: str) -> List[float]:
    """
    Get available lengths for a given pole class
    
    Args:
        pole_class: Pole class (e.g., "H1", "1", "2", etc.)
        
    Returns:
        List of available lengths in feet
    """
    if pole_class in ANSI_POLE_SPECIFICATIONS:
        return sorted(ANSI_POLE_SPECIFICATIONS[pole_class].keys())
    return []


def get_all_pole_classes() -> List[str]:
    """Get all available pole classes"""
    return list(ANSI_POLE_SPECIFICATIONS.keys())

# Made with Bob
