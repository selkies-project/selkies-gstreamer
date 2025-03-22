# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#   Copyright 2019 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import GPUtil
import asyncio
import time

import logging
logger = logging.getLogger("gpu_monitor")
logger.setLevel(logging.INFO)


class GPUMonitor:
    def __init__(self, period=1, enabled=True):
        self.period = period
        self.enabled = enabled
        self.running = False

        self.on_stats = lambda load, memoryTotal, memoryUsed: logger.warning(
            "unhandled on_stats")

    async def start(self, gpu_id=0):
        self.running = True
        while self.running:
            if self.enabled and int(time.time()) % self.period == 0:
                gpu = GPUtil.getGPUs()[gpu_id]
                self.on_stats(gpu.load, gpu.memoryTotal, gpu.memoryUsed)
            await asyncio.sleep(0.5)
        logger.info("GPU monitor stopped")

    def stop(self):
        self.running = False
