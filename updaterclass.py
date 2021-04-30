import tarfile
import os
import hashlib
from bs4 import BeautifulSoup as bs4
import json
import urllib.request
from packaging import version as ver
import subprocess
import getpass


class TS3Updater:
    version: str
    currentUser: str = getpass.getuser()

    def __init__(self, dl_url, dl_req):
        self.dl_url = dl_url
        self.dl_req = dl_req

    def sha256match(self, sha256hash) -> bool:
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

    def get_current_version(self):
        with open('version.json', 'r') as version_file:
            try:
                data = json.load(version_file)
                self.version = data['version']
            except:
                print("Can't read version.json")
                raise

    def check_for_updates(self):
        version: str
        page = urllib.request.urlopen(self.dl_req)
        soup = bs4(page, 'html.parser')
        css_selector = soup.select_one('#server > div:nth-child(3) > div:nth-child(3) > \
        div:nth-child(1) > h3:nth-child(1) > span:nth-child(1)')
        version = css_selector.find(text=lambda text: text and text.strip(),
                                    recursive=False).strip()
        if(ver.parse(version) > ver.parse(self.version)):
            self.version = version
            return self.version
        else:
            self.version = self.version
            return self.version

    def download_update(self):
        try:
            urllib.request.urlretrieve(f"https://files.teamspeak-services.com/releases/server/{self.version}/teamspeak3-server_linux_amd64-{self.version}.tar.bz2",
                                       "update.tar.bz2")
            page = urllib.request.urlopen(self.dl_req)
            soup = bs4(page, 'html.parser')
            css_selector = soup.select_one(
                '#server > div:nth-child(3) > div:nth-child(3) > div:nth-child(1) > div:nth-child(2) > pre:nth-child(1)')
            sha256hash = css_selector.find(text=lambda text: text and text.strip(),
                                           recursive=False).strip()
            if(self.sha256match(sha256hash[8:]) is False):
                raise ValueError('The SHA256 sums do not match')
        except:
            print("Couldn't download the update")
            raise

    def install_update(self):
        try:
            update_file = tarfile.open("update.tar.bz2", "r:bz2")
            update_file.extractall()
            update_file.close()
            os.unlink("update.tar.bz2")
            with open('version.json', 'r+') as version_file:
                data = json.load(version_file)
                data['version'] = self.version
                version_file.seek(0)
                version_file.truncate()
                json.dump(data, version_file)
        except:
            print("Couldn't install the update")
            raise

    def ts3_instance_management(self, action):
        if(action == "start"):
            subprocess.call("./ts3server_startscript.sh start",
                            cwd=f"/home/{self.currentUser}/teamspeak3-server_linux_amd64",
                            shell=True)
        elif(action == "stop"):
            subprocess.call("./ts3server_startscript.sh stop",
                            cwd=f"/home/{self.currentUser}/teamspeak3-server_linux_amd64",
                            shell=True)
        elif(action == "status"):
            status = subprocess.check_output(
                "./ts3server_startscript.sh status", cwd=f"/home/{self.currentUser}/teamspeak3-server_linux_amd64", shell=True, universal_newlines=True)
            if(status == "Server is running\n"):
                return "Up"
            else:
                return "Down"
        else:
            print("No action given")

    def update_ts3_if_needed(self):
        self.get_current_version()
        old_version = self.version
        new_version: str = self.check_for_updates()
        if(ver.parse(new_version) > ver.parse(old_version)):
            self.download_update()
            self.ts3_instance_management("stop")
            self.install_update()
            self.ts3_instance_management("start")
            print("Server updated")
        else:
            print("No update to do")

    def restore_ts3_from_crash(self):
        status = self.ts3_instance_management("status")
        if(status == "Up"):
            print("Server is running normally")
        elif(status == "Down"):
            print("Server has crashed, restarting")
            self.ts3_instance_management("stop")
            self.ts3_instance_management("start")
