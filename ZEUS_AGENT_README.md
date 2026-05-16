# Zeus AI Agent - ANSI O5.1-2023 Expert

Zeus is an intelligent conversational AI agent that understands and explains ANSI O5.1-2023 Wood Poles, Specifications and Dimensions. He can answer questions, provide recommendations, perform calculations, and help users understand utility pole standards.

## Overview

Zeus provides:
- **Natural language understanding** of pole-related questions
- **Intelligent responses** with context-aware answers
- **Specifications lookup** for any pole class and length
- **Engineering calculations** for loads, decay, and more
- **Recommendations** for pole selection
- **Comparisons** between different pole classes
- **Explanations** of ANSI O5.1-2023 concepts

## Features

### 1. Conversational Interface
Ask Zeus questions in natural language:
- "What are the specifications for H1 40ft?"
- "Recommend a pole for 12,000 lbs at 45ft"
- "Explain fiber stress"
- "Compare poles at 40ft"

### 2. Query Types
Zeus handles multiple types of queries:
- **Specification Lookup**: Get detailed pole specifications
- **Comparison**: Compare different pole classes
- **Recommendation**: Get pole suggestions for requirements
- **Calculation**: Perform engineering calculations
- **Explanation**: Learn about ANSI O5.1-2023 concepts
- **Compliance**: Check pole compliance (via analyzer integration)

### 3. Context Awareness
Zeus maintains context and provides relevant suggestions for follow-up questions.

## Installation

Zeus is part of the pole analyzer system. No additional installation required beyond the main system dependencies.

## Usage

### 1. Basic Usage

```python
from backend.zeus_agent import ZeusAgent

# Initialize Zeus
zeus = ZeusAgent()

# Ask a question
response = zeus.ask("What are the specifications for H1 40ft?")

print(response.answer)
print(f"Confidence: {response.confidence}")

# Follow-up with suggestions
if response.suggestions:
    print("\nSuggestions:")
    for suggestion in response.suggestions:
        print(f"  - {suggestion}")
```

### 2. With Context

```python
# Provide context for more specific answers
context = {
    "pole_class": "H1",
    "length_ft": 40,
    "required_load_lbs": 12000
}

response = zeus.ask("Is this pole suitable?", context)
print(response.answer)
```

### 3. Different Query Types

#### Specification Lookup
```python
response = zeus.ask("Show me H1 40ft specifications")
# Returns detailed specs with dimensions and capacity
```

#### Comparison
```python
response = zeus.ask("Compare poles at 40ft")
# Returns comparison table of all classes at 40ft
```

#### Recommendation
```python
response = zeus.ask("Recommend a pole for 15,000 lbs at 45ft")
# Returns recommended pole class with safety margins
```

#### Calculation
```python
context = {"load_lbs": 10000, "height_ft": 30}
response = zeus.ask("Calculate bending moment", context)
# Returns calculated moment with explanation
```

#### Explanation
```python
response = zeus.ask("Explain fiber stress")
# Returns detailed explanation of the concept
```

## API Endpoints

### Start the API Server

```python
from fastapi import FastAPI
from backend.zeus_api import router

app = FastAPI(title="Zeus AI Agent")
app.include_router(router)

# Run with: uvicorn main:app --reload
```

### Available Endpoints

#### 1. Ask Zeus
```http
POST /api/zeus/ask
Content-Type: application/json

{
  "question": "What are the specifications for H1 40ft?",
  "context": {
    "pole_class": "H1",
    "length_ft": 40
  }
}
```

Response:
```json
{
  "query_type": "specification_lookup",
  "answer": "**H1 Class Pole - 40ft**\n\n**Dimensions:**\n...",
  "data": {
    "pole_class": "H1",
    "length_ft": 40,
    "capacity_lbs": 14000,
    ...
  },
  "suggestions": [
    "Compare H1 with other classes at 40ft",
    "Calculate loads for this pole"
  ],
  "confidence": 0.9
}
```

#### 2. Get Capabilities
```http
GET /api/zeus/capabilities
```

#### 3. Quick Specification Lookup
```http
POST /api/zeus/specification?pole_class=H1&length_ft=40
```

#### 4. Get Recommendation
```http
POST /api/zeus/recommend?required_load_lbs=12000&length_ft=45
```

#### 5. Compare Poles
```http
POST /api/zeus/compare?length_ft=40
```

#### 6. Calculate Bending Moment
```http
POST /api/zeus/calculate/bending-moment?load_lbs=10000&height_ft=30
```

#### 7. Calculate Decay Strength
```http
POST /api/zeus/calculate/decay-strength?diameter_inches=11&decay_depth_inches=1.5
```

#### 8. Explain Concept
```http
POST /api/zeus/explain?topic=fiber%20stress
```

#### 9. Get Examples
```http
GET /api/zeus/examples
```

#### 10. Conversation Mode
```http
POST /api/zeus/conversation
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "What are H-class poles?"},
    {"role": "zeus", "content": "...", "data": {...}},
    {"role": "user", "content": "Show me H1 specifications"}
  ]
}
```

## Zeus's Knowledge Base

Zeus has deep knowledge of:

### ANSI O5.1-2023 Standard
- Complete understanding of the standard
- All pole classes and their specifications
- Load capacity requirements
- Dimensional requirements

### Pole Classes
- H-Class poles (H6 through H1)
- Standard classes (1 through 7)
- Available lengths for each class
- Capacity ranges

### Technical Concepts
- Fiber stress (8000 psi standard)
- Load application (2 feet from top)
- Groundline definition (6 feet from butt)
- Circumference vs diameter
- Safety factors
- Decay effects
- Embedment requirements

### Wood Species
- Southern Pine
- Douglas Fir
- Western Red Cedar
- Northern White Cedar
- Treatment types and methods

### Engineering Calculations
- Bending moments
- Fiber stress
- Section modulus
- Decay strength reduction
- Wind and ice loads
- Embedment depth

## Example Conversations

### Example 1: Specification Inquiry
```
User: "What are the specs for H1 40ft?"

Zeus: "**H1 Class Pole - 40ft**

**Dimensions:**
- Minimum top circumference: 15.0" (4.77" diameter)
- Minimum groundline circumference: 34.5" (10.99" diameter)

**Capacity:**
- Horizontal load capacity: 14,000 lbs (at 2 feet from top)
- Fiber stress: 8,000 psi

**Application:**
This pole can support 14,000 lbs of horizontal load applied 2 feet 
from the top, with a fiber stress of 8,000 psi at the groundline."

Suggestions:
- Compare H1 with other classes at 40ft
- Calculate loads for this pole
- Check if this pole meets your requirements
```

### Example 2: Recommendation Request
```
User: "I need a pole for 12,000 lbs at 45ft"

Zeus: "**Pole Recommendation**

**Requirements:**
- Required load: 12,000 lbs
- Pole length: 45 ft
- Design load (with safety factor 1.5): 18,000 lbs

**Recommended Pole:**
- Class: **H1**
- Rated capacity: 12,700 lbs
- Safety margin: -5,300 lbs (-41.7%)

Wait, this doesn't meet requirements. Let me recommend Class 2:

**Recommended Pole:**
- Class: **2**
- Rated capacity: 24,300 lbs
- Safety margin: 6,300 lbs (25.9%)

This pole provides adequate capacity with a 25.9% safety margin."
```

### Example 3: Comparison
```
User: "Compare poles at 40ft"

Zeus: "**Pole Class Comparison at 40ft**

| Class | Capacity (lbs) | Top Circ (in) | Groundline Circ (in) |
|-------|----------------|---------------|----------------------|
| 1     |         33,200 |          27.0 |                 43.5 |
| 2     |         26,700 |          25.0 |                 39.5 |
| 3     |         21,300 |          23.0 |                 36.0 |
| H1    |         14,000 |          15.0 |                 34.5 |
| H2    |         12,600 |          15.0 |                 33.0 |
...

**Analysis:**
- Strongest: 1 (33,200 lbs)
- Lightest: 7 (6,700 lbs)
- Capacity range: 6,700 - 33,200 lbs"
```

### Example 4: Explanation
```
User: "Explain fiber stress"

Zeus: "The standard uses 8000 psi as the allowable fiber stress for 
most wood species. This is the maximum stress allowed at the extreme 
fiber of the pole under design loads.

Fiber stress is the tensile or compressive stress in the outermost 
fibers of the pole when it bends under load. The 8000 psi value 
represents a safe working stress that accounts for:
- Wood species strength characteristics
- Load duration
- Safety factors
- Environmental conditions

This standardized value allows for consistent pole design across 
different applications and wood species."
```

### Example 5: Calculation
```
User: "Calculate bending moment for 10,000 lbs at 30ft"

Zeus: "**Bending Moment Calculation**

Load: 10,000 lbs
Height: 30 ft

**Bending Moment: 300,000 ft-lbs**

This is the moment at the base caused by the horizontal load 
applied at the specified height.

To verify if a pole can handle this:
1. Calculate section modulus from pole diameter
2. Compute fiber stress = Moment / Section Modulus
3. Compare to allowable stress (8000 psi)"
```

## Zeus's Capabilities

```python
capabilities = zeus.get_capabilities()

# Returns:
{
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
        "Explain ANSI O5.1-2023 concepts",
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
```

## Integration with Pole Analyzer

Zeus integrates seamlessly with the Pole Analyzer:

```python
from backend.zeus_agent import ZeusAgent
from backend.pole_analyzer_agent import PoleAnalyzerAgent, PoleInspectionData

zeus = ZeusAgent()
analyzer = PoleAnalyzerAgent()

# Get recommendation from Zeus
response = zeus.ask("Recommend a pole for 12,000 lbs at 45ft")

# Use analyzer for detailed compliance check
inspection = PoleInspectionData(
    pole_id="POLE-001",
    pole_class=response.data["recommended_class"],
    length_ft=45,
    # ... other measurements
)

result = analyzer.analyze_pole(inspection)
```

## Best Practices

1. **Be Specific**: Provide pole class and length for accurate responses
2. **Use Context**: Include relevant data in context parameter
3. **Follow Suggestions**: Zeus provides helpful follow-up suggestions
4. **Check Confidence**: Lower confidence may indicate ambiguous questions
5. **Iterate**: Use conversation mode for complex inquiries

## Response Format

All Zeus responses include:
- **query_type**: Type of query handled
- **answer**: Formatted answer text (supports markdown)
- **data**: Structured data (specifications, calculations, etc.)
- **suggestions**: Follow-up question suggestions
- **confidence**: Confidence score (0.0 to 1.0)

## Error Handling

Zeus handles various scenarios gracefully:
- Invalid pole classes → Suggests valid options
- Missing information → Asks for clarification
- Ambiguous questions → Provides general guidance
- Calculation errors → Explains requirements

## Performance

- **Response Time**: < 100ms for most queries
- **Accuracy**: Based on ANSI O5.1-2023 specifications
- **Coverage**: All pole classes and lengths in standard

## Limitations

- Zeus provides guidance based on ANSI O5.1-2023
- Always consult licensed engineers for critical decisions
- Local codes and regulations may have additional requirements
- Environmental factors may require adjustments

## Future Enhancements

Potential improvements:
- Multi-language support
- Voice interface
- Image analysis for pole inspection
- Integration with GIS systems
- Historical data analysis
- Predictive maintenance recommendations

## Support

For questions about Zeus:
1. Check example conversations above
2. Review ANSI O5.1-2023 documentation
3. Test with example questions from `/api/zeus/examples`

## License

Zeus is part of the ANSI O5.1-2023 Pole Analyzer system.
Always consult with licensed professional engineers for critical infrastructure decisions.

---

**Zeus**: "I'm here to help you understand and work with ANSI O5.1-2023 Wood Poles specifications. Ask me anything!"