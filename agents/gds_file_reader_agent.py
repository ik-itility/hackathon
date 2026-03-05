"""Agent 1: GDS File Reader - Reads GDSII photonics mask files from S3"""
import boto3
import gdstk
import tempfile
import os
from typing import Dict, Any

class GDSFileReaderAgent:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def process_s3_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process S3 event and read GDS file"""
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        if not key.endswith('.gds'):
            return {'status': 'skipped', 'reason': 'Not a GDS file'}
        
        # Handle local files (bucket == 'local')
        if bucket == 'local':
            return self._read_local_file(key)
        
        # Download GDS file from S3 to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gds') as tmp:
            self.s3_client.download_fileobj(bucket, key, tmp)
            tmp_path = tmp.name
        
        try:
            return self._read_gds_file(tmp_path, bucket, key)
        finally:
            os.unlink(tmp_path)
    
    def _read_local_file(self, filepath: str) -> Dict[str, Any]:
        """Read GDS file from local filesystem"""
        return self._read_gds_file(filepath, 'local', filepath)
    
    def _read_gds_file(self, tmp_path: str, bucket: str, key: str) -> Dict[str, Any]:
        """Read and parse GDS file"""
        # Read GDS file
        library = gdstk.read_gds(tmp_path)
        
        # Extract all cells and polygons
        cells_data = []
        for cell in library.cells:
            polygons = []
            for polygon in cell.polygons:
                polygons.append({
                    'layer': polygon.layer,
                    'points': polygon.points.tolist(),
                    'area': polygon.area()
                })
            
            cells_data.append({
                'name': cell.name,
                'polygon_count': len(polygons),
                'polygons': polygons
            })
        
        return {
            'status': 'success',
            'bucket': bucket,
            'key': key,
            'library_name': library.name,
            'cells': cells_data,
            'trigger_validation': True
        }

if __name__ == '__main__':
    sample_event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'photonics-mask-bucket'},
                'object': {'key': 'uploads/design.gds'}
            }
        }]
    }
    
    agent = GDSFileReaderAgent()
    result = agent.process_s3_event(sample_event)
    print(f"Read {len(result.get('cells', []))} cells from GDS")
