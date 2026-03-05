"""Format DRC results into structured reports"""
import json
from datetime import datetime

class ReportFormatter:
    @staticmethod
    def to_json(violations: list, gds_path: str) -> dict:
        """Format violations as JSON"""
        return {
            'file': gds_path,
            'timestamp': datetime.now().isoformat(),
            'total_violations': sum(v['count'] for v in violations),
            'violations': violations
        }
    
    @staticmethod
    def to_text(violations: list, gds_path: str) -> str:
        """Format violations as human-readable text"""
        lines = []
        lines.append("="*60)
        lines.append("PHOTONICS GDS DRC REPORT")
        lines.append("="*60)
        lines.append(f"\nFile: {gds_path}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\nTotal Violations: {sum(v['count'] for v in violations)}\n")
        
        if not violations:
            lines.append("✓ No violations found - design passes all rules!")
        else:
            lines.append("VIOLATIONS:\n" + "-"*60)
            for v in violations:
                lines.append(f"\n[{v['severity']}] {v['rule']}")
                lines.append(f"  Description: {v['description']}")
                lines.append(f"  Layer: {v.get('layer', v.get('layers', 'N/A'))}")
                lines.append(f"  Count: {v['count']}")
                if v.get('locations'):
                    lines.append(f"  Sample locations:")
                    for loc in v['locations'][:3]:
                        lines.append(f"    - ({loc['x']:.3f}, {loc['y']:.3f}) µm")
        
        return '\n'.join(lines)
    
    @staticmethod
    def save_reports(violations: list, gds_path: str, output_dir: str):
        """Save both JSON and text reports"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        basename = os.path.basename(gds_path).replace('.gds', '')
        
        # JSON report
        json_path = os.path.join(output_dir, f"{basename}_drc_report.json")
        with open(json_path, 'w') as f:
            json.dump(ReportFormatter.to_json(violations, gds_path), f, indent=2)
        
        # Text report
        txt_path = os.path.join(output_dir, f"{basename}_drc_report.txt")
        with open(txt_path, 'w') as f:
            f.write(ReportFormatter.to_text(violations, gds_path))
        
        return json_path, txt_path
