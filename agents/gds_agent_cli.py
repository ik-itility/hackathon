#!/usr/bin/env python3
"""GDS Validation Agent CLI - Interactive agent for photonics mask validation"""

import argparse
import json
import sys
from pathlib import Path
import boto3

# Parse GDS to JSON
def parse_gds_to_json(gds_file: str) -> dict:
    """Parse GDS file using gds_parser and return JSON"""
    import subprocess
    result = subprocess.run(
        ['python', '/workshop/gds_parser.py', gds_file, '--summary-only'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# Validate JSON against rules
def validate_json(gds_json: dict, rules_file: str = '/workshop/data/rules.txt') -> dict:
    """Validate parsed GDS JSON against design rules"""
    rules = {
        'min_spacing': 0.20, 'min_feature_size': 0.10,
        'min_waveguide_width': 0.45, 'max_waveguide_width': 2.0,
        'min_waveguide_spacing': 0.30, 'min_ring_radius': 5.0,
        'min_bend_radius': 10.0, 'min_angle': 135.0,
    }
    
    errors = []
    for cell_name, cell_data in gds_json.get('cells', {}).items():
        geom = cell_data.get('geometry', {})
        
        # Check layer stats
        for layer_key, stats in geom.get('layer_stats', {}).items():
            if stats['total_area_um2'] < rules['min_feature_size'] ** 2:
                errors.append(f"Cell '{cell_name}' layer {layer_key}: Feature too small")
        
        # Check paths
        for path in geom.get('paths_summary', []):
            for width in path.get('widths', []):
                if width < rules['min_waveguide_width']:
                    errors.append(f"Cell '{cell_name}': Width {width:.3f} µm < min {rules['min_waveguide_width']} µm")
                if width > rules['max_waveguide_width']:
                    errors.append(f"Cell '{cell_name}': Width {width:.3f} µm > max {rules['max_waveguide_width']} µm")
    
    return {'valid': len(errors) == 0, 'errors': errors}

# Generate fixes using Bedrock
def generate_fixes(gds_json: dict, errors: list) -> str:
    """Use AWS Bedrock to generate fix recommendations"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    prompt = f"""Photonics mask design expert: Fix these violations:

Errors:
{chr(10).join(f"- {e}" for e in errors)}

GDS Summary:
{json.dumps(gds_json.get('summary', {}), indent=2)}

Provide specific fixes with coordinates and justification."""

    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-sonnet-4-5-v2:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 2000,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    return json.loads(response['body'].read())['content'][0]['text']

# CLI Agent Loop
def run_agent_cli(gds_file: str):
    """Interactive CLI agent"""
    print(f"\n🔍 Parsing GDS file: {gds_file}")
    gds_json = parse_gds_to_json(gds_file)
    
    print(f"✓ Parsed {len(gds_json.get('cells', {}))} cells")
    
    while True:
        print("\n" + "="*60)
        print("GDS Validation Agent - What would you like to do?")
        print("="*60)
        print("1. Validate design rules")
        print("2. Show GDS summary")
        print("3. Generate fix recommendations")
        print("4. Export JSON")
        print("5. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            print("\n🔍 Validating design rules...")
            result = validate_json(gds_json)
            if result['valid']:
                print("✓ All design rules passed!")
            else:
                print(f"✗ Found {len(result['errors'])} violations:")
                for err in result['errors']:
                    print(f"  - {err}")
        
        elif choice == '2':
            print("\n📊 GDS Summary:")
            print(json.dumps(gds_json.get('summary', {}), indent=2))
        
        elif choice == '3':
            result = validate_json(gds_json)
            if result['valid']:
                print("✓ No errors to fix!")
            else:
                print("\n🤖 Generating fixes with AI...")
                fixes = generate_fixes(gds_json, result['errors'])
                print(f"\n{fixes}")
        
        elif choice == '4':
            out = Path(gds_file).stem + '_parsed.json'
            Path(out).write_text(json.dumps(gds_json, indent=2))
            print(f"✓ Exported to {out}")
        
        elif choice == '5':
            print("Goodbye!")
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GDS Validation Agent CLI')
    parser.add_argument('gds_file', help='Path to GDS file')
    args = parser.parse_args()
    
    run_agent_cli(args.gds_file)
