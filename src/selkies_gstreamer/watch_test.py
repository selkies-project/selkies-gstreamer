# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import sys
import logging
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler

def on_modified_handler(event):
    if type(event) is FileModifiedEvent:
        print("File changed: {}".format(event.src_path))

async def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = FileSystemEventHandler()
    event_handler.on_modified = on_modified_handler
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    asyncio.run(main())
