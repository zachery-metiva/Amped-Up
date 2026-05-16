"""
Pole Inspection Rules and Defect Detection Model
Based on NESC 2023, OSHA 1910.269, Michigan PSC standards, and the Pole Compliance Exemplar Library v0.7
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class DefectSeverity(Enum):
    """OSHA 29 CFR 1903.14 severity classification"""
    IMMINENT_DANGER = "imminent_danger"  # Immediate threat to life/health
    SERIOUS = "serious"  # Substantial probability of death or serious harm
    OTHER_THAN_SERIOUS = "other_than_serious"  # Direct relationship to safety/health but not serious
    DE_MINIMIS = "deminimis"  # No direct relationship to safety/health
    MULTI_DEFECT = "multi_defect"  # Multiple compounding defects


class WeatherCondition(Enum):
    """Weather conditions affecting pole inspection"""
    NORMAL = "normal"
    ICE_LOADING = "ice_loading"  # NESC 250.B heavy district
    SNOW_ACCUMULATION = "snow_accumulation"
    POST_STORM = "post_storm"  # Wind, lightning damage
    SUMMER_THERMAL = "summer_thermal"  # NESC 232 at max temp


class DefectCategory(Enum):
    """Categories of pole defects"""
    VEGETATION = "vegetation"
    STRUCTURAL = "structural"
    HARDWARE = "hardware"
    CLEARANCE = "clearance"
    GROUNDING = "grounding"
    INSULATION = "insulation"
    CORROSION = "corrosion"
    DECAY = "decay"
    ATTACHMENT = "attachment"
    IDENTIFICATION = "identification"
    WEATHER_INDUCED = "weather_induced"


@dataclass
class DefectRule:
    """Rule for detecting and classifying a defect"""
    defect_id: str
    name: str
    category: DefectCategory
    severity: DefectSeverity
    description: str
    nesc_reference: Optional[str] = None
    osha_reference: Optional[str] = None
    michigan_reference: Optional[str] = None
    detection_criteria: Optional[Dict] = None
    corrective_action: Optional[str] = None
    weather_sensitive: bool = False


@dataclass
class PoleType:
    """Pole type specification from dataset"""
    pole_id: str
    name: str
    height_ft: float
    ansi_class: str
    embedment_ft: float
    voltage_kv: Optional[float] = None
    voltage_v: Optional[int] = None
    material: str = "wood"
    neutral: Optional[str] = None
    species: Optional[str] = None
    description: Optional[str] = None


class PoleInspectionRules:
    """
    Comprehensive pole inspection rules based on:
    - NESC 2023 (IEEE C2)
    - OSHA 29 CFR 1910.269
    - OSHA 29 CFR 1903.14
    - Michigan PSC R 460.3504 and R 460.601
    - Pole Compliance Exemplar Library v0.7
    """
    
    def __init__(self):
        self.defect_rules = self._build_defect_rules()
        self.pole_types = self._load_pole_types()
        self.clearance_requirements = self._build_clearance_requirements()
        self.vegetation_clearance_michigan = self._build_vegetation_clearance()
    
    def _build_defect_rules(self) -> Dict[str, DefectRule]:
        """Build comprehensive defect detection rules"""
        rules = {}
        
        # VEGETATION DEFECTS (NESC 218, NERC FAC-003)
        rules["veg_contact"] = DefectRule(
            defect_id="veg_contact",
            name="Vegetation Contact with Conductor",
            category=DefectCategory.VEGETATION,
            severity=DefectSeverity.SERIOUS,
            description="Tree branches or vegetation in direct contact with energized conductors",
            nesc_reference="NESC 218",
            michigan_reference="MPSC R 460.3504",
            detection_criteria={
                "min_clearance_ft": 0,
                "contact_type": "direct"
            },
            corrective_action="Immediate vegetation removal, line de-energization if necessary",
            weather_sensitive=True
        )
        
        rules["veg_encroachment"] = DefectRule(
            defect_id="veg_encroachment",
            name="Vegetation Encroachment",
            category=DefectCategory.VEGETATION,
            severity=DefectSeverity.OTHER_THAN_SERIOUS,
            description="Vegetation within minimum clearance zone but not in contact",
            nesc_reference="NESC 218",
            detection_criteria={
                "min_clearance_primary_side_ft": 10,
                "min_clearance_above_ft": 15,
                "min_clearance_below_ft": 10
            },
            corrective_action="Schedule vegetation trimming within utility cycle",
            weather_sensitive=True
        )
        
        # STRUCTURAL DEFECTS
        rules["pole_lean"] = DefectRule(
            defect_id="pole_lean",
            name="Excessive Pole Lean",
            category=DefectCategory.STRUCTURAL,
            severity=DefectSeverity.SERIOUS,
            description="Pole leaning beyond acceptable limits, indicating foundation failure",
            nesc_reference="NESC 261",
            detection_criteria={
                "max_lean_degrees": 5,
                "max_lean_percent": 8.7  # tan(5°) ≈ 8.7%
            },
            corrective_action="Guy wire installation or pole replacement",
            weather_sensitive=True
        )
        
        rules["pole_decay"] = DefectRule(
            defect_id="pole_decay",
            name="Pole Groundline Decay",
            category=DefectCategory.DECAY,
            severity=DefectSeverity.SERIOUS,
            description="Wood decay at groundline reducing structural capacity",
            nesc_reference="ANSI O5.1",
            detection_criteria={
                "max_decay_depth_inches": 1.5,
                "max_strength_loss_percent": 30
            },
            corrective_action="Pole replacement or reinforcement within 6 months",
            weather_sensitive=False
        )
        
        rules["crossarm_split"] = DefectRule(
            defect_id="crossarm_split",
            name="Crossarm Split or Crack",
            category=DefectCategory.STRUCTURAL,
            severity=DefectSeverity.SERIOUS,
            description="Longitudinal split in crossarm compromising structural integrity",
            nesc_reference="NESC 261",
            detection_criteria={
                "max_split_length_inches": 6,
                "max_split_depth_percent": 50
            },
            corrective_action="Crossarm replacement",
            weather_sensitive=True
        )
        
        rules["crossarm_decay"] = DefectRule(
            defect_id="crossarm_decay",
            name="Crossarm Decay",
            category=DefectCategory.DECAY,
            severity=DefectSeverity.SERIOUS,
            description="Wood decay in crossarm at attachment points",
            detection_criteria={
                "max_decay_depth_inches": 1.0
            },
            corrective_action="Crossarm replacement",
            weather_sensitive=False
        )
        
        # HARDWARE DEFECTS
        rules["insulator_damaged"] = DefectRule(
            defect_id="insulator_damaged",
            name="Damaged Insulator",
            category=DefectCategory.INSULATION,
            severity=DefectSeverity.SERIOUS,
            description="Cracked, chipped, or shattered insulator",
            nesc_reference="NESC 277, ANSI C29",
            detection_criteria={
                "damage_types": ["crack", "chip", "shatter", "arc_tracking"]
            },
            corrective_action="Insulator replacement",
            weather_sensitive=True
        )
        
        rules["guy_corrosion"] = DefectRule(
            defect_id="guy_corrosion",
            name="Guy Wire Corrosion",
            category=DefectCategory.CORROSION,
            severity=DefectSeverity.SERIOUS,
            description="Corrosion of guy wire reducing tensile strength",
            nesc_reference="ASTM A475",
            detection_criteria={
                "max_strand_breaks": 2,
                "max_corrosion_percent": 25
            },
            corrective_action="Guy wire replacement",
            weather_sensitive=False
        )
        
        rules["anchor_exposed"] = DefectRule(
            defect_id="anchor_exposed",
            name="Anchor Rod Exposed",
            category=DefectCategory.STRUCTURAL,
            severity=DefectSeverity.OTHER_THAN_SERIOUS,
            description="Guy anchor rod exposed above ground due to erosion",
            detection_criteria={
                "min_burial_depth_ft": 6
            },
            corrective_action="Re-bury anchor or install new anchor",
            weather_sensitive=False
        )
        
        rules["loose_hardware"] = DefectRule(
            defect_id="loose_hardware",
            name="Loose Hardware",
            category=DefectCategory.HARDWARE,
            severity=DefectSeverity.OTHER_THAN_SERIOUS,
            description="Loose bolts, clamps, or other hardware",
            detection_criteria={
                "hardware_types": ["bolt", "clamp", "bracket", "brace"]
            },
            corrective_action="Tighten or replace hardware",
            weather_sensitive=False
        )
        
        # CLEARANCE VIOLATIONS (NESC 232, 234, 235)
        rules["clearance_ground"] = DefectRule(
            defect_id="clearance_ground",
            name="Ground Clearance Violation",
            category=DefectCategory.CLEARANCE,
            severity=DefectSeverity.SERIOUS,
            description="Conductor clearance below minimum for ground",
            nesc_reference="NESC 232.A",
            detection_criteria={
                "min_clearance_ft": 18  # Varies by voltage and location
            },
            corrective_action="Conductor re-tensioning or pole height increase",
            weather_sensitive=True
        )
        
        rules["clearance_road"] = DefectRule(
            defect_id="clearance_road",
            name="Road Clearance Violation",
            category=DefectCategory.CLEARANCE,
            severity=DefectSeverity.SERIOUS,
            description="Conductor clearance below minimum for roadway",
            nesc_reference="NESC 232.C",
            detection_criteria={
                "min_clearance_ft": 18  # 15.5 ft for <600V, 18 ft for distribution
            },
            corrective_action="Immediate conductor adjustment",
            weather_sensitive=True
        )
        
        rules["clearance_building"] = DefectRule(
            defect_id="clearance_building",
            name="Building Clearance Violation",
            category=DefectCategory.CLEARANCE,
            severity=DefectSeverity.SERIOUS,
            description="Insufficient clearance from building or structure",
            nesc_reference="NESC 234",
            detection_criteria={
                "min_horizontal_clearance_ft": 3,
                "min_vertical_clearance_ft": 8
            },
            corrective_action="Conductor relocation or building modification",
            weather_sensitive=False
        )
        
        rules["phase_separation"] = DefectRule(
            defect_id="phase_separation",
            name="Phase Separation Violation",
            category=DefectCategory.CLEARANCE,
            severity=DefectSeverity.IMMINENT_DANGER,
            description="Insufficient separation between phase conductors",
            nesc_reference="NESC 235",
            detection_criteria={
                "min_separation_inches": 12  # Varies by voltage
            },
            corrective_action="Immediate line de-energization and repair",
            weather_sensitive=True
        )
        
        # GROUNDING DEFECTS (NESC 97)
        rules["ground_missing"] = DefectRule(
            defect_id="ground_missing",
            name="Missing Ground Wire",
            category=DefectCategory.GROUNDING,
            severity=DefectSeverity.SERIOUS,
            description="Required grounding conductor missing or disconnected",
            nesc_reference="NESC 97",
            osha_reference="OSHA 1910.269(n)",
            detection_criteria={
                "required_locations": ["transformer", "arrester", "guy_anchor", "equipment"]
            },
            corrective_action="Install proper grounding",
            weather_sensitive=False
        )
        
        # SERVICE DROP DEFECTS (NESC 230)
        rules["service_drop_low"] = DefectRule(
            defect_id="service_drop_low",
            name="Service Drop Too Low",
            category=DefectCategory.CLEARANCE,
            severity=DefectSeverity.SERIOUS,
            description="Service drop below minimum clearance",
            nesc_reference="NESC 230",
            detection_criteria={
                "min_clearance_pedestrian_ft": 10,
                "min_clearance_driveway_ft": 12,
                "min_clearance_road_ft": 15.5
            },
            corrective_action="Service drop adjustment or pole relocation",
            weather_sensitive=True
        )
        
        rules["weatherhead_damaged"] = DefectRule(
            defect_id="weatherhead_damaged",
            name="Damaged Weatherhead",
            category=DefectCategory.HARDWARE,
            severity=DefectSeverity.OTHER_THAN_SERIOUS,
            description="Service weatherhead damaged or improperly oriented",
            nesc_reference="NESC 230",
            corrective_action="Weatherhead replacement",
            weather_sensitive=False
        )
        
        # EQUIPMENT DEFECTS
        rules["transformer_oil_leak"] = DefectRule(
            defect_id="transformer_oil_leak",
            name="Transformer Oil Leak",
            category=DefectCategory.HARDWARE,
            severity=DefectSeverity.SERIOUS,
            description="Visible oil leak from transformer",
            detection_criteria={
                "leak_severity": ["minor", "moderate", "severe"]
            },
            corrective_action="Transformer replacement or repair",
            weather_sensitive=False
        )
        
        rules["cutout_hanging"] = DefectRule(
            defect_id="cutout_hanging",
            name="Cutout Fuse Hanging Open",
            category=DefectCategory.HARDWARE,
            severity=DefectSeverity.OTHER_THAN_SERIOUS,
            description="Fuse cutout in open position (blown fuse)",
            corrective_action="Investigate cause and replace fuse",
            weather_sensitive=False
        )
        
        # IDENTIFICATION DEFECTS
        rules["pole_number_illegible"] = DefectRule(
            defect_id="pole_number_illegible",
            name="Pole Number Illegible",
            category=DefectCategory.IDENTIFICATION,
            severity=DefectSeverity.DE_MINIMIS,
            description="Pole identification number faded or missing",
            michigan_reference="MPSC R 460.601",
            corrective_action="Replace pole tag",
            weather_sensitive=False
        )
        
        # WEATHER-INDUCED DEFECTS
        rules["ice_sag_violation"] = DefectRule(
            defect_id="ice_sag_violation",
            name="Ice Loading Clearance Violation",
            category=DefectCategory.WEATHER_INDUCED,
            severity=DefectSeverity.SERIOUS,
            description="Ice accumulation causing conductor sag below clearance",
            nesc_reference="NESC 250.B, NESC 232",
            detection_criteria={
                "weather_condition": "ice_loading",
                "ice_thickness_inches": 0.5
            },
            corrective_action="Monitor and de-ice if necessary",
            weather_sensitive=True
        )
        
        rules["thermal_sag_violation"] = DefectRule(
            defect_id="thermal_sag_violation",
            name="Summer Thermal Sag Violation",
            category=DefectCategory.WEATHER_INDUCED,
            severity=DefectSeverity.SERIOUS,
            description="High temperature causing excessive conductor sag",
            nesc_reference="NESC 232, IEEE 738",
            detection_criteria={
                "weather_condition": "summer_thermal",
                "conductor_temp_c": 75
            },
            corrective_action="Conductor re-tensioning or replacement",
            weather_sensitive=True
        )
        
        rules["storm_damage"] = DefectRule(
            defect_id="storm_damage",
            name="Storm Damage",
            category=DefectCategory.WEATHER_INDUCED,
            severity=DefectSeverity.IMMINENT_DANGER,
            description="Physical damage from wind, lightning, or debris",
            detection_criteria={
                "weather_condition": "post_storm",
                "damage_types": ["broken_crossarm", "downed_conductor", "lightning_scorch"]
            },
            corrective_action="Immediate repair or line de-energization",
            weather_sensitive=True
        )
        
        return rules
    
    def _load_pole_types(self) -> Dict[str, PoleType]:
        """Load pole type specifications from dataset metadata"""
        pole_types = {
            "ju40c4": PoleType(
                pole_id="ju40c4",
                name="Joint-use distribution tangent pole",
                height_ft=40,
                ansi_class="4",
                embedment_ft=6.0,
                voltage_kv=12.47,
                neutral="grounded_wye",
                species="southern_yellow_pine",
                description="Most common residential distribution pole in Michigan"
            ),
            "sp35c5": PoleType(
                pole_id="sp35c5",
                name="Single-phase tangent distribution pole",
                height_ft=35,
                ansi_class="5",
                embedment_ft=5.5,
                voltage_kv=7.2,
                neutral="grounded",
                description="Single-phase lateral tap, residential"
            ),
            "ang40c4": PoleType(
                pole_id="ang40c4",
                name="Three-phase angle distribution pole",
                height_ft=40,
                ansi_class="4",
                embedment_ft=6.0,
                voltage_kv=12.47,
                neutral="grounded_wye",
                description="Line direction change, double crossarm with bisector guy"
            ),
            "de45c3": PoleType(
                pole_id="de45c3",
                name="Three-phase dead-end pole",
                height_ft=45,
                ansi_class="3",
                embedment_ft=6.5,
                voltage_kv=12.47,
                neutral="grounded_wye",
                description="Line termination, twin down guys, strain insulators"
            ),
            "serv30c6": PoleType(
                pole_id="serv30c6",
                name="Single residential service pole",
                height_ft=30,
                ansi_class="6",
                embedment_ft=5.0,
                voltage_v=240,
                neutral="service_neutral",
                description="Single customer service with pole-mount meter"
            ),
        }
        return pole_types
    
    def _build_clearance_requirements(self) -> Dict[str, Dict]:
        """Build NESC clearance requirements"""
        return {
            "ground": {
                "0-750V": 18.0,  # feet
                "750V-22kV": 18.5,
                "22kV-50kV": 20.0,
                "description": "NESC 232.A - Clearance above ground"
            },
            "roadway": {
                "0-600V": 15.5,
                "600V-22kV": 18.0,
                "22kV-50kV": 20.0,
                "description": "NESC 232.C - Clearance above roads"
            },
            "railroad": {
                "all_voltages": 26.0,
                "description": "NESC 234.F, AAR M-1004"
            },
            "water": {
                "navigable": 28.0,
                "non_navigable": 18.0,
                "description": "NESC 232.B, USACE"
            },
            "building": {
                "horizontal": 3.0,
                "vertical_above_roof": 8.0,
                "description": "NESC 234"
            },
            "phase_separation": {
                "0-8.7kV": 12.0,  # inches
                "8.7-15kV": 18.0,
                "15-50kV": 24.0,
                "description": "NESC 235"
            }
        }
    
    def _build_vegetation_clearance(self) -> Dict:
        """Build Michigan vegetation clearance requirements"""
        return {
            "primary_distribution": {
                "side_ft": 10,
                "above_ft": 15,
                "below_ft": 10,
                "consumers_energy_cycle_low_v": "4 years",
                "consumers_energy_cycle_high_v": "3 years",
                "dte_electric_cycle_distribution": "4 years",
                "dte_electric_cycle_subtransmission": "3 years"
            },
            "service_drops": "Maintain clearance per NESC 230",
            "transmission_200kv_plus": "Per NERC FAC-003"
        }
    
    def get_defect_rule(self, defect_id: str) -> Optional[DefectRule]:
        """Get a specific defect rule"""
        return self.defect_rules.get(defect_id)
    
    def get_rules_by_category(self, category: DefectCategory) -> List[DefectRule]:
        """Get all rules for a specific category"""
        return [rule for rule in self.defect_rules.values() if rule.category == category]
    
    def get_rules_by_severity(self, severity: DefectSeverity) -> List[DefectRule]:
        """Get all rules for a specific severity level"""
        return [rule for rule in self.defect_rules.values() if rule.severity == severity]
    
    def get_weather_sensitive_rules(self) -> List[DefectRule]:
        """Get all weather-sensitive rules"""
        return [rule for rule in self.defect_rules.values() if rule.weather_sensitive]
    
    def evaluate_clearance(
        self,
        clearance_type: str,
        voltage_kv: float,
        measured_clearance_ft: float
    ) -> Tuple[bool, str]:
        """
        Evaluate if clearance meets requirements
        
        Returns:
            Tuple of (is_compliant, message)
        """
        requirements = self.clearance_requirements.get(clearance_type, {})
        
        # Determine voltage range
        if voltage_kv <= 0.75:
            voltage_range = "0-750V"
        elif voltage_kv <= 22:
            voltage_range = "750V-22kV"
        else:
            voltage_range = "22kV-50kV"
        
        required_clearance = requirements.get(voltage_range, requirements.get("all_voltages", 18.0))
        
        is_compliant = measured_clearance_ft >= required_clearance
        
        if is_compliant:
            message = f"Compliant: {measured_clearance_ft:.1f} ft exceeds minimum {required_clearance:.1f} ft"
        else:
            deficit = required_clearance - measured_clearance_ft
            message = f"Violation: {measured_clearance_ft:.1f} ft is {deficit:.1f} ft below minimum {required_clearance:.1f} ft"
        
        return is_compliant, message
    
    def get_pole_type(self, pole_id: str) -> Optional[PoleType]:
        """Get pole type specification"""
        return self.pole_types.get(pole_id)
    
    def get_all_defect_ids(self) -> List[str]:
        """Get list of all defect IDs"""
        return list(self.defect_rules.keys())
    
    def get_inspection_checklist(self, pole_type_id: str) -> Dict:
        """Generate inspection checklist for a pole type"""
        pole_type = self.get_pole_type(pole_type_id)
        
        if not pole_type:
            return {"error": f"Unknown pole type: {pole_type_id}"}
        
        checklist = {
            "pole_type": pole_type.name,
            "pole_id": pole_type_id,
            "height_ft": pole_type.height_ft,
            "ansi_class": pole_type.ansi_class,
            "voltage_kv": pole_type.voltage_kv,
            "inspection_items": []
        }
        
        # Add relevant inspection items based on pole type
        for rule in self.defect_rules.values():
            checklist["inspection_items"].append({
                "defect_id": rule.defect_id,
                "name": rule.name,
                "category": rule.category.value,
                "severity_if_found": rule.severity.value,
                "check_for": rule.description
            })
        
        return checklist


# Made with Bob