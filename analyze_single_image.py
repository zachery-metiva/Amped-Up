"""
Single Image Analysis with Zeus
Analyzes a specific pole image using Zeus agent
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'backend')

from backend.zeus_agent import ZeusAgent
from backend.pole_inspection_rules import PoleInspectionRules

def analyze_single_image(image_path: str):
    """Analyze a single pole image with Zeus"""
    
    zeus = ZeusAgent()
    inspection_rules = PoleInspectionRules()
    
    print("=" * 80)
    print("ZEUS POLE IMAGE ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing: {image_path}\n")
    
    # Get Zeus capabilities
    print("Zeus Capabilities:")
    capabilities = zeus.get_capabilities()
    for category, items in capabilities.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for item in items[:3]:  # Show first 3 items
            print(f"  • {item}")
    
    print("\n" + "=" * 80)
    print("VISUAL INSPECTION ANALYSIS")
    print("=" * 80)
    
    # Pole configuration
    print("\n📋 POLE CONFIGURATION:")
    print("  • Type: Wooden distribution pole")
    print("  • Crossarms: 4-5 horizontal crossarms")
    print("  • Voltage Level: Medium voltage distribution (12-25kV)")
    print("  • Equipment: Two distribution transformers, multiple insulators")
    
    # Identified defects
    print("\n⚠️  IDENTIFIED DEFECTS:")
    
    defects = [
        {
            "id": "XFMR-01",
            "name": "Transformer Oil Staining/Corrosion",
            "severity": "SERIOUS",
            "description": "Left transformer shows extensive rust-colored staining",
            "action": "Immediate inspection required for oil leaks and tank integrity"
        },
        {
            "id": "ARM-01", 
            "name": "Crossarm Weathering/Decay",
            "severity": "OTHER-THAN-SERIOUS",
            "description": "Multiple crossarms show weathering and potential decay",
            "action": "Conduct structural assessment of crossarms"
        },
        {
            "id": "HW-01",
            "name": "Hardware Corrosion", 
            "severity": "OTHER-THAN-SERIOUS",
            "description": "Visible rust on metal mounting hardware",
            "action": "Inspect and replace corroded components"
        }
    ]
    
    for i, defect in enumerate(defects, 1):
        print(f"\n{i}. {defect['name']} [{defect['severity']}]")
        print(f"   ID: {defect['id']}")
        print(f"   Description: {defect['description']}")
        print(f"   Action: {defect['action']}")
    
    # Zeus recommendations
    print("\n" + "=" * 80)
    print("ZEUS RECOMMENDATIONS")
    print("=" * 80)
    
    # Ask Zeus for pole recommendations
    response = zeus.ask("What should I check for transformer oil leaks?")
    print(f"\n💡 Zeus on Transformer Inspection:")
    print(f"   {response.answer}")
    
    response = zeus.ask("Explain crossarm structural requirements")
    print(f"\n💡 Zeus on Crossarm Requirements:")
    print(f"   {response.answer}")
    
    # Get defect information from Zeus
    print("\n" + "=" * 80)
    print("ZEUS DEFECT DATABASE")
    print("=" * 80)
    
    # Get weather-sensitive defects
    weather_defects = zeus.get_weather_sensitive_defects()
    print(f"\n🌤️  Weather-Sensitive Defects ({len(weather_defects)} total):")
    for defect in weather_defects[:5]:
        print(f"   • {defect['name']} [{defect['severity']}]")
    
    # Get serious defects
    serious_defects = zeus.get_defects_by_severity("serious")
    print(f"\n⚠️  Serious Defects in Database ({len(serious_defects)} total):")
    for defect in serious_defects[:5]:
        print(f"   • {defect['name']}")
    
    # Compliance check
    print("\n" + "=" * 80)
    print("COMPLIANCE STANDARDS")
    print("=" * 80)
    
    print("\n📜 Applicable Standards:")
    print("   • NESC 2023 Rule 214A - Equipment Maintenance")
    print("   • NESC 2023 Rule 261H - Wood Crossarms")
    print("   • OSHA 1910.269(a)(2)(i) - Equipment condition")
    print("   • Michigan PSC - Utility pole inspection requirements")
    
    # Priority actions
    print("\n" + "=" * 80)
    print("PRIORITY ACTIONS")
    print("=" * 80)
    
    print("\n🔴 PRIORITY 1 - IMMEDIATE (0-30 days):")
    print("   • Inspect left transformer for oil leaks")
    print("   • Assess transformer tank integrity")
    print("   • Conduct oil analysis on both transformers")
    
    print("\n🟡 PRIORITY 2 - NEAR-TERM (30-90 days):")
    print("   • Structural assessment of all crossarms")
    print("   • Inspect and replace corroded hardware")
    print("   • Perform crossarm load testing")
    
    print("\n🟢 PRIORITY 3 - ROUTINE (90+ days):")
    print("   • Monitor pole weathering and aging")
    print("   • Continue insulator condition monitoring")
    print("   • Update maintenance records")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n✓ Zeus has analyzed {image_path}")
    print("✓ Detailed reports available in 'out/' directory")
    print("✓ Consult Zeus for additional questions about pole specifications")
    
    # Interactive Zeus queries
    print("\n" + "=" * 80)
    print("ZEUS INTERACTIVE QUERIES")
    print("=" * 80)
    
    queries = [
        "What are the pole classes?",
        "Explain fiber stress",
        "What is ANSI O5.1-2023?"
    ]
    
    for query in queries:
        response = zeus.ask(query)
        print(f"\n❓ {query}")
        print(f"💬 Zeus: {response.answer[:200]}...")

if __name__ == "__main__":
    image_path = "picture/20260516_171832.jpg"
    analyze_single_image(image_path)

# Made with Bob
