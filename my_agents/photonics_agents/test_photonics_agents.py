#!/usr/bin/env python3
"""
Test script for Photonics IC Design Agents
"""

from orchestrator_agent import DRCOrchestrator
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_photonics_agents.py <nazca_file.py> [drc_script.drc]")
        print("\nExample:")
        print("  python test_photonics_agents.py /shared_workshop/hackathon/nazca-scripts/Laser-with-errors.py")
        sys.exit(1)
    
    nazca_file = sys.argv[1]
    drc_script = sys.argv[2] if len(sys.argv) > 2 else "example_drc.drc"
    
    if not os.path.exists(nazca_file):
        print(f"Error: Nazca file not found: {nazca_file}")
        sys.exit(1)
    
    if not os.path.exists(drc_script):
        print(f"Warning: DRC script not found: {drc_script}")
        print("Using example DRC script")
        drc_script = os.path.join(os.path.dirname(__file__), "example_drc.drc")
    
    print("="*80)
    print("Photonics IC Design - Automated DRC Fixing")
    print("="*80)
    print(f"Nazca File: {nazca_file}")
    print(f"DRC Script: {drc_script}")
    print("="*80)
    
    orchestrator = DRCOrchestrator(max_iterations=10)
    orchestrator.process(nazca_file, drc_script)
    
    print("\n" + "="*80)
    print("Process Complete")
    print("="*80)

if __name__ == "__main__":
    main()
