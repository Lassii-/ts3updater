import tarfile
import os
import hashlib
from bs4 import BeautifulSoup as bs4
import json
import urllib.request
from packaging import version as ver
import subprocess
import getpass


def sha256match(sha256hash: str) -> bool:
    """Verifies update.tar.bz2 against the given SHA256 hash"""
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open('update.tar.bz2', 'rb', buffering=0) as update_file:
        for n in iter(lambda: update_file.readinto(mv), 0):
            h.update(mv[:n])
    if(sha256hash == h.hexdigest()):
        return True
    else:
        return False


def get_current_version() -> str:
    """Reads and returns the current TS3 server version from version.json"""
    version: str
    with open('version.json', 'r') as version_file:
        try:
            data = json.load(version_file)
            version = data['version']
            return version
        except:
            print("Can't read version.json")
            raise


def check_for_updates(old_version: str, dlreq: urllib.request.Request) -> str:
    """Checks TS3 downloads and updates json-file and returns new version

    In case of no update being available
    function returns the old version number
    """
    version: str
    page = urllib.request.urlopen(dlreq)
    soup = bs4(page, 'html.parser')
    css_selector = soup.select_one('#server > div:nth-child(3) > div:nth-child(3) > \
    div:nth-child(1) > h3:nth-child(1) > span:nth-child(1)')
    version = css_selector.find(text=lambda text: text and text.strip(),
                                recursive=False).strip()
    if(ver.parse(version) > ver.parse(old_version)):
        try:
            with open('version.json', 'r+') as version_file:
                data = json.load(version_file)
                data['version'] = version
                version_file.seek(0)
                version_file.truncate()
                json.dump(data, version_file)
                return version
        except:
            print("Something went wrong updating the version.json")
            raise
    else:
        return old_version


def download_update(version: str, dlreq: urllib.request.Request):
    """Downloads the new TS3 version based on given version-number.

    The update gets saved as update.tar.bz2.
    Function also uses sha256match-function to check
    that the downloaded data matches the hash on the downloads-page
    """
    try:
        urllib.request.urlretrieve(f"https://files.teamspeak-services.com/releases/server/{version}/teamspeak3-server_linux_amd64-{version}.tar.bz2",
                                   "update.tar.bz2")
        page = urllib.request.urlopen(dlreq)
        soup = bs4(page, 'html.parser')
        css_selector = soup.select_one('#server > div:nth-child(3) > div:nth-child(3) >\
        div:nth-child(1) > div:nth-child(2) > p:nth-child(1)')
        sha256hash = css_selector.find(text=lambda text: text and text.strip(),
                                       recursive=False).strip()
        if(sha256match(sha256hash[8:]) is False):
            raise ValueError('The SHA256 sums do not match')
    except:
        print("Couldn't download the update")
        raise


def install_update():
    """Installs the update and removes the update-file after that."""
    try:
        update_file = tarfile.open("update.tar.bz2", "r:bz2")
        update_file.extractall()
        update_file.close()
        os.unlink("update.tar.bz2")
    except:
        print("Couldn't install the update")
        raise


def ts3_instance_management(action: str):
    """Starts, stops or gives the server status based on the passed argument.

    The following arguments are supported.
    start: Sends the start-command to TS3 startscript
    stop: Sends the stop-command to TS3 startscript
    status: Sends the status-command to TS3 startscript
            and then returns "Up" or "Down" depending whether
            the TS3 instance has running or not
    """
    currentUser = getpass.getuser()
    if(action == "start"):
        subprocess.call("./ts3server_startscript.sh start",
                        cwd=f"/home/{currentUser}/teamspeak3-server_linux_amd64",
                        shell=True)
    elif(action == "stop"):
        subprocess.call("./ts3server_startscript.sh stop",
                        cwd=f"/home/{currentUser}/teamspeak3-server_linux_amd64",
                        shell=True)
    elif(action == "status"):
        status = subprocess.check_output("./ts3server_startscript.sh status",
                                         cwd=f"/home/{currentUser}/teamspeak3-server_linux_amd64",
                                         shell=True,
                                         universal_newlines=True)
        if(status == "Server is running\n"):
            return "Up"
        else:
            return "Down"
    else:
        print("No action given")
