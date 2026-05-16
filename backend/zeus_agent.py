"""
Zeus AI Agent - ANSI O5.1-2022 Wood Poles Expert
An intelligent conversational agent that understands and explains
ANSI O5.1-2022 Wood Poles, Specifications and Dimensions
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
from backend.pole_analyzer_agent import PoleAnalyzerAgent
from backend.pole_calculations import (
    calculate_bending_moment,
    calculate_fiber_stress,
    calculate_section_modulus,
    calculate_strength_reduction_from_decay,
    calculate_embedment_depth,
    calculate_wind_load
)


class QueryType(Enum):
    """Types of queries Zeus can handle"""
    SPECIFICATION_LOOKUP = "specification_lookup"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    CALCULATION = "calculation"
    EXPLANATION = "explanation"
    COMPLIANCE = "compliance"
    GENERAL = "general"


@dataclass
class ZeusResponse:
    """Response from Zeus agent"""
    query_type: QueryType
    answer: str
    data: Optional[Dict] = None
    suggestions: Optional[List[str]] = None
    confidence: float = 1.0


class ZeusAgent:
    """
    Zeus - AI Agent for ANSI O5.1-2022 Wood Poles
    
    Zeus is an expert system that understands utility pole specifications,
    can answer questions, provide recommendations, and explain concepts
    related to ANSI O5.1-2022 standards.
    """
    
    def __init__(self):
        self.analyzer = PoleAnalyzerAgent()
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, str]:
        """Build knowledge base about ANSI O5.1-2022"""
        return {
            "standard": """ANSI O5.1-2022 is the American National Standard for Wood Poles - 
            Specifications and Dimensions. It defines the requirements for wood utility poles 
            used in electrical distribution and transmission systems.""",
            
            "pole_classes": """Pole classes range from H6 (lightest) to H1 (heavy) for H-class poles, 
            and Class 1 (heaviest) to Class 7 (lightest) for standard classes. Each class has specific 
            minimum dimensions and load-bearing capacities.""",
            
            "fiber_stress": """The standard uses 8000 psi as the allowable fiber stress for most 
            wood species. This is the maximum stress allowed at the extreme fiber of the pole 
            under design loads.""",
            
            "load_application": """Horizontal loads are specified at 2 feet from the top of the pole. 
            This represents typical attachment points for electrical conductors and equipment.""",
            
            "groundline": """The groundline is defined as 6 feet from the butt (bottom) of the pole. 
            This is typically where the pole enters the ground and is the critical section for 
            structural analysis.""",
            
            "circumference": """Pole dimensions are specified by minimum circumference at the top 
            and at groundline (6 feet from butt). Circumference is used rather than diameter 
            because it's easier to measure in the field.""",
            
            "wood_species": """Common species include Southern Pine, Douglas Fir, Western Red Cedar, 
            and Northern White Cedar. Each species has different strength characteristics, but the 
            standard uses 8000 psi fiber stress as a baseline.""",
            
            "treatment": """Poles are typically treated with preservatives like Creosote, 
            Pentachlorophenol, or Chromated Copper Arsenate (CCA) to prevent decay and extend 
            service life.""",
            
            "safety_factor": """A safety factor of 1.5 to 2.0 is typically applied to design loads 
            to account for uncertainties in loading, material properties, and deterioration over time.""",
            
            "decay": """Decay is the primary cause of pole failure. Regular inspection and monitoring 
            of decay at the groundline is critical for maintaining pole integrity.""",
            
            "embedment": """Typical embedment depth is 10% of pole length plus 2 feet, adjusted for 
            soil conditions. Proper embedment is essential for stability.""",
            
            "inspection": """Poles should be inspected every 5-10 years, with more frequent inspections 
            for older poles or those in harsh environments."""
        }
    
    def ask(self, question: str, context: Optional[Dict] = None) -> ZeusResponse:
        """
        Ask Zeus a question about ANSI O5.1-2022
        
        Args:
            question: User's question
            context: Optional context (pole data, measurements, etc.)
            
        Returns:
            ZeusResponse with answer and relevant data
        """
        question_lower = question.lower()
        
        # Determine query type and route to appropriate handler
        if any(word in question_lower for word in ["what is", "define", "explain", "tell me about"]):
            return self._handle_explanation(question, context)
        
        elif any(word in question_lower for word in ["specification", "spec", "dimensions", "size"]):
            return self._handle_specification_lookup(question, context)
        
        elif any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
            return self._handle_comparison(question, context)
        
        elif any(word in question_lower for word in ["recommend", "suggest", "which pole", "what class"]):
            return self._handle_recommendation(question, context)
        
        elif any(word in question_lower for word in ["calculate", "compute", "how much", "load"]):
            return self._handle_calculation(question, context)
        
        elif any(word in question_lower for word in ["compliant", "meets", "acceptable", "safe"]):
            return self._handle_compliance(question, context)
        
        else:
            return self._handle_general(question, context)
    
    def _handle_explanation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle explanation requests"""
        question_lower = question.lower()
        
        # Check knowledge base for relevant topics
        for topic, explanation in self.knowledge_base.items():
            if topic.replace("_", " ") in question_lower:
                suggestions = [
                    f"Would you like to know more about {topic.replace('_', ' ')}?",
                    "I can also help with specifications, calculations, or recommendations.",
                    "Ask me about specific pole classes or load requirements."
                ]
                
                return ZeusResponse(
                    query_type=QueryType.EXPLANATION,
                    answer=explanation,
                    suggestions=suggestions,
                    confidence=0.9
                )
        
        # General ANSI O5.1-2022 explanation
        if "ansi" in question_lower or "o5.1" in question_lower or "standard" in question_lower:
            return ZeusResponse(
                query_type=QueryType.EXPLANATION,
                answer=self.knowledge_base["standard"],
                data={
                    "available_classes": get_all_pole_classes(),
                    "class_count": len(get_all_pole_classes())
                },
                suggestions=[
                    "Ask about specific pole classes (H1, Class 1, etc.)",
                    "Request specifications for a particular pole",
                    "Get recommendations for your load requirements"
                ]
            )
        
        # Pole class explanation
        if "class" in question_lower or "h1" in question_lower or "h2" in question_lower:
            return ZeusResponse(
                query_type=QueryType.EXPLANATION,
                answer=self.knowledge_base["pole_classes"] + "\n\nAvailable classes: " + 
                       ", ".join(get_all_pole_classes()),
                suggestions=[
                    "Compare different pole classes",
                    "Get specifications for a specific class",
                    "Find the right class for your load requirements"
                ]
            )
        
        return ZeusResponse(
            query_type=QueryType.GENERAL,
            answer="I'm Zeus, your ANSI O5.1-2022 expert. I can help with pole specifications, "
                   "load calculations, compliance checking, and recommendations. What would you like to know?",
            suggestions=[
                "What are the pole classes?",
                "How do I select the right pole?",
                "What is the load capacity of an H1 40ft pole?",
                "Calculate the bending moment for my application"
            ]
        )
    
    def _handle_specification_lookup(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle specification lookup requests"""
        # Extract pole class and length from question or context
        pole_class = None
        length = None
        
        if context:
            pole_class = context.get("pole_class")
            length = context.get("length_ft")
        
        # Try to extract from question
        question_lower = question.lower()
        for cls in get_all_pole_classes():
            if cls.lower() in question_lower:
                pole_class = cls
                break
        
        # Extract length
        import re
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question_lower)
        if length_match:
            length = float(length_match.group(1))
        
        if pole_class and length:
            spec = get_pole_specification(pole_class, length)
            if spec:
                answer = f"""**{spec.pole_class} Class Pole - {spec.length_ft}ft**

**Dimensions:**
- Minimum top circumference: {spec.min_circumference_top_inches}" ({spec.get_top_diameter_inches():.2f}" diameter)
- Minimum groundline circumference: {spec.min_circumference_6ft_from_butt_inches}" ({spec.get_groundline_diameter_inches():.2f}" diameter)

**Capacity:**
- Horizontal load capacity: {spec.horizontal_load_lbs:,} lbs (at 2 feet from top)
- Fiber stress: {spec.fiber_stress_psi:,} psi

**Application:**
This pole can support {spec.horizontal_load_lbs:,} lbs of horizontal load applied 2 feet from the top, 
with a fiber stress of {spec.fiber_stress_psi:,} psi at the groundline."""
                
                return ZeusResponse(
                    query_type=QueryType.SPECIFICATION_LOOKUP,
                    answer=answer,
                    data={
                        "pole_class": spec.pole_class,
                        "length_ft": spec.length_ft,
                        "top_circumference": spec.min_circumference_top_inches,
                        "groundline_circumference": spec.min_circumference_6ft_from_butt_inches,
                        "capacity_lbs": spec.horizontal_load_lbs,
                        "top_diameter": spec.get_top_diameter_inches(),
                        "groundline_diameter": spec.get_groundline_diameter_inches()
                    },
                    suggestions=[
                        f"Compare {pole_class} with other classes at {length}ft",
                        f"Calculate loads for this pole",
                        f"Check if this pole meets your requirements"
                    ]
                )
            else:
                return ZeusResponse(
                    query_type=QueryType.SPECIFICATION_LOOKUP,
                    answer=f"No specification found for {pole_class} class at {length}ft. "
                           f"Available lengths for {pole_class}: {get_available_lengths(pole_class)}",
                    confidence=0.5
                )
        
        elif pole_class:
            lengths = get_available_lengths(pole_class)
            return ZeusResponse(
                query_type=QueryType.SPECIFICATION_LOOKUP,
                answer=f"**{pole_class} Class Poles**\n\nAvailable lengths: {lengths}\n\n"
                       f"Please specify a length to get detailed specifications.",
                data={"pole_class": pole_class, "available_lengths": lengths},
                suggestions=[f"Get specs for {pole_class} {length}ft" for length in lengths[:3]]
            )
        
        else:
            return ZeusResponse(
                query_type=QueryType.SPECIFICATION_LOOKUP,
                answer="Please specify a pole class (e.g., H1, Class 1) and length (e.g., 40ft) "
                       "to get specifications.",
                data={"available_classes": get_all_pole_classes()},
                suggestions=[
                    "What are the specs for H1 40ft?",
                    "Show me Class 2 45ft specifications",
                    "List all available pole classes"
                ]
            )
    
    def _handle_comparison(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle pole comparison requests"""
        # Extract length for comparison
        length = None
        if context:
            length = context.get("length_ft")
        
        import re
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question.lower())
        if length_match:
            length = float(length_match.group(1))
        
        if length:
            results = self.analyzer.compare_pole_classes(length)
            
            if results:
                answer = f"**Pole Class Comparison at {length}ft**\n\n"
                answer += "| Class | Capacity (lbs) | Top Circ (in) | Groundline Circ (in) |\n"
                answer += "|-------|----------------|---------------|----------------------|\n"
                
                for pole_class, spec in results:
                    answer += f"| {pole_class:5s} | {spec.horizontal_load_lbs:14,} | {spec.min_circumference_top_inches:13.1f} | {spec.min_circumference_6ft_from_butt_inches:20.1f} |\n"
                
                answer += f"\n**Analysis:**\n"
                answer += f"- Strongest: {results[0][0]} ({results[0][1].horizontal_load_lbs:,} lbs)\n"
                answer += f"- Lightest: {results[-1][0]} ({results[-1][1].horizontal_load_lbs:,} lbs)\n"
                answer += f"- Capacity range: {results[-1][1].horizontal_load_lbs:,} - {results[0][1].horizontal_load_lbs:,} lbs"
                
                return ZeusResponse(
                    query_type=QueryType.COMPARISON,
                    answer=answer,
                    data={
                        "length_ft": length,
                        "poles": [
                            {
                                "class": cls,
                                "capacity": spec.horizontal_load_lbs,
                                "top_circ": spec.min_circumference_top_inches,
                                "groundline_circ": spec.min_circumference_6ft_from_butt_inches
                            }
                            for cls, spec in results
                        ]
                    },
                    suggestions=[
                        "Get detailed specs for a specific class",
                        "Find the right pole for your load requirements",
                        "Calculate loads for your application"
                    ]
                )
        
        return ZeusResponse(
            query_type=QueryType.COMPARISON,
            answer="Please specify a length to compare pole classes (e.g., 'Compare poles at 40ft')",
            suggestions=[
                "Compare poles at 40ft",
                "Compare poles at 45ft",
                "Show me all H-class poles"
            ]
        )
    
    def _handle_recommendation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle pole recommendation requests"""
        required_load = None
        length = None
        
        if context:
            required_load = context.get("required_load_lbs")
            length = context.get("length_ft")
        
        # Extract from question
        import re
        load_match = re.search(r'(\d+(?:,\d+)?)\s*(?:lb|lbs|pound)', question.lower())
        if load_match:
            required_load = float(load_match.group(1).replace(',', ''))
        
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question.lower())
        if length_match:
            length = float(length_match.group(1))
        
        if required_load and length:
            result = self.analyzer.get_recommended_pole_class(required_load, length)
            
            if result:
                pole_class, spec = result
                design_load = required_load * self.analyzer.safety_factor
                margin = spec.horizontal_load_lbs - design_load
                margin_pct = (margin / spec.horizontal_load_lbs) * 100
                
                answer = f"""**Pole Recommendation**

**Requirements:**
- Required load: {required_load:,.0f} lbs
- Pole length: {length} ft
- Design load (with safety factor {self.analyzer.safety_factor}): {design_load:,.0f} lbs

**Recommended Pole:**
- Class: **{pole_class}**
- Rated capacity: {spec.horizontal_load_lbs:,} lbs
- Safety margin: {margin:,.0f} lbs ({margin_pct:.1f}%)

**Specifications:**
- Top circumference: {spec.min_circumference_top_inches}" ({spec.get_top_diameter_inches():.2f}" diameter)
- Groundline circumference: {spec.min_circumference_6ft_from_butt_inches}" ({spec.get_groundline_diameter_inches():.2f}" diameter)

This pole provides adequate capacity with a {margin_pct:.1f}% safety margin above the design load."""
                
                return ZeusResponse(
                    query_type=QueryType.RECOMMENDATION,
                    answer=answer,
                    data={
                        "recommended_class": pole_class,
                        "required_load": required_load,
                        "design_load": design_load,
                        "pole_capacity": spec.horizontal_load_lbs,
                        "safety_margin_lbs": margin,
                        "safety_margin_percent": margin_pct,
                        "specification": {
                            "top_circumference": spec.min_circumference_top_inches,
                            "groundline_circumference": spec.min_circumference_6ft_from_butt_inches
                        }
                    },
                    suggestions=[
                        f"Get full specifications for {pole_class} {length}ft",
                        f"Compare {pole_class} with other options",
                        "Calculate actual loads for this pole"
                    ]
                )
            else:
                return ZeusResponse(
                    query_type=QueryType.RECOMMENDATION,
                    answer=f"No suitable pole found for {required_load:,.0f} lbs at {length}ft. "
                           f"The required load may exceed available pole capacities.",
                    confidence=0.7,
                    suggestions=[
                        "Consider using a shorter pole for higher capacity",
                        "Review load requirements",
                        "Consider using multiple poles or guy wires"
                    ]
                )
        
        return ZeusResponse(
            query_type=QueryType.RECOMMENDATION,
            answer="Please provide the required load (in lbs) and pole length (in ft) for a recommendation.",
            suggestions=[
                "Recommend a pole for 10,000 lbs at 40ft",
                "What pole do I need for 15,000 lbs at 45ft?",
                "Suggest a pole for my application"
            ]
        )
    
    def _handle_calculation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle calculation requests"""
        question_lower = question.lower()
        
        if "bending moment" in question_lower or "moment" in question_lower:
            load = context.get("load_lbs") if context else None
            height = context.get("height_ft") if context else None
            
            if load and height:
                moment = calculate_bending_moment(load, height)
                answer = f"""**Bending Moment Calculation**

Load: {load:,.0f} lbs
Height: {height} ft

**Bending Moment: {moment:,.0f} ft-lbs**

This is the moment at the base caused by the horizontal load applied at the specified height."""
                
                return ZeusResponse(
                    query_type=QueryType.CALCULATION,
                    answer=answer,
                    data={"load_lbs": load, "height_ft": height, "moment_ft_lbs": moment}
                )
        
        elif "decay" in question_lower or "strength loss" in question_lower:
            diameter = context.get("diameter_inches") if context else None
            decay = context.get("decay_depth_inches") if context else None
            
            if diameter and decay:
                ratio, loss_pct = calculate_strength_reduction_from_decay(diameter, decay)
                answer = f"""**Decay Strength Analysis**

Original diameter: {diameter} inches
Decay depth: {decay} inches

**Results:**
- Remaining strength: {ratio*100:.1f}%
- Strength loss: {loss_pct:.1f}%

{'⚠️ CRITICAL: Significant strength loss detected!' if loss_pct > 30 else 
 '⚠️ WARNING: Moderate strength loss' if loss_pct > 15 else 
 '✓ Acceptable decay level'}"""
                
                return ZeusResponse(
                    query_type=QueryType.CALCULATION,
                    answer=answer,
                    data={
                        "original_diameter": diameter,
                        "decay_depth": decay,
                        "strength_ratio": ratio,
                        "strength_loss_percent": loss_pct
                    }
                )
        
        return ZeusResponse(
            query_type=QueryType.CALCULATION,
            answer="I can help with various calculations. What would you like to calculate?",
            suggestions=[
                "Calculate bending moment",
                "Calculate strength loss from decay",
                "Calculate wind load",
                "Calculate embedment depth"
            ]
        )
    
    def _handle_compliance(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle compliance checking requests"""
        if not context or "pole_class" not in context:
            return ZeusResponse(
                query_type=QueryType.COMPLIANCE,
                answer="To check compliance, please provide pole measurements and specifications.",
                suggestions=[
                    "Analyze my pole for compliance",
                    "Check if my pole meets ANSI standards",
                    "What are the compliance requirements?"
                ]
            )
        
        # This would integrate with the analyzer for full compliance checking
        return ZeusResponse(
            query_type=QueryType.COMPLIANCE,
            answer="Compliance checking requires detailed pole inspection data. "
                   "Use the pole analyzer for comprehensive compliance analysis.",
            suggestions=[
                "Learn about compliance requirements",
                "What makes a pole compliant?",
                "Get pole specifications"
            ]
        )
    
    def _handle_general(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle general questions"""
        return ZeusResponse(
            query_type=QueryType.GENERAL,
            answer="I'm Zeus, your ANSI O5.1-2022 expert. I can help you with:\n\n"
                   "• Pole specifications and dimensions\n"
                   "• Load capacity calculations\n"
                   "• Pole class comparisons\n"
                   "• Recommendations for your requirements\n"
                   "• Compliance checking\n"
                   "• Engineering calculations\n\n"
                   "What would you like to know?",
            suggestions=[
                "What are the pole classes?",
                "Get specifications for H1 40ft",
                "Recommend a pole for 12,000 lbs at 45ft",
                "Compare poles at 40ft",
                "Explain fiber stress"
            ]
        )
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get Zeus's capabilities"""
        return {
            "specifications": [
                "Look up pole specifications by class and length",
                "Get dimensional requirements",
                "Find load capacities",
                "List available pole classes and lengths"
            ],
            "comparisons": [
                "Compare different pole classes",
                "Analyze capacity differences",
                "Evaluate dimensional variations"
            ],
            "recommendations": [
                "Recommend appropriate pole class for load requirements",
                "Suggest alternatives",
                "Optimize pole selection"
            ],
            "calculations": [
                "Calculate bending moments",
                "Compute fiber stress",
                "Analyze decay effects",
                "Calculate wind and ice loads",
                "Determine embedment depth"
            ],
            "explanations": [
                "Explain ANSI O5.1-2022 concepts",
                "Describe pole classes",
                "Clarify specifications",
                "Provide best practices"
            ],
            "compliance": [
                "Check pole compliance",
                "Identify issues",
                "Provide recommendations"
            ]
        }

# Made with Bob
