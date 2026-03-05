"""Agent 1: File Monitor - Watches for new GDS files"""
import time
import os
from pathlib import Path

class FileMonitorAgent:
    def __init__(self, watch_folder: str):
        self.watch_folder = watch_folder
        self.processed_files = set()
        
        # Load already processed files
        if os.path.exists(watch_folder):
            for f in os.listdir(watch_folder):
                if f.endswith('.gds'):
                    self.processed_files.add(f)
    
    def check_for_new_files(self):
        """Check for new GDS files"""
        new_files = []
        
        if not os.path.exists(self.watch_folder):
            return new_files
        
        for filename in os.listdir(self.watch_folder):
            if filename.endswith('.gds') and filename not in self.processed_files:
                filepath = os.path.join(self.watch_folder, filename)
                new_files.append(filepath)
                self.processed_files.add(filename)
                print(f"[FileMonitor] New file detected: {filename}")
        
        return new_files
    
    def watch(self, callback, interval=2):
        """Continuously watch for new files"""
        print(f"[FileMonitor] Watching folder: {self.watch_folder}")
        print(f"[FileMonitor] Press Ctrl+C to stop\n")
        
        try:
            while True:
                new_files = self.check_for_new_files()
                
                for filepath in new_files:
                    print(f"[FileMonitor] Triggering DRC for: {os.path.basename(filepath)}")
                    callback(filepath)
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n[FileMonitor] Stopped watching")

if __name__ == '__main__':
    def test_callback(filepath):
        print(f"  -> Would process: {filepath}")
    
    monitor = FileMonitorAgent('/workshop/hackathon/gds-files')
    monitor.watch(test_callback)
