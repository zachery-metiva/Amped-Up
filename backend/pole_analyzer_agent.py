"""
Pole Analyzer Agent - ANSI O5.1-2023 Compliance Analysis
Analyzes utility poles for compliance with ANSI O5.1-2023 standards
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.ansi_pole_specs import (
    get_pole_specification,
    get_available_lengths,
    get_all_pole_classes,
    PoleSpecification,
    ANSI_POLE_SPECIFICATIONS
)
from backend.pole_calculations import (
    calculate_bending_moment,
    calculate_fiber_stress,
    calculate_section_modulus,
    calculate_strength_reduction_from_decay,
    check_pole_adequacy
)


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    MARGINAL = "marginal"
    UNKNOWN = "unknown"


@dataclass
class PoleAnalysis:
    """Results of pole analysis"""
    pole_class: str
    length_ft: float
    compliance_status: ComplianceStatus
    issues: List[str]
    recommendations: List[str]
    capacity_utilization: float
    safety_margin: float
    details: Dict


class PoleAnalyzerAgent:
    """
    Pole Analyzer Agent for ANSI O5.1-2023 compliance checking
    
    Analyzes utility poles against ANSI O5.1-2023 standards and provides
    detailed compliance reports and recommendations.
    """
    
    def __init__(self, safety_factor: float = 1.5):
        """
        Initialize the analyzer
        
        Args:
            safety_factor: Safety factor for load calculations (default 1.5)
        """
        self.safety_factor = safety_factor
    
    def analyze_pole(
        self,
        pole_class: str,
        length_ft: float,
        applied_load_lbs: float,
        measured_top_circumference: Optional[float] = None,
        measured_groundline_circumference: Optional[float] = None,
        decay_depth_inches: Optional[float] = None
    ) -> PoleAnalysis:
        """
        Analyze a pole for ANSI O5.1-2023 compliance
        
        Args:
            pole_class: Pole class (e.g., "H1", "1", etc.)
            length_ft: Pole length in feet
            applied_load_lbs: Applied horizontal load in pounds
            measured_top_circumference: Measured top circumference in inches
            measured_groundline_circumference: Measured groundline circumference in inches
            decay_depth_inches: Depth of decay at groundline in inches
            
        Returns:
            PoleAnalysis with compliance status and recommendations
        """
        spec = get_pole_specification(pole_class, length_ft)
        
        if not spec:
            return PoleAnalysis(
                pole_class=pole_class,
                length_ft=length_ft,
                compliance_status=ComplianceStatus.UNKNOWN,
                issues=[f"No specification found for {pole_class} at {length_ft}ft"],
                recommendations=["Verify pole class and length"],
                capacity_utilization=0.0,
                safety_margin=0.0,
                details={}
            )
        
        issues = []
        recommendations = []
        
        # Check dimensional compliance
        if measured_top_circumference is not None:
            if measured_top_circumference < spec.min_circumference_top_inches:
                issues.append(
                    f"Top circumference {measured_top_circumference}\" is below minimum "
                    f"{spec.min_circumference_top_inches}\""
                )
                recommendations.append("Pole may need replacement due to undersized top")
        
        if measured_groundline_circumference is not None:
            if measured_groundline_circumference < spec.min_circumference_6ft_from_butt_inches:
                issues.append(
                    f"Groundline circumference {measured_groundline_circumference}\" is below minimum "
                    f"{spec.min_circumference_6ft_from_butt_inches}\""
                )
                recommendations.append("Pole may need replacement due to undersized groundline")
        
        # Check for decay effects
        effective_capacity = spec.horizontal_load_lbs
        if decay_depth_inches is not None and decay_depth_inches > 0:
            groundline_diameter = spec.get_groundline_diameter_inches()
            strength_ratio, loss_pct = calculate_strength_reduction_from_decay(
                groundline_diameter,
                decay_depth_inches
            )
            effective_capacity = spec.horizontal_load_lbs * strength_ratio
            
            if loss_pct > 30:
                issues.append(f"Critical decay: {loss_pct:.1f}% strength loss")
                recommendations.append("URGENT: Pole replacement required")
            elif loss_pct > 15:
                issues.append(f"Significant decay: {loss_pct:.1f}% strength loss")
                recommendations.append("Schedule pole replacement within 1 year")
            elif loss_pct > 5:
                issues.append(f"Moderate decay: {loss_pct:.1f}% strength loss")
                recommendations.append("Monitor decay progression, consider treatment")
        
        # Check load capacity
        is_adequate, utilization, status = check_pole_adequacy(
            applied_load_lbs,
            effective_capacity,
            self.safety_factor
        )
        
        if not is_adequate:
            issues.append(f"Load capacity exceeded: {status}")
            recommendations.append("Consider pole reinforcement or replacement")
        
        # Determine overall compliance status
        if not issues:
            compliance_status = ComplianceStatus.COMPLIANT
        elif utilization > 1.1 or any("Critical" in issue or "URGENT" in rec 
                                       for issue in issues 
                                       for rec in recommendations):
            compliance_status = ComplianceStatus.NON_COMPLIANT
        else:
            compliance_status = ComplianceStatus.MARGINAL
        
        # Calculate safety margin
        design_load = applied_load_lbs * self.safety_factor
        safety_margin = effective_capacity - design_load
        
        return PoleAnalysis(
            pole_class=pole_class,
            length_ft=length_ft,
            compliance_status=compliance_status,
            issues=issues,
            recommendations=recommendations,
            capacity_utilization=utilization,
            safety_margin=safety_margin,
            details={
                "specification": {
                    "rated_capacity": spec.horizontal_load_lbs,
                    "effective_capacity": effective_capacity,
                    "min_top_circumference": spec.min_circumference_top_inches,
                    "min_groundline_circumference": spec.min_circumference_6ft_from_butt_inches
                },
                "applied_load": applied_load_lbs,
                "design_load": design_load,
                "safety_factor": self.safety_factor,
                "measurements": {
                    "top_circumference": measured_top_circumference,
                    "groundline_circumference": measured_groundline_circumference,
                    "decay_depth": decay_depth_inches
                }
            }
        )
    
    def compare_pole_classes(self, length_ft: float) -> List[Tuple[str, PoleSpecification]]:
        """
        Compare all available pole classes at a given length
        
        Args:
            length_ft: Pole length in feet
            
        Returns:
            List of (pole_class, specification) tuples sorted by capacity (highest first)
        """
        results = []
        
        for pole_class in get_all_pole_classes():
            spec = get_pole_specification(pole_class, length_ft)
            if spec:
                results.append((pole_class, spec))
        
        # Sort by capacity (highest first)
        results.sort(key=lambda x: x[1].horizontal_load_lbs, reverse=True)
        
        return results
    
    def get_recommended_pole_class(
        self,
        required_load_lbs: float,
        length_ft: float,
        include_safety_factor: bool = True
    ) -> Optional[Tuple[str, PoleSpecification]]:
        """
        Get recommended pole class for given load and length
        
        Args:
            required_load_lbs: Required load capacity in pounds
            length_ft: Pole length in feet
            include_safety_factor: Whether to apply safety factor to required load
            
        Returns:
            Tuple of (pole_class, specification) or None if no suitable pole found
        """
        design_load = required_load_lbs * self.safety_factor if include_safety_factor else required_load_lbs
        
        # Get all poles at this length, sorted by capacity
        available_poles = self.compare_pole_classes(length_ft)
        
        # Find the lightest pole that meets the requirement
        for pole_class, spec in reversed(available_poles):
            if spec.horizontal_load_lbs >= design_load:
                return (pole_class, spec)
        
        return None
    
    def calculate_remaining_life(
        self,
        pole_class: str,
        length_ft: float,
        current_decay_depth_inches: float,
        decay_rate_inches_per_year: float = 0.05
    ) -> Dict:
        """
        Estimate remaining pole life based on decay progression
        
        Args:
            pole_class: Pole class
            length_ft: Pole length in feet
            current_decay_depth_inches: Current decay depth in inches
            decay_rate_inches_per_year: Decay progression rate (default 0.05 in/year)
            
        Returns:
            Dictionary with remaining life estimates
        """
        spec = get_pole_specification(pole_class, length_ft)
        
        if not spec:
            return {"error": "Specification not found"}
        
        groundline_diameter = spec.get_groundline_diameter_inches()
        
        # Calculate current strength
        current_strength_ratio, current_loss_pct = calculate_strength_reduction_from_decay(
            groundline_diameter,
            current_decay_depth_inches
        )
        
        # Calculate decay depth at various strength loss thresholds
        thresholds = {
            "marginal": 15,  # 15% loss
            "critical": 30,  # 30% loss
            "failure": 50    # 50% loss
        }
        
        estimates = {}
        for threshold_name, loss_pct in thresholds.items():
            # Calculate required decay depth for this loss percentage
            # Strength ratio = (d_remaining / d_original)^3
            target_ratio = 1 - (loss_pct / 100)
            remaining_diameter = groundline_diameter * (target_ratio ** (1/3))
            target_decay_depth = (groundline_diameter - remaining_diameter) / 2
            
            # Calculate years until this threshold
            additional_decay = target_decay_depth - current_decay_depth_inches
            years_remaining = additional_decay / decay_rate_inches_per_year if decay_rate_inches_per_year > 0 else float('inf')
            
            estimates[threshold_name] = {
                "years_remaining": max(0, years_remaining),
                "target_decay_depth": target_decay_depth,
                "strength_loss_percent": loss_pct
            }
        
        return {
            "current_decay_depth": current_decay_depth_inches,
            "current_strength_loss": current_loss_pct,
            "decay_rate": decay_rate_inches_per_year,
            "estimates": estimates,
            "recommendation": self._get_life_recommendation(estimates)
        }
    
    def _get_life_recommendation(self, estimates: Dict) -> str:
        """Get recommendation based on remaining life estimates"""
        marginal_years = estimates["marginal"]["years_remaining"]
        critical_years = estimates["critical"]["years_remaining"]
        
        if marginal_years <= 0:
            return "URGENT: Pole has reached marginal condition. Schedule replacement immediately."
        elif marginal_years <= 2:
            return f"Schedule replacement within {marginal_years:.1f} years (approaching marginal condition)."
        elif marginal_years <= 5:
            return f"Plan replacement within {marginal_years:.1f} years. Increase inspection frequency."
        elif critical_years <= 10:
            return f"Monitor closely. Estimated {marginal_years:.1f} years to marginal condition."
        else:
            return f"Pole in good condition. Estimated {marginal_years:.1f} years to marginal condition."


# Made with Bob