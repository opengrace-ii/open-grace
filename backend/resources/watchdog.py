import asyncio
from datetime import datetime
from .logs import get_diagnostics_logger
from .self_test import run_all_diagnostics

logger = get_diagnostics_logger()

class WatchdogMonitor:
    def __init__(self):
        self.is_running = False
        self.check_interval = 60 # seconds

    async def start(self):
        self.is_running = True
        logger.info("Watchdog started")
        asyncio.create_task(self._monitor_loop())

    def stop(self):
        self.is_running = False
        logger.info("Watchdog stopped")

    async def _monitor_loop(self):
        while self.is_running:
            try:
                self._run_checks()
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
            await asyncio.sleep(self.check_interval)

    def _run_checks(self):
        results = run_all_diagnostics()
        failures = [r for r in results if r["status"] == "fail"]
        
        if failures:
            logger.error(f"Watchdog detected {len(failures)} failures.")
            for f in failures:
                logger.error(f"Failed Layer {f['layer']}: {f['name']} - {f['details']}")
            
            self._generate_report(failures)

    def _generate_report(self, failures):
        report = f"Diagnostics Report generated at {datetime.now().isoformat()}\\n"
        for f in failures:
            report += f"Problem in {f['name']}: {f['details']}\\n"
            report += f"Recommended Fix: Review {f['name']} logs and verify configuration.\\n"
        
        logger.info(f"Report generated:\\n{report}")

watchdog = WatchdogMonitor()
