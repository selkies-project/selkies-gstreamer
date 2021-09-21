# Copyright 2021 The Selkies Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import psutil

import logging
logger = logging.getLogger("system_monitor")


class SystemMonitor:
    def __init__(self, period=1, enabled=True):
        self.period = period
        self.enabled = enabled
        self.running = False

        self.cpu_percent = 0
        self.mem_total = 0
        self.mem_used = 0

        self.on_timer = lambda: logger.warn(
            "unhandled on_timer")

    def start(self):
        self.running = True
        while self.running:
            if self.enabled:
                self.cpu_percent = psutil.cpu_percent()
                mem = psutil.virtual_memory()
                self.mem_total = mem.total
                self.mem_used = mem.used
                self.on_timer(time.time())
                time.sleep(self.period)

    def stop(self):
        self.running = False
