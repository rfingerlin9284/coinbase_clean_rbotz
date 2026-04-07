#!/usr/bin/env python3
"""
RBOTZILLA PHOENIX: Autonomous AI Supervisor
Handles zero-touch startup, swarm management, and recursive health-checks.
Provides a stable environment for other AI agents to interact with the bot.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path
import psutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | 🤖 SUPERVISOR | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AutonomousBoot")

class AutonomousSupervisor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.orchestrator_path = self.base_dir / "orchestrator_start.py"
        self.maintenance_path = self.base_dir / "maintenance_agent.py"
        
        self.processes = {}
        
    def check_system_health(self):
        """Pre-flight memory and CPU checks"""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        logger.info(f"System Health -> CPU: {cpu}% | RAM: {mem}%")
        if mem > 90:
            logger.critical("Memory too high for safe autonomous boot! Aborting.")
            return False
        return True

    def launch_maintenance_agent(self):
        """Starts the background Error/SMS monitor"""
        logger.info("Initializing Maintenance/SMS Agent...")
        try:
            p = subprocess.Popen(
                [sys.executable, str(self.maintenance_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes['maintenance'] = p
            time.sleep(2)
            if p.poll() is None:
                logger.info("✅ Maintenance Agent ONLINE")
            else:
                logger.error("❌ Maintenance Agent failed to start")
        except Exception as e:
            logger.error(f"Failed to launch Maintenance Agent: {e}")

    def launch_swarm_orchestrator(self):
        """Boots the primary trading orchestrator in swarm mode"""
        logger.info("Initializing Hive Mind Swarm Orchestrator...")
        try:
            # We run it with --auto so it doesn't wait for interactive input
            p = subprocess.Popen(
                [sys.executable, str(self.orchestrator_path), "--swarm", "--auto"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes['orchestrator'] = p
            time.sleep(5)
            if p.poll() is None:
                logger.info("✅ Orchestrator Swarm ONLINE")
            else:
                logger.error("❌ Orchestrator failed to start")
        except Exception as e:
            logger.error(f"Failed to launch Orchestrator: {e}")

    def monitor_loop(self):
        """Continuous health-check loop"""
        logger.info("Entering Autonomous Monitoring pattern...")
        try:
            while True:
                time.sleep(60) # Health check every 60 seconds
                
                # Check Orchestrator
                orch_proc = self.processes.get('orchestrator')
                if orch_proc and orch_proc.poll() is not None:
                    logger.critical("⚠️ ORCHESTRATOR CRASH DETECTED! Initiating restart sequence...")
                    self.launch_swarm_orchestrator()
                
                # Check Maintenance Agent
                maint_proc = self.processes.get('maintenance')
                if maint_proc and maint_proc.poll() is not None:
                    logger.warning("⚠️ Maintenance Agent offline. Restarting...")
                    self.launch_maintenance_agent()
                
                # In a real scenario, you'd add deeper API checks here,
                # like pinging OANDA via requests to ensure the network is up.
                
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of all child processes"""
        logger.info("Initiating total system shutdown...")
        for name, p in self.processes.items():
            if p.poll() is None:
                logger.info(f"Terminating {name}...")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        logger.info("System Offline.")

def main():
    print("\n" + "="*60)
    print(" RBOTZILLA PHOENIX - AUTONOMOUS AI SUPERVISOR")
    print("="*60 + "\n")
    
    supervisor = AutonomousSupervisor()
    
    if not supervisor.check_system_health():
        sys.exit(1)
        
    supervisor.launch_maintenance_agent()
    supervisor.launch_swarm_orchestrator()
    
    supervisor.monitor_loop()

if __name__ == "__main__":
    main()
