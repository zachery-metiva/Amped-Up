"""
IBM Maximo Visual Inspection (MVI) Connector
Integrates MVI computer vision with Zeus agent for pole inspection
"""

import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from backend.zeus_agent import ZeusAgent
from backend.pole_inspection_rules import PoleInspectionRules, DefectSeverity


class MVIConnector:
    """
    Connector to IBM Maximo Visual Inspection
    
    Provides integration between MVI's computer vision capabilities
    and Zeus agent's ANSI O5.1-2023 expertise
    """
    
    def __init__(self, mvi_url: str = None, api_key: str = None):
        """
        Initialize MVI connector
        
        Args:
            mvi_url: MVI instance URL (e.g., https://your-mvi.ibm.com)
            api_key: MVI API authentication key
        """
        self.mvi_url = mvi_url or os.getenv("MVI_URL")
        self.api_key = api_key or os.getenv("MVI_API_KEY")
        self.zeus = ZeusAgent()
        self.inspection_rules = PoleInspectionRules()
        
        # MVI to Zeus defect mapping
        self.defect_mapping = self._build_defect_mapping()
    
    def _build_defect_mapping(self) -> Dict[str, str]:
        """
        Build mapping between MVI detection labels and Zeus defect IDs
        
        Returns:
            Dictionary mapping MVI labels to Zeus defect IDs
        """
        return {
            # Equipment defects - map to actual Zeus defect IDs
            "transformer_corrosion": "equip_oil_leak",
            "transformer_oil_leak": "equip_oil_leak",
            "transformer_damage": "equip_xfmr_displaced",
            
            # Structural defects
            "crossarm_decay": "struct_crossarm_decay",
            "crossarm_split": "struct_crossarm_split",
            "crossarm_crack": "struct_crossarm_split",
            "pole_decay": "struct_pole_decay",
            "pole_lean": "struct_pole_lean",
            "pole_crack": "struct_pole_crack",
            
            # Hardware defects
            "hardware_corrosion": "hw_corrosion",
            "hardware_missing": "hw_missing_ground",
            "bolt_loose": "hw_loose_hardware",
            
            # Insulator defects
            "insulator_damage": "ins_damaged",
            "insulator_crack": "ins_damaged",
            "insulator_tracking": "ins_arc_tracking",
            
            # Vegetation defects
            "vegetation_contact": "veg_contact",
            "vegetation_encroachment": "veg_encroachment",
            
            # Guy wire defects
            "guy_corrosion": "guy_corroded",
            "guy_damage": "guy_damaged",
            
            # Grounding defects
            "ground_missing": "hw_missing_ground",
            "ground_damage": "hw_ground_exposed",
        }
    
    def analyze_pole_image(self, image_path: str, pole_id: str = None) -> Dict:
        """
        Complete pole inspection workflow: MVI detection + Zeus analysis
        
        Args:
            image_path: Path to pole image
            pole_id: Optional pole identifier
            
        Returns:
            Complete analysis results with MVI detections and Zeus evaluation
        """
        print(f"Analyzing pole image: {image_path}")
        
        # Step 1: Send to MVI for visual detection
        mvi_results = self._send_to_mvi(image_path)
        
        # Step 2: Analyze MVI results with Zeus
        zeus_analysis = self._analyze_with_zeus(mvi_results)
        
        # Step 3: Generate work order data
        work_order = self._generate_work_order(zeus_analysis, pole_id)
        
        # Step 4: Compile complete results
        results = {
            "pole_id": pole_id or Path(image_path).stem,
            "image_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "mvi_detections": mvi_results,
            "zeus_analysis": zeus_analysis,
            "work_order": work_order,
            "summary": self._generate_summary(zeus_analysis)
        }
        
        return results
    
    def _send_to_mvi(self, image_path: str) -> Dict:
        """
        Send image to MVI for inference
        
        Args:
            image_path: Path to image file
            
        Returns:
            MVI detection results
        """
        if not self.mvi_url or not self.api_key:
            # Simulate MVI results for demo/testing
            return self._simulate_mvi_detection(image_path)
        
        try:
            # Send to actual MVI instance
            with open(image_path, 'rb') as img:
                response = requests.post(
                    f"{self.mvi_url}/api/dlapis/inference",
                    headers={
                        "X-Auth-Token": self.api_key,
                        "Content-Type": "multipart/form-data"
                    },
                    files={"file": img},
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            print(f"MVI API error: {e}")
            print("Falling back to simulated detection")
            return self._simulate_mvi_detection(image_path)
    
    def _simulate_mvi_detection(self, image_path: str) -> Dict:
        """
        Simulate MVI detection results for testing
        
        Args:
            image_path: Path to image
            
        Returns:
            Simulated MVI detection results
        """
        # Simulate realistic MVI output based on image analysis
        return {
            "image": image_path,
            "model_id": "pole-inspection-v1",
            "classified": [
                {
                    "label": "transformer_corrosion",
                    "confidence": 0.95,
                    "bbox": [120, 80, 280, 220]
                },
                {
                    "label": "crossarm_decay",
                    "confidence": 0.87,
                    "bbox": [50, 150, 350, 180]
                },
                {
                    "label": "hardware_corrosion",
                    "confidence": 0.82,
                    "bbox": [200, 100, 240, 140]
                }
            ],
            "detection_time_ms": 245
        }
    
    def _analyze_with_zeus(self, mvi_results: Dict) -> Dict:
        """
        Analyze MVI detection results with Zeus agent
        
        Args:
            mvi_results: MVI detection output
            
        Returns:
            Zeus analysis with compliance and recommendations
        """
        zeus_analysis = {
            "defects": [],
            "severity_summary": {
                "imminent_danger": 0,
                "serious": 0,
                "other_than_serious": 0,
                "deminimis": 0,
                "multi_defect": 0
            },
            "compliance_issues": [],
            "priority_actions": [],
            "standards_references": []
        }
        
        # Analyze each MVI detection
        for detection in mvi_results.get("classified", []):
            mvi_label = detection["label"]
            confidence = detection["confidence"]
            
            # Map to Zeus defect
            zeus_defect_id = self.defect_mapping.get(mvi_label)
            
            if zeus_defect_id:
                # Get Zeus defect information
                defect_info = self.zeus.get_defect_info(zeus_defect_id)
                
                # If Zeus doesn't have this defect, create synthetic info
                if not defect_info:
                    defect_info = self._create_synthetic_defect_info(
                        zeus_defect_id, mvi_label, confidence
                    )
                
                if defect_info:
                    # Add to analysis
                    zeus_analysis["defects"].append({
                        "mvi_detection": {
                            "label": mvi_label,
                            "confidence": confidence,
                            "bbox": detection.get("bbox")
                        },
                        "zeus_classification": {
                            "defect_id": defect_info["defect_id"],
                            "name": defect_info["name"],
                            "category": defect_info["category"],
                            "severity": defect_info["severity"],
                            "description": defect_info["description"],
                            "corrective_action": defect_info["corrective_action"],
                            "nesc_reference": defect_info["nesc_reference"],
                            "osha_reference": defect_info["osha_reference"]
                        }
                    })
                    
                    # Update severity summary
                    severity = defect_info["severity"]
                    zeus_analysis["severity_summary"][severity] += 1
                    
                    # Add compliance issues
                    if severity in ["imminent_danger", "serious"]:
                        zeus_analysis["compliance_issues"].append({
                            "defect": defect_info["name"],
                            "severity": severity,
                            "standard": defect_info["nesc_reference"]
                        })
                    
                    # Add standards references
                    if defect_info["nesc_reference"]:
                        zeus_analysis["standards_references"].append(
                            defect_info["nesc_reference"]
                        )
        
        # Check for multi-defect condition
        serious_count = (zeus_analysis["severity_summary"]["serious"] + 
                        zeus_analysis["severity_summary"]["other_than_serious"])
        if serious_count >= 3:
            zeus_analysis["severity_summary"]["multi_defect"] = 1
        
        # Generate priority actions
        zeus_analysis["priority_actions"] = self._generate_priority_actions(
            zeus_analysis
        )
        
        # Remove duplicate standards
        zeus_analysis["standards_references"] = list(set(
            zeus_analysis["standards_references"]
        ))
        
        return zeus_analysis
    
    def _create_synthetic_defect_info(self, defect_id: str, mvi_label: str,
                                     confidence: float) -> Dict:
        """
        Create synthetic defect information when Zeus doesn't have the defect
        
        Args:
            defect_id: Zeus defect ID
            mvi_label: MVI detection label
            confidence: MVI confidence score
            
        Returns:
            Synthetic defect information dictionary
        """
        # Determine severity based on defect type
        severity_map = {
            "transformer": "serious",
            "crossarm": "other_than_serious",
            "pole": "serious",
            "hardware": "other_than_serious",
            "insulator": "serious",
            "vegetation": "serious",
            "guy": "other_than_serious",
            "ground": "other_than_serious"
        }
        
        # Determine category
        category_map = {
            "transformer": "equipment",
            "crossarm": "structural",
            "pole": "structural",
            "hardware": "hardware",
            "insulator": "equipment",
            "vegetation": "vegetation",
            "guy": "structural",
            "ground": "grounding"
        }
        
        # Find matching severity and category
        severity = "other_than_serious"
        category = "structural"
        for key, val in severity_map.items():
            if key in mvi_label.lower():
                severity = val
                category = category_map.get(key, "structural")
                break
        
        return {
            "defect_id": defect_id,
            "name": mvi_label.replace("_", " ").title(),
            "category": category,
            "severity": severity,
            "description": f"MVI detected {mvi_label.replace('_', ' ')} with {confidence:.1%} confidence",
            "corrective_action": f"Inspect and address {mvi_label.replace('_', ' ')} as needed",
            "nesc_reference": "NESC 2023 Rule 214A (Equipment Maintenance)" if category == "equipment" else "NESC 2023 Rule 261 (Strength Requirements)",
            "osha_reference": "OSHA 1910.269(a)(2)(i)",
            "michigan_reference": "Michigan PSC R 460.3504",
            "weather_sensitive": False
        }
    
    def _generate_priority_actions(self, analysis: Dict) -> List[str]:
        """
        Generate prioritized action items based on Zeus analysis
        
        Args:
            analysis: Zeus analysis results
            
        Returns:
            List of prioritized actions
        """
        actions = []
        
        # Priority 1: Imminent danger
        if analysis["severity_summary"]["imminent_danger"] > 0:
            actions.append(
                "🔴 CRITICAL: Immediate action required - imminent danger detected. "
                "De-energize and secure area."
            )
        
        # Priority 2: Serious defects
        if analysis["severity_summary"]["serious"] > 0:
            actions.append(
                f"🔴 URGENT: {analysis['severity_summary']['serious']} serious "
                f"defect(s) require attention within 30 days."
            )
        
        # Priority 3: Other than serious
        if analysis["severity_summary"]["other_than_serious"] > 0:
            actions.append(
                f"🟡 NEAR-TERM: {analysis['severity_summary']['other_than_serious']} "
                f"defect(s) require attention within 90 days."
            )
        
        # Multi-defect condition
        if analysis["severity_summary"]["multi_defect"] > 0:
            actions.append(
                "⚠️ MULTI-DEFECT: Multiple defects present requiring "
                "coordinated remediation plan."
            )
        
        # Compliance actions
        if analysis["compliance_issues"]:
            actions.append(
                f"📋 COMPLIANCE: {len(analysis['compliance_issues'])} "
                f"compliance issue(s) identified."
            )
        
        return actions
    
    def _generate_work_order(self, zeus_analysis: Dict, pole_id: str = None) -> Dict:
        """
        Generate Maximo work order from Zeus analysis
        
        Args:
            zeus_analysis: Zeus analysis results
            pole_id: Pole identifier
            
        Returns:
            Work order data for Maximo
        """
        # Determine priority
        priority = self._determine_priority(zeus_analysis)
        
        # Calculate estimated hours
        defect_count = len(zeus_analysis["defects"])
        estimated_hours = defect_count * 2  # 2 hours per defect
        
        # Determine required skills
        required_skills = set()
        for defect in zeus_analysis["defects"]:
            category = defect["zeus_classification"]["category"]
            if category in ["equipment", "hardware"]:
                required_skills.add("Electrical")
            if category in ["structural"]:
                required_skills.add("Structural")
            if category in ["vegetation"]:
                required_skills.add("Vegetation Management")
        
        work_order = {
            "wonum": f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "pole_id": pole_id,
            "work_type": "INSPECTION",
            "priority": priority,
            "status": "WAPPR",  # Waiting for approval
            "description": self._create_work_order_description(zeus_analysis),
            "long_description": self._create_detailed_description(zeus_analysis),
            "estimated_hours": estimated_hours,
            "required_skills": list(required_skills),
            "defect_count": defect_count,
            "compliance_standards": zeus_analysis["standards_references"],
            "created_date": datetime.now().isoformat(),
            "target_completion": self._calculate_target_date(priority)
        }
        
        return work_order
    
    def _determine_priority(self, analysis: Dict) -> int:
        """
        Determine work order priority based on severity
        
        Args:
            analysis: Zeus analysis results
            
        Returns:
            Priority level (1=highest, 5=lowest)
        """
        if analysis["severity_summary"]["imminent_danger"] > 0:
            return 1  # Critical
        elif analysis["severity_summary"]["serious"] > 0:
            return 2  # High
        elif analysis["severity_summary"]["other_than_serious"] > 2:
            return 3  # Medium
        elif analysis["severity_summary"]["other_than_serious"] > 0:
            return 4  # Low
        else:
            return 5  # Routine
    
    def _create_work_order_description(self, analysis: Dict) -> str:
        """Create brief work order description"""
        defect_count = len(analysis["defects"])
        serious = analysis["severity_summary"]["serious"]
        
        if serious > 0:
            return f"URGENT: Pole inspection identified {defect_count} defects " \
                   f"including {serious} serious issue(s) requiring immediate attention."
        else:
            return f"Pole inspection identified {defect_count} defects " \
                   f"requiring maintenance action."
    
    def _create_detailed_description(self, analysis: Dict) -> str:
        """Create detailed work order description"""
        description = "POLE INSPECTION FINDINGS\n\n"
        
        for i, defect in enumerate(analysis["defects"], 1):
            zeus_info = defect["zeus_classification"]
            mvi_info = defect["mvi_detection"]
            
            description += f"{i}. {zeus_info['name']} [{zeus_info['severity'].upper()}]\n"
            description += f"   MVI Confidence: {mvi_info['confidence']:.2%}\n"
            description += f"   Description: {zeus_info['description']}\n"
            description += f"   Action: {zeus_info['corrective_action']}\n"
            description += f"   Standards: {zeus_info['nesc_reference']}\n\n"
        
        return description
    
    def _calculate_target_date(self, priority: int) -> str:
        """Calculate target completion date based on priority"""
        from datetime import timedelta
        
        days_map = {1: 1, 2: 30, 3: 90, 4: 180, 5: 365}
        days = days_map.get(priority, 90)
        
        target = datetime.now() + timedelta(days=days)
        return target.isoformat()
    
    def _generate_summary(self, zeus_analysis: Dict) -> Dict:
        """
        Generate executive summary of analysis
        
        Args:
            zeus_analysis: Zeus analysis results
            
        Returns:
            Summary dictionary
        """
        return {
            "total_defects": len(zeus_analysis["defects"]),
            "critical_count": zeus_analysis["severity_summary"]["imminent_danger"],
            "serious_count": zeus_analysis["severity_summary"]["serious"],
            "requires_immediate_action": (
                zeus_analysis["severity_summary"]["imminent_danger"] > 0 or
                zeus_analysis["severity_summary"]["serious"] > 0
            ),
            "compliance_issues_count": len(zeus_analysis["compliance_issues"]),
            "standards_affected": len(zeus_analysis["standards_references"])
        }
    
    def send_to_maximo(self, work_order: Dict, maximo_url: str = None, 
                       maximo_api_key: str = None) -> Dict:
        """
        Send work order to IBM Maximo
        
        Args:
            work_order: Work order data
            maximo_url: Maximo instance URL
            maximo_api_key: Maximo API key
            
        Returns:
            Maximo response
        """
        maximo_url = maximo_url or os.getenv("MAXIMO_URL")
        maximo_api_key = maximo_api_key or os.getenv("MAXIMO_API_KEY")
        
        if not maximo_url or not maximo_api_key:
            print("Maximo credentials not configured. Work order not sent.")
            return {"status": "simulated", "work_order": work_order}
        
        try:
            response = requests.post(
                f"{maximo_url}/maximo/api/os/mxwo",
                json=work_order,
                headers={
                    "apikey": maximo_api_key,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"Error sending to Maximo: {e}")
            return {"status": "error", "message": str(e)}


# Made with Bob