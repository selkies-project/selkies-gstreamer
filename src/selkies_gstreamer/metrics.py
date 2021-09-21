# Copyright 2019 Google LLC
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

from prometheus_client import start_http_server, Summary
from prometheus_client import Gauge, Histogram
import logging
import random
import time

logger = logging.getLogger("metrics")

FPS_HIST_BUCKETS = (0, 20, 40, 60)

class Metrics:
    def __init__(self, port=8000):
        self.port = port

        self.fps = Gauge('fps', 'Frames per second observed by client')
        self.fps_hist = Histogram('fps_hist', 'Histogram of FPS observed by client', buckets=FPS_HIST_BUCKETS)
        self.gpu_utilization = Gauge('gpu_utilization', 'Utilization percentage reported by GPU')
        self.latency = Gauge('latency', 'Latency observed by client')

    def set_fps(self, fps):
        self.fps.set(fps)
        self.fps_hist.observe(fps)

    def set_gpu_utilization(self, utilization):
        self.gpu_utilization.set(utilization)
    
    def set_latency(self, latency_ms):
        self.latency.set(latency_ms)
    
    def start(self):
        start_http_server(self.port)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    port = 8000

    m = Metrics(port)
    m.start()

    logger.info("Started metrics server on port %d" % port)
    
    # Generate some metrics.
    while True:
        m.set_fps(int(random.random() * 100 % 60))
        m.set_gpu_utilization(int(random.random() * 100))
        time.sleep(1)