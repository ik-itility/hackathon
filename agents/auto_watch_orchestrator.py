#!/usr/bin/env python3
"""Auto-Watch DRC Orchestrator - Monitors folder and processes new GDS files"""

import sys
import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from strands_orchestrator import process_gds_file

class GDSFileHandler(FileSystemEventHandler):
    """Handler for new GDS files"""
    
    def __init__(self, rules_path: str, output_dir: str):
        self.rules_path = rules_path
        self.output_dir = output_dir
        self.processed_files = set()
    
    def on_created(self, event):
        """Called when a file is created"""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.gds'):
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            
            if event.src_path not in self.processed_files:
                print(f"\n{'='*70}")
                print(f"🔔 NEW GDS FILE DETECTED: {event.src_path}")
                print(f"{'='*70}\n")
                
                try:
                    process_gds_file(
                        gds_path=event.src_path,
                        rules_path=self.rules_path,
                        output_dir=self.output_dir
                    )
                    self.processed_files.add(event.src_path)
                except Exception as e:
                    print(f"❌ Error processing {event.src_path}: {e}")

def start_watching(watch_folder: str, rules_path: str, output_dir: str):
    """Start watching folder for new GDS files"""
    
    print("\n" + "="*70)
    print("🤖 MULTI-AGENT DRC AUTO-WATCH SYSTEM")
    print("="*70)
    print(f"📁 Watching: {watch_folder}")
    print(f"📋 Rules: {rules_path}")
    print(f"📊 Output: {output_dir}")
    print("="*70)
    print("\n⏳ Waiting for new GDS files...")
    print("   (Drop a .gds file into the folder to trigger processing)")
    print("   (Press Ctrl+C to stop)\n")
    
    # Create handler and observer
    event_handler = GDSFileHandler(rules_path, output_dir)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping auto-watch system...")
        observer.stop()
    
    observer.join()
    print("✅ Auto-watch system stopped.\n")

if __name__ == '__main__':
    start_watching(
        watch_folder='/workshop/hackathon/gds-files',
        rules_path='/workshop/hackathon/data/rules_config.yaml',
        output_dir='/workshop/hackathon/output'
    )
