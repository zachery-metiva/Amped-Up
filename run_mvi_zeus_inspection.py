#!/usr/bin/env python3
"""
MVI-Zeus Pole Inspection Workflow
Run integrated pole inspection using MVI + Zeus
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'backend')

from backend.mvi_zeus_integration import MVIZeusIntegration


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Run MVI-Zeus integrated pole inspection'
    )
    parser.add_argument(
        'image',
        help='Path to pole image or folder containing images'
    )
    parser.add_argument(
        '--pole-id',
        help='Pole identifier (optional)'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process all images in folder'
    )
    parser.add_argument(
        '--send-to-maximo',
        action='store_true',
        help='Send work order to Maximo'
    )
    
    args = parser.parse_args()
    
    # Initialize integration
    integration = MVIZeusIntegration()
    
    # Run inspection
    if args.batch:
        results = integration.inspect_multiple_poles(
            args.image,
            send_to_maximo=args.send_to_maximo
        )
        print(f"\n✓ Processed {len(results)} poles")
    else:
        results = integration.inspect_pole(
            args.image,
            pole_id=args.pole_id,
            send_to_maximo=args.send_to_maximo
        )
        print(f"\n✓ Inspection complete for {results['pole_id']}")
    
    print("\nResults saved to: out/mvi_zeus_results/")


if __name__ == "__main__":
    main()

# Made with Bob
