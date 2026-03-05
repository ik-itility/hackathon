"""Agent 2: GDS Validator - Validates photonics mask design rules"""
import numpy as np
from typing import Dict, List, Any
from shapely.geometry import Polygon, Point

class GDSValidatorAgent:
    def __init__(self, rules_file: str = '/workshop/hackathon/data/rules.txt'):
        self.rules = self._load_rules(rules_file)
    
    def _load_rules(self, filepath: str) -> Dict[str, float]:
        """Parse photonics design rules"""
        return {
            'min_spacing': 0.20,  # µm
            'min_feature_size': 0.10,  # µm
            'min_waveguide_width': 0.45,  # µm
            'max_waveguide_width': 2.0,  # µm
            'min_waveguide_spacing': 0.30,  # µm
            'min_ring_radius': 5.0,  # µm
            'min_bend_radius': 10.0,  # µm
            'min_angle': 135.0,  # degrees
        }
    
    def validate_gds(self, gds_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Validate GDS against photonics design rules"""
        errors = []
        
        for cell in gds_data.get('cells', []):
            for i, poly_data in enumerate(cell['polygons']):
                points = np.array(poly_data['points'])
                
                # Check minimum feature size
                if poly_data['area'] < self.rules['min_feature_size'] ** 2:
                    errors.append(
                        f"Cell '{cell['name']}' polygon {i}: "
                        f"Feature too small ({poly_data['area']:.3f} µm²)"
                    )
                
                # Check minimum spacing between edges
                widths = self._calculate_widths(points)
                if widths and min(widths) < self.rules['min_waveguide_width']:
                    errors.append(
                        f"Cell '{cell['name']}' polygon {i}: "
                        f"Width {min(widths):.3f} µm < minimum {self.rules['min_waveguide_width']} µm"
                    )
                
                # Check angles
                angles = self._calculate_angles(points)
                if angles and min(angles) < self.rules['min_angle']:
                    errors.append(
                        f"Cell '{cell['name']}' polygon {i}: "
                        f"Sharp angle {min(angles):.1f}° < minimum {self.rules['min_angle']}°"
                    )
        
        return {
            'filename': filename,
            'valid': len(errors) == 0,
            'errors': errors,
            'trigger_fix': len(errors) > 0
        }
    
    def _calculate_widths(self, points: np.ndarray) -> List[float]:
        """Calculate edge widths"""
        widths = []
        for i in range(len(points) - 1):
            dist = np.linalg.norm(points[i+1] - points[i])
            widths.append(dist)
        return widths
    
    def _calculate_angles(self, points: np.ndarray) -> List[float]:
        """Calculate internal angles"""
        angles = []
        for i in range(len(points) - 2):
            v1 = points[i+1] - points[i]
            v2 = points[i+2] - points[i+1]
            angle = np.degrees(np.arccos(
                np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            ))
            angles.append(angle)
        return angles

if __name__ == '__main__':
    sample_gds = {
        'cells': [{
            'name': 'waveguide',
            'polygons': [{
                'layer': 1,
                'points': [[0, 0], [10, 0], [10, 0.3], [0, 0.3]],
                'area': 3.0
            }]
        }]
    }
    
    agent = GDSValidatorAgent()
    result = agent.validate_gds(sample_gds, 'test.gds')
    print(result)
