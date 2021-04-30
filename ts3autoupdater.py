#!/usr/bin/env python3

import urllib.request
import time
from datetime import datetime, timedelta
from updaterclass import TS3Updater

dl_url = "https://teamspeak.com/en/downloads/"
dlreq = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0'})


def main():
    TS3UpdaterInstance = TS3Updater(dl_url, dlreq)
    print(f"Checking for server updates {datetime.now().time()}")
    TS3UpdaterInstance.update_ts3_if_needed()
    last_checked = datetime.utcnow()
    while(True):
        if (datetime.utcnow() - last_checked) > timedelta(1):
            print(f"Checking for server updates {datetime.now().time()}")
            TS3UpdaterInstance.update_ts3_if_needed()
            last_checked = datetime.utcnow()
        else:
            print("Skipping server update check")
        print("Checking if server has crashed")
        TS3UpdaterInstance.restore_ts3_from_crash()
        print("Sleeping for 1 minute")
        time.sleep(60)


if __name__ == '__main__':
    main()
