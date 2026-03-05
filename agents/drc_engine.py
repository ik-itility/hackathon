"""DRC Engine using KLayout Region checks"""
import klayout.db as db
import yaml

class DRCEngine:
    def __init__(self, gds_reader, rules_path: str):
        self.reader = gds_reader
        self.rules = self._load_rules(rules_path)
    
    def _load_rules(self, path: str) -> list:
        with open(path) as f:
            config = yaml.safe_load(f)
        return config['rules']
    
    def run_checks(self) -> list:
        """Run all DRC checks and return violations"""
        violations = []
        
        for rule in self.rules:
            if rule['check'] in ['width', 'space', 'area']:
                violations.extend(self._check_single_layer(rule))
            elif rule['check'] == 'separation':
                violations.extend(self._check_two_layers(rule))
        
        return violations
    
    def _check_single_layer(self, rule: dict) -> list:
        """Check rules on a single layer"""
        layer, datatype = rule['layer']
        region = self.reader.get_layer_region(layer, datatype)
        
        violations = []
        
        if rule['check'] == 'width':
            errs = region.width_check(rule['min_value_nm'])
            if errs.count() > 0:
                violations.append({
                    'rule': rule['name'],
                    'description': rule['description'],
                    'layer': f"{layer}/{datatype}",
                    'count': errs.count(),
                    'severity': 'CRITICAL',
                    'locations': self._extract_locations(errs, 5)
                })
        
        elif rule['check'] == 'space':
            errs = region.space_check(rule['min_value_nm'])
            if errs.count() > 0:
                violations.append({
                    'rule': rule['name'],
                    'description': rule['description'],
                    'layer': f"{layer}/{datatype}",
                    'count': errs.count(),
                    'severity': 'WARNING',
                    'locations': self._extract_locations(errs, 5)
                })
        
        return violations
    
    def _check_two_layers(self, rule: dict) -> list:
        """Check rules between two layers"""
        layer_a = self.reader.get_layer_region(*rule['layer_a'])
        layer_b = self.reader.get_layer_region(*rule['layer_b'])
        
        violations = []
        
        if rule['check'] == 'separation':
            errs = layer_a.separation_check(layer_b, rule['min_value_nm'])
            if errs.count() > 0:
                violations.append({
                    'rule': rule['name'],
                    'description': rule['description'],
                    'layers': f"{rule['layer_a']} vs {rule['layer_b']}",
                    'count': errs.count(),
                    'severity': 'WARNING',
                    'locations': self._extract_locations(errs, 5)
                })
        
        return violations
    
    def _extract_locations(self, edge_pairs, limit: int = 5) -> list:
        """Extract violation locations from EdgePairs"""
        locations = []
        count = 0
        for ep in edge_pairs.each():
            if count >= limit:
                break
            locations.append({
                'x': ep.first.p1.x * self.reader.dbu,
                'y': ep.first.p1.y * self.reader.dbu
            })
            count += 1
        return locations
