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

from prometheus_client import start_http_server, Summary
from prometheus_client import Gauge, Histogram, Info
from datetime import datetime
import csv
import json
import logging
import random
import time

logger = logging.getLogger("metrics")

FPS_HIST_BUCKETS = (0, 20, 40, 60)

class Metrics:
    def __init__(self, port=8000, using_webrtc_csv=False):
        self.port = port

        self.fps = Gauge('fps', 'Frames per second observed by client')
        self.fps_hist = Histogram('fps_hist', 'Histogram of FPS observed by client', buckets=FPS_HIST_BUCKETS)
        self.gpu_utilization = Gauge('gpu_utilization', 'Utilization percentage reported by GPU')
        self.latency = Gauge('latency', 'Latency observed by client')
        self.webrtc_statistics = Info('webrtc_statistics', 'WebRTC Statistics from the client')
        self.using_webrtc_csv = using_webrtc_csv
        self.stats_video_file_path = None
        self.stats_audio_file_path = None
        self.prev_stats_video_header_len = None 
        self.prev_stats_audio_header_len = None

    def set_fps(self, fps):
        self.fps.set(fps)
        self.fps_hist.observe(fps)

    def set_gpu_utilization(self, utilization):
        self.gpu_utilization.set(utilization)

    def set_latency(self, latency_ms):
        self.latency.set(latency_ms)

    def start_http(self):
        start_http_server(self.port)

    def set_webrtc_stats(self, webrtc_stat_type, webrtc_stats):
        webrtc_stats_obj = json.loads(webrtc_stats)
        if self.using_webrtc_csv:
            if webrtc_stat_type == "_stats_audio":
                self.write_webrtc_stats_csv(webrtc_stats_obj, self.stats_audio_file_path)
            else:
                self.write_webrtc_stats_csv(webrtc_stats_obj, self.stats_video_file_path)
        self.webrtc_statistics.info(webrtc_stats_obj)

    def write_webrtc_stats_csv(self, obj_list, file_path):
        """Writes the WebRTC statistics to a CSV file.

        Arguments:
            obj_list {[list of object]} -- list of Python objects/dictionary
        """

        dt = datetime.now()
        timestamp = dt.strftime("%d/%B/%Y:%H:%M:%S")
        try:
            with open(file_path, 'a+') as stats_file:
                csv_writer = csv.writer(stats_file, quotechar='"')

                # Prepare the data
                headers = ["timestamp"]
                for obj in obj_list:
                    headers.extend(list(obj.keys()))
                values = [timestamp]
                for obj in obj_list:
                    values.extend(['"{}"'.format(val) if isinstance(val, str) and ';' in val else val for val in obj.values()])

                if 'audio' in file_path:
                    # Audio stats
                    if self.prev_stats_audio_header_len == None:
                        csv_writer.writerow(headers)
                        csv_writer.writerow(values)
                        self.prev_stats_audio_header_len = len(headers)
                    elif self.prev_stats_audio_header_len == len(headers):
                        csv_writer.writerow(values)
                    else:
                        # We got new fields so update the data
                        self.update_webrtc_stats_csv(file_path, headers, values)
                        self.prev_stats_audio_header_len = len(headers)
                else:
                    # Video stats
                    if self.prev_stats_video_header_len == None:
                        csv_writer.writerow(headers)
                        csv_writer.writerow(values)
                        self.prev_stats_video_header_len = len(headers)
                    elif self.prev_stats_video_header_len == len(headers):
                        csv_writer.writerow(values)
                    else:
                        # We got new fields so update the data
                        self.update_webrtc_stats_csv(file_path, headers, values)
                        self.prev_stats_video_header_len = len(headers)

        except Exception as e:
            logger.error("writing WebRTC Statistics to CSV file: " + str(e))

    def update_webrtc_stats_csv(self, file_path, headers, values):
        """Copies data from one CSV file to another to facilite dynamic updates to the data structure
           by handling empty values and appending new data.
        """
        prev_headers = None
        prev_values = []

        try:
            with open(file_path, 'r') as stats_file:
                csv_reader = csv.reader(stats_file, delimiter=',')

                # Fetch all existing data
                header_indicator = 0
                for row in csv_reader:
                    if header_indicator == 0:
                        prev_headers = row
                        header_indicator += 1
                    else:
                        prev_values.append(row)

                i, j = 0, 0
                while i < len(headers):
                    if headers[i] != prev_headers[j]:
                        # If there is a mismatch update all previous rows with a placeholder to represent an empty value, using `-1` here
                        for row in prev_values:
                            row.insert(i, -1)
                        i += 1
                    else:
                        i += 1
                        j += 1
                
                # When new files are at the end
                while j < i - 1:
                    for row in prev_values:
                        row.insert(j, -1)
                    j += 1

                # Validation check to confirm modified rows are of same length
                if len(prev_values[0]) != len(values):
                    logger.warn("There's a mismatch; columns could be misaligned with headers")
           
            # Purge existing file
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                logger.warn("File {} doesn't exist to purge".format(file_path))

            # create a new file with updated data
            with open(file_path, "a") as stats_file:
                csv_writer = csv.writer(stats_file)

                csv_writer.writerow(headers)
                csv_writer.writerows(prev_values)
                csv_writer.writerow(values)

                logger.info("WebRTC Statistics file {} created with updated data".format(stats_file))
        except Exception as e:
            logger.error("writing WebRTC Statistics to CSV file: " + str(e))

    def initialize_webrtc_csv_file(self, webrtc_stats_dir='/tmp'):
        """Initializes the WebRTC Statistics file upon every new WebRTC connection
        """
        dt = datetime.now()
        timestamp = dt.strftime("%Y-%m-%d:%H:%M:%S")
        self.stats_video_file_path = '{}/selkies-stats-video-{}.csv'.format(webrtc_stats_dir, timestamp)
        self.stats_audio_file_path = '{}/selkies-stats-audio-{}.csv'.format(webrtc_stats_dir, timestamp)
        self.prev_stats_video_header_len = None
        self.prev_stats_audio_header_len = None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    port = 8000

    m = Metrics(port)
    m.start()

    logger.info("Started metrics server on port %d" % port)

    # Generate random metrics
    while True:
        m.set_fps(int(random.random() * 100 % 60))
        m.set_gpu_utilization(int(random.random() * 100))
        time.sleep(1)
