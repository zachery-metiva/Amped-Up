"""
MVI-Zeus Integration Service
Complete workflow for pole inspection using MVI + Zeus
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from backend.mvi_connector import MVIConnector
from backend.zeus_agent import ZeusAgent


class MVIZeusIntegration:
    """
    Integration service combining MVI visual inspection with Zeus analysis
    
    Provides complete pole inspection workflow:
    1. Image capture/upload
    2. MVI visual defect detection
    3. Zeus standards compliance analysis
    4. Work order generation
    5. Maximo integration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize integration service
        
        Args:
            config: Configuration dictionary with MVI/Maximo credentials
        """
        self.config = config or self._load_config()
        self.mvi_connector = MVIConnector(
            mvi_url=self.config.get("mvi_url"),
            api_key=self.config.get("mvi_api_key")
        )
        self.zeus = ZeusAgent()
    
    def _load_config(self) -> Dict:
        """Load configuration from environment or config file"""
        config_file = Path("config/mvi_config.json")
        
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        
        # Fallback to environment variables
        return {
            "mvi_url": os.getenv("MVI_URL"),
            "mvi_api_key": os.getenv("MVI_API_KEY"),
            "maximo_url": os.getenv("MAXIMO_URL"),
            "maximo_api_key": os.getenv("MAXIMO_API_KEY")
        }
    
    def inspect_pole(self, image_path: str, pole_id: Optional[str] = None,
                     send_to_maximo: bool = False) -> Dict:
        """
        Complete pole inspection workflow
        
        Args:
            image_path: Path to pole image
            pole_id: Optional pole identifier
            send_to_maximo: Whether to send work order to Maximo
            
        Returns:
            Complete inspection results
        """
        print("=" * 80)
        print("MVI-ZEUS INTEGRATED POLE INSPECTION")
        print("=" * 80)
        print(f"\nImage: {image_path}")
        print(f"Pole ID: {pole_id or 'Auto-generated'}")
        print(f"\nStarting analysis...")
        
        # Run MVI + Zeus analysis
        results = self.mvi_connector.analyze_pole_image(image_path, pole_id)
        
        # Print results
        self._print_results(results)
        
        # Send to Maximo if requested
        if send_to_maximo:
            print("\n" + "=" * 80)
            print("SENDING TO MAXIMO")
            print("=" * 80)
            maximo_response = self.mvi_connector.send_to_maximo(
                results["work_order"],
                self.config.get("maximo_url"),
                self.config.get("maximo_api_key")
            )
            results["maximo_response"] = maximo_response
            print(f"Status: {maximo_response.get('status', 'unknown')}")
        
        # Save results
        self._save_results(results)
        
        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE")
        print("=" * 80)
        
        return results
    
    def inspect_multiple_poles(self, image_folder: str, 
                              send_to_maximo: bool = False) -> List[Dict]:
        """
        Inspect multiple poles from a folder
        
        Args:
            image_folder: Folder containing pole images
            send_to_maximo: Whether to send work orders to Maximo
            
        Returns:
            List of inspection results
        """
        print("=" * 80)
        print("BATCH POLE INSPECTION")
        print("=" * 80)
        print(f"\nFolder: {image_folder}")
        
        # Get image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if Path(f).suffix.lower() in image_extensions
        ]
        
        print(f"Found {len(image_files)} images\n")
        
        # Process each image
        all_results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing {Path(image_path).name}")
            results = self.inspect_pole(image_path, send_to_maximo=send_to_maximo)
            all_results.append(results)
        
        # Generate batch summary
        summary = self._generate_batch_summary(all_results)
        
        print("\n" + "=" * 80)
        print("BATCH SUMMARY")
        print("=" * 80)
        print(f"\nTotal poles inspected: {len(all_results)}")
        print(f"Total defects found: {summary['total_defects']}")
        print(f"Critical issues: {summary['critical_count']}")
        print(f"Serious issues: {summary['serious_count']}")
        print(f"Poles requiring immediate action: {summary['immediate_action_count']}")
        
        return all_results
    
    def _print_results(self, results: Dict):
        """Print inspection results to console"""
        print("\n" + "=" * 80)
        print("MVI DETECTION RESULTS")
        print("=" * 80)
        
        mvi_detections = results["mvi_detections"].get("classified", [])
        print(f"\nDetections: {len(mvi_detections)}")
        for detection in mvi_detections:
            print(f"  • {detection['label']}: {detection['confidence']:.1%} confidence")
        
        print("\n" + "=" * 80)
        print("ZEUS ANALYSIS")
        print("=" * 80)
        
        zeus_analysis = results["zeus_analysis"]
        print(f"\nDefects analyzed: {len(zeus_analysis['defects'])}")
        
        print("\nSeverity Summary:")
        for severity, count in zeus_analysis["severity_summary"].items():
            if count > 0:
                print(f"  • {severity.replace('_', ' ').title()}: {count}")
        
        print("\nPriority Actions:")
        for action in zeus_analysis["priority_actions"]:
            print(f"  {action}")
        
        if zeus_analysis["compliance_issues"]:
            print(f"\nCompliance Issues: {len(zeus_analysis['compliance_issues'])}")
            for issue in zeus_analysis["compliance_issues"]:
                print(f"  • {issue['defect']} [{issue['severity']}]")
        
        print("\n" + "=" * 80)
        print("WORK ORDER")
        print("=" * 80)
        
        wo = results["work_order"]
        print(f"\nWork Order: {wo['wonum']}")
        print(f"Priority: {wo['priority']} ({'Critical' if wo['priority'] == 1 else 'High' if wo['priority'] == 2 else 'Medium' if wo['priority'] == 3 else 'Low'})")
        print(f"Estimated Hours: {wo['estimated_hours']}")
        print(f"Required Skills: {', '.join(wo['required_skills'])}")
        print(f"\nDescription: {wo['description']}")
    
    def _save_results(self, results: Dict):
        """Save inspection results to file"""
        output_dir = Path("out/mvi_zeus_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pole_id = results["pole_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = output_dir / f"{pole_id}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save text report
        txt_file = output_dir / f"{pole_id}_{timestamp}_report.txt"
        with open(txt_file, 'w') as f:
            self._write_text_report(f, results)
        
        print(f"\nResults saved to: {output_dir}")
    
    def _write_text_report(self, f, results: Dict):
        """Write text report to file"""
        f.write("MVI-ZEUS INTEGRATED POLE INSPECTION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Pole ID: {results['pole_id']}\n")
        f.write(f"Image: {results['image_path']}\n")
        f.write(f"Timestamp: {results['timestamp']}\n\n")
        
        f.write("MVI DETECTIONS\n")
        f.write("-" * 80 + "\n")
        for detection in results["mvi_detections"].get("classified", []):
            f.write(f"• {detection['label']}: {detection['confidence']:.1%}\n")
        
        f.write("\n\nZEUS ANALYSIS\n")
        f.write("-" * 80 + "\n")
        
        for i, defect in enumerate(results["zeus_analysis"]["defects"], 1):
            zeus_info = defect["zeus_classification"]
            f.write(f"\n{i}. {zeus_info['name']} [{zeus_info['severity'].upper()}]\n")
            f.write(f"   Category: {zeus_info['category']}\n")
            f.write(f"   Description: {zeus_info['description']}\n")
            f.write(f"   Action: {zeus_info['corrective_action']}\n")
            f.write(f"   Standards: {zeus_info['nesc_reference']}\n")
        
        f.write("\n\nWORK ORDER\n")
        f.write("-" * 80 + "\n")
        wo = results["work_order"]
        f.write(f"Number: {wo['wonum']}\n")
        f.write(f"Priority: {wo['priority']}\n")
        f.write(f"Description: {wo['description']}\n")
        f.write(f"Estimated Hours: {wo['estimated_hours']}\n")
        f.write(f"Required Skills: {', '.join(wo['required_skills'])}\n")
    
    def _generate_batch_summary(self, all_results: List[Dict]) -> Dict:
        """Generate summary for batch inspection"""
        summary = {
            "total_poles": len(all_results),
            "total_defects": 0,
            "critical_count": 0,
            "serious_count": 0,
            "immediate_action_count": 0
        }
        
        for results in all_results:
            summary["total_defects"] += results["summary"]["total_defects"]
            summary["critical_count"] += results["summary"]["critical_count"]
            summary["serious_count"] += results["summary"]["serious_count"]
            if results["summary"]["requires_immediate_action"]:
                summary["immediate_action_count"] += 1
        
        return summary
    
    def get_zeus_insights(self, question: str) -> Dict:
        """
        Ask Zeus a question about pole standards
        
        Args:
            question: Question for Zeus
            
        Returns:
            Zeus response
        """
        response = self.zeus.ask(question)
        return {
            "question": question,
            "answer": response.answer,
            "query_type": response.query_type.value,
            "suggestions": response.suggestions,
            "confidence": response.confidence
        }


def main():
    """Example usage of MVI-Zeus integration"""
    integration = MVIZeusIntegration()
    
    # Inspect single pole
    results = integration.inspect_pole(
        "picture/20260516_171832.jpg",
        pole_id="POLE-001",
        send_to_maximo=False
    )
    
    # Ask Zeus for insights
    print("\n" + "=" * 80)
    print("ZEUS INSIGHTS")
    print("=" * 80)
    
    insights = integration.get_zeus_insights(
        "What are the requirements for transformer maintenance?"
    )
    print(f"\nQuestion: {insights['question']}")
    print(f"Answer: {insights['answer']}")


if __name__ == "__main__":
    main()


# Made with Bob