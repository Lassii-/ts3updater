#!/usr/bin/env python3

import urllib.request
from packaging import version as ver
import time
from datetime import datetime, timedelta
from helperfunctions import get_current_version, check_for_updates,\
     download_update, ts3_instance_management, install_update

old_version: str
new_version: str
dl_url = "https://teamspeak.com/en/downloads/"
dlreq = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0'})


def update_ts3_if_needed():
    """Checks if there's an update for TS3 server and installs it if so"""
    old_version = get_current_version()
    new_version = check_for_updates(old_version, dlreq)
    if(ver.parse(new_version) > ver.parse(old_version)):
        download_update(new_version, dlreq)
        ts3_instance_management("stop")
        install_update()
        ts3_instance_management("start")
        print("Server updated")
    else:
        print("No update to do")


def restore_ts3_from_crash():
    """Checks whether the TS3 has crashed and restarts it if so."""
    status = ts3_instance_management("status")
    if(status == "Up"):
        print("Server is running normally")
    elif(status == "Down"):
        print("Server has crashed, restarting")
        ts3_instance_management("stop")
        ts3_instance_management("start")


def main():
    print("Checking for server updates")
    update_ts3_if_needed()
    last_checked = datetime.utcnow()
    while(True):
        if (datetime.utcnow() - last_checked) > timedelta(1):
            print("Checking for server updates")
            update_ts3_if_needed
            last_checked = datetime.utcnow()
        else:
            print("Skipping server update check")
        print("Checking if server has crashed")
        restore_ts3_from_crash()
        print("sleeping for 10 minutes")
        time.sleep(600)


if __name__ == '__main__':
    main()
