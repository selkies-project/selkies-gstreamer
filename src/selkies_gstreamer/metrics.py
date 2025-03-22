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

from prometheus_client import start_http_server
from prometheus_client import Gauge, Histogram, Info
from datetime import datetime
import asyncio
import csv
import json
import logging
import random
import os
from collections import OrderedDict
import argparse

logger = logging.getLogger("metrics")
logger.setLevel(logging.INFO)

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

    async def start_http(self):
        await asyncio.to_thread(start_http_server, self.port)

    async def set_webrtc_stats(self, webrtc_stat_type, webrtc_stats):
        webrtc_stats_obj = await asyncio.to_thread(json.loads, webrtc_stats)
        sanitized_stats = await asyncio.to_thread(self.sanitize_json_stats, webrtc_stats_obj)
        if self.using_webrtc_csv:
            if webrtc_stat_type == "_stats_audio":
                asyncio.create_task(asyncio.to_thread(self.write_webrtc_stats_csv, sanitized_stats, self.stats_audio_file_path))
            else:
                asyncio.create_task(asyncio.to_thread(self.write_webrtc_stats_csv, sanitized_stats, self.stats_video_file_path))
        await asyncio.to_thread(self.webrtc_statistics.info, sanitized_stats)

    def sanitize_json_stats(self, obj_list):
        """A helper function to process data to a structure
           For example: reportName.fieldName:value
        """
        obj_type = []
        sanitized_stats = OrderedDict()
        for i in range(len(obj_list)):
            curr_key = obj_list[i].get('type')
            if  curr_key in obj_type:
                # Append id at suffix to eliminate duplicate types
                curr_key = curr_key + str("-") + obj_list[i].get('id')
                obj_type.append(curr_key)
            else:
                obj_type.append(curr_key)

            for key, val in obj_list[i].items():
                unique_type = curr_key + str(".")  + key
                if not isinstance(val, str):
                    sanitized_stats[unique_type] =  str(val)
                else:
                    sanitized_stats[unique_type] = val

        return sanitized_stats

    def write_webrtc_stats_csv(self, obj, file_path):
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
                headers += obj.keys()

                # Upon reconnections the client could send a redundant objs just discard them
                if len(headers) < 15: 
                    return

                values = [timestamp]
                for val in obj.values():
                    values.extend(['"{}"'.format(val) if isinstance(val, str) and ';' in val else val])

                if 'audio' in file_path:
                    # Audio stats
                    if self.prev_stats_audio_header_len is None:
                        csv_writer.writerow(headers)
                        csv_writer.writerow(values)
                        self.prev_stats_audio_header_len = len(headers)
                    elif self.prev_stats_audio_header_len == len(headers):
                        csv_writer.writerow(values)
                    else:
                        # Update the data after obtaining new fields
                        self.prev_stats_audio_header_len = self.update_webrtc_stats_csv(file_path, headers, values)
                else:
                    # Video stats
                    if self.prev_stats_video_header_len is None:
                        csv_writer.writerow(headers)
                        csv_writer.writerow(values)
                        self.prev_stats_video_header_len = len(headers)
                    elif self.prev_stats_video_header_len == len(headers):
                        csv_writer.writerow(values)
                    else:
                        # Update the data after obtaining new fields
                        self.prev_stats_video_header_len = self.update_webrtc_stats_csv(file_path, headers, values)

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

                # Sometimes columns might not exist in new data
                if len(headers) < len(prev_headers):
                    for i in prev_headers:
                        if i not in headers:
                            values.insert(prev_headers.index(i), "NaN")
                else:
                    i, j, k = 0, 0, 0
                    while i < len(headers):
                        if headers[i] != prev_headers[j]:
                            # If there is a mismatch, update all previous rows with a placeholder to represent an empty value, using `NaN` here
                            for row in prev_values:
                                row.insert(i, "NaN")
                            i += 1
                            k += 1  # track number of values added
                        else:
                            i += 1
                            j += 1

                    j += k
                    # When new fields are at the end
                    while j < i:
                        for row in prev_values:
                            row.insert(j, "NaN")
                        j += 1

                # Validation check to confirm modified rows are of same length
                if len(prev_values[0]) != len(values):
                    logger.warning("There's a mismatch; columns could be misaligned with headers")

            # Purge existing file
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                logger.warning("File {} doesn't exist to purge".format(file_path))

            # Create a new file with updated data
            with open(file_path, "a") as stats_file:
                csv_writer = csv.writer(stats_file)

                if len(headers) > len(prev_headers):
                    csv_writer.writerow(headers)
                else:
                    csv_writer.writerow(prev_headers)
                csv_writer.writerows(prev_values)
                csv_writer.writerow(values)

                logger.debug("WebRTC Statistics file {} created with updated data".format(file_path))
            return len(headers) if len(headers) > len(prev_headers) else len(prev_headers)
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

async def main():
    parser = argparse.ArgumentParser(description='Metrics server')
    parser.add_argument('--port', type=int, default=8000, help='Port to start metrics server on')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    m = Metrics(args.port)
    await m.start_http()
    logger.info("Started metrics server on port %d" % port)
    await asyncio.to_thread(m.initialize_webrtc_csv_file())
    # Generate random metrics
    while True:
        m.set_fps(int(random.random() * 100 % 60))
        m.set_gpu_utilization(int(random.random() * 100))
        await asyncio.sleep(1.0)

def entrypoint():
    asyncio.run(main())

if __name__ == '__main__':
    entrypoint()
