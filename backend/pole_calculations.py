"""
ANSI O5.1-2023 Pole Calculations
Engineering calculations for wood utility poles
"""

import math
from typing import Tuple


def calculate_bending_moment(load_lbs: float, height_ft: float) -> float:
    """
    Calculate bending moment at the base of the pole
    
    Args:
        load_lbs: Horizontal load in pounds
        height_ft: Height at which load is applied in feet
        
    Returns:
        Bending moment in ft-lbs
    """
    return load_lbs * height_ft


def calculate_section_modulus(diameter_inches: float) -> float:
    """
    Calculate section modulus for a circular cross-section
    
    Args:
        diameter_inches: Diameter in inches
        
    Returns:
        Section modulus in cubic inches
    """
    radius = diameter_inches / 2
    return (math.pi * radius**3) / 4


def calculate_fiber_stress(moment_ft_lbs: float, section_modulus_in3: float) -> float:
    """
    Calculate fiber stress at extreme fiber
    
    Args:
        moment_ft_lbs: Bending moment in ft-lbs
        section_modulus_in3: Section modulus in cubic inches
        
    Returns:
        Fiber stress in psi
    """
    moment_in_lbs = moment_ft_lbs * 12  # Convert ft-lbs to in-lbs
    return moment_in_lbs / section_modulus_in3


def calculate_strength_reduction_from_decay(
    original_diameter_inches: float,
    decay_depth_inches: float
) -> Tuple[float, float]:
    """
    Calculate strength reduction due to decay
    
    Args:
        original_diameter_inches: Original pole diameter in inches
        decay_depth_inches: Depth of decay from surface in inches
        
    Returns:
        Tuple of (remaining_strength_ratio, strength_loss_percent)
    """
    remaining_diameter = original_diameter_inches - (2 * decay_depth_inches)
    
    if remaining_diameter <= 0:
        return 0.0, 100.0
    
    # Strength is proportional to section modulus (d^3)
    original_modulus = calculate_section_modulus(original_diameter_inches)
    remaining_modulus = calculate_section_modulus(remaining_diameter)
    
    strength_ratio = remaining_modulus / original_modulus
    strength_loss_pct = (1 - strength_ratio) * 100
    
    return strength_ratio, strength_loss_pct


def calculate_embedment_depth(pole_length_ft: float, soil_class: str = "normal") -> float:
    """
    Calculate recommended embedment depth
    
    Args:
        pole_length_ft: Total pole length in feet
        soil_class: Soil classification ("firm", "normal", "soft")
        
    Returns:
        Recommended embedment depth in feet
    """
    # Base formula: 10% of length + 2 feet
    base_depth = (pole_length_ft * 0.10) + 2
    
    # Adjust for soil conditions
    soil_factors = {
        "firm": 0.9,
        "normal": 1.0,
        "soft": 1.2
    }
    
    factor = soil_factors.get(soil_class.lower(), 1.0)
    return base_depth * factor


def calculate_wind_load(
    wind_speed_mph: float,
    projected_area_sq_ft: float,
    drag_coefficient: float = 1.0
) -> float:
    """
    Calculate wind load on pole and attachments
    
    Args:
        wind_speed_mph: Wind speed in miles per hour
        projected_area_sq_ft: Projected area in square feet
        drag_coefficient: Drag coefficient (default 1.0 for cylinders)
        
    Returns:
        Wind load in pounds
    """
    # Wind pressure formula: P = 0.00256 * V^2 * Cd
    # where V is in mph and P is in psf
    wind_pressure_psf = 0.00256 * (wind_speed_mph ** 2) * drag_coefficient
    
    return wind_pressure_psf * projected_area_sq_ft


def calculate_ice_load(
    ice_thickness_inches: float,
    conductor_diameter_inches: float,
    span_length_ft: float,
    ice_density_pcf: float = 57.0
) -> float:
    """
    Calculate ice load on conductors
    
    Args:
        ice_thickness_inches: Radial ice thickness in inches
        conductor_diameter_inches: Conductor diameter in inches
        span_length_ft: Span length in feet
        ice_density_pcf: Ice density in pounds per cubic foot (default 57 pcf)
        
    Returns:
        Ice load in pounds
    """
    # Calculate ice-covered diameter
    ice_diameter = conductor_diameter_inches + (2 * ice_thickness_inches)
    
    # Calculate cross-sectional area of ice (annulus)
    conductor_area = math.pi * (conductor_diameter_inches / 2) ** 2
    ice_covered_area = math.pi * (ice_diameter / 2) ** 2
    ice_area = ice_covered_area - conductor_area
    
    # Convert to square feet
    ice_area_sq_ft = ice_area / 144
    
    # Calculate volume and weight
    volume_cu_ft = ice_area_sq_ft * span_length_ft
    weight_lbs = volume_cu_ft * ice_density_pcf
    
    return weight_lbs


def calculate_combined_wind_ice_load(
    wind_speed_mph: float,
    ice_thickness_inches: float,
    conductor_diameter_inches: float,
    span_length_ft: float,
    number_of_conductors: int = 3
) -> Tuple[float, float, float]:
    """
    Calculate combined wind and ice loads
    
    Args:
        wind_speed_mph: Wind speed in miles per hour
        ice_thickness_inches: Radial ice thickness in inches
        conductor_diameter_inches: Conductor diameter in inches
        span_length_ft: Span length in feet
        number_of_conductors: Number of conductors
        
    Returns:
        Tuple of (ice_load_lbs, wind_load_lbs, total_load_lbs)
    """
    # Calculate ice load per conductor
    ice_load_per_conductor = calculate_ice_load(
        ice_thickness_inches,
        conductor_diameter_inches,
        span_length_ft
    )
    total_ice_load = ice_load_per_conductor * number_of_conductors
    
    # Calculate wind load on ice-covered conductors
    ice_diameter = conductor_diameter_inches + (2 * ice_thickness_inches)
    projected_area = (ice_diameter / 12) * span_length_ft * number_of_conductors
    wind_load = calculate_wind_load(wind_speed_mph, projected_area, drag_coefficient=1.0)
    
    # Total horizontal load (wind + weight component)
    total_load = wind_load + (total_ice_load * 0.1)  # 10% of ice weight as horizontal component
    
    return total_ice_load, wind_load, total_load


def calculate_pole_deflection(
    load_lbs: float,
    height_ft: float,
    pole_diameter_inches: float,
    modulus_of_elasticity_psi: float = 1_600_000
) -> float:
    """
    Calculate pole deflection at load point
    
    Args:
        load_lbs: Horizontal load in pounds
        height_ft: Height at which load is applied in feet
        pole_diameter_inches: Pole diameter at groundline in inches
        modulus_of_elasticity_psi: Modulus of elasticity (default 1.6M psi for wood)
        
    Returns:
        Deflection in inches
    """
    # Convert height to inches
    height_inches = height_ft * 12
    
    # Calculate moment of inertia
    radius = pole_diameter_inches / 2
    moment_of_inertia = (math.pi * radius**4) / 4
    
    # Deflection formula for cantilever beam with point load
    # δ = (P * L^3) / (3 * E * I)
    deflection = (load_lbs * height_inches**3) / (3 * modulus_of_elasticity_psi * moment_of_inertia)
    
    return deflection


def check_pole_adequacy(
    applied_load_lbs: float,
    pole_capacity_lbs: float,
    safety_factor: float = 1.5
) -> Tuple[bool, float, str]:
    """
    Check if pole is adequate for applied load
    
    Args:
        applied_load_lbs: Applied load in pounds
        pole_capacity_lbs: Pole rated capacity in pounds
        safety_factor: Required safety factor
        
    Returns:
        Tuple of (is_adequate, utilization_ratio, status_message)
    """
    design_load = applied_load_lbs * safety_factor
    utilization = design_load / pole_capacity_lbs
    
    if utilization <= 1.0:
        status = f"✓ ADEQUATE - Utilization: {utilization*100:.1f}%"
        is_adequate = True
    elif utilization <= 1.1:
        status = f"⚠️ MARGINAL - Utilization: {utilization*100:.1f}% (slightly over capacity)"
        is_adequate = False
    else:
        status = f"✗ INADEQUATE - Utilization: {utilization*100:.1f}% (significantly over capacity)"
        is_adequate = False
    
    return is_adequate, utilization, status


# Made with Bob