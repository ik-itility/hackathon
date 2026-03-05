"""GDS Reader using KLayout"""
import klayout.db as db

class GDSReader:
    def __init__(self, gds_path: str):
        self.layout = db.Layout()
        self.layout.read(gds_path)
        self.top_cell = self.layout.top_cell()
        self.dbu = self.layout.dbu  # database unit in microns
    
    def get_layer_region(self, layer: int, datatype: int = 0) -> db.Region:
        """Extract a layer as a Region for DRC operations"""
        layer_idx = self.layout.layer(layer, datatype)
        return db.Region(self.top_cell.begin_shapes_rec(layer_idx))
    
    def get_info(self) -> dict:
        """Get basic GDS file information"""
        return {
            'top_cell': self.top_cell.name,
            'dbu': self.dbu,
            'num_cells': len([c for c in self.layout.each_cell()]),
            'layers': [(li.layer, li.datatype) for li in self.layout.layer_infos()]
        }
