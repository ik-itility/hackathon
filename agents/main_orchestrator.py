"""Main Orchestrator: Connects File Monitor and DRC Agent"""
import sys
sys.path.append('/workshop/hackathon/agents')
from file_monitor_agent import FileMonitorAgent
from drc_agent import DRCAgent

class DRCOrchestrator:
    def __init__(self, watch_folder: str, rules_path: str, output_dir: str):
        self.file_monitor = FileMonitorAgent(watch_folder)
        self.drc_agent = DRCAgent(rules_path, output_dir)
    
    def process_new_file(self, filepath: str):
        """Callback when new file is detected"""
        try:
            result = self.drc_agent.process_gds(filepath)
            return result
        except Exception as e:
            print(f"[Orchestrator] Error processing {filepath}: {e}")
            return None
    
    def start(self):
        """Start watching for new files"""
        print("="*70)
        print("PHOTONICS GDS DRC SYSTEM")
        print("="*70)
        print("Agent 1: File Monitor - Watching for new GDS files")
        print("Agent 2: DRC Agent - Running checks and generating reports")
        print("="*70)
        
        self.file_monitor.watch(self.process_new_file, interval=2)

if __name__ == '__main__':
    orchestrator = DRCOrchestrator(
        watch_folder='/workshop/hackathon/gds-files',
        rules_path='/workshop/hackathon/data/rules_config.yaml',
        output_dir='/workshop/hackathon/output'
    )
    
    orchestrator.start()
