# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import time
import psutil

import logging
logger = logging.getLogger("system_monitor")
logger.setLevel(logging.INFO)


class SystemMonitor:
    def __init__(self, period=1, enabled=True):
        self.period = period
        self.enabled = enabled
        self.running = False

        self.cpu_percent = 0
        self.mem_total = 0
        self.mem_used = 0

        self.on_timer = lambda: logger.warning(
            "unhandled on_timer")

    async def start(self):
        self.running = True
        while self.running:
            if self.enabled and int(time.time()) % self.period == 0:
                self.cpu_percent = psutil.cpu_percent()
                mem = psutil.virtual_memory()
                self.mem_total = mem.total
                self.mem_used = mem.used
                self.on_timer(time.time())
            await asyncio.sleep(0.5)
        logger.info("system monitor stopped")

    def stop(self):
        self.running = False
