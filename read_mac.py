#!/usr/bin/python3
import subprocess
import requests
import datetime as dt
snmpwalk="snmpwalk"
community="shack"
router_ip="10.0.0.3"
oid=".1.3.6.1.2.1.3.1.1.2"

from os.path import expanduser
home = expanduser("~")
persist_file = "%s/old_macs.json"%home

refresh_timeout=dt.timedelta(hours=4)
#refresh_timeout=dt.timedelta(minutes=1)
shackles_host="http://shackles.shack"

def get_last_macs():
    import json
    try:
        with open(persist_file,"r") as f:
            return json.load(f)
    except:
        print("no file found, returning []")
        return []
def set_last_macs(macs):
    import json
    with open(persist_file,"w+") as f:
        json.dump(macs,f)
def snmpwalk_available():
    return True

def get_macs():
    if not snmpwalk_available():
        raise Exception("Cannot find usable snmpwalk")
    proc = subprocess.Popen([snmpwalk,"-c",community,
        "-v","2c",router_ip,
        oid],stdout=subprocess.PIPE)
    all_macs = []
    for line in proc.stdout:
        line = line.decode()
        mac = line.split(":")[-1].strip().replace(" ",":").lower()
        #print(mac)
        all_macs.append(mac)
    return all_macs

def main():
    import requests

    all_macs = get_macs()
    last_macs = get_last_macs()
    event = {}
    for mac in all_macs:
        try: last_macs.remove(mac)
        except: print("%s was not in the last poll of macs"%mac)
    # removed all the new macs, go through the list of last macs and
    # log out every old user
    for old_mac in last_macs:
        ret=requests.get(shackles_host+"/api/rfid/"+old_mac)
        if ret.ok:
            j = ret.json()
            user = j["_id"]
            status = j["status"]
            # log out logged in users if none of their devices is online
            if status == "logged in":
                print("logging out %s"%user)
                event[user] = "logout"
        
    for mac in all_macs:
        ret=requests.get(shackles_host+"/api/rfid/"+mac)
        if ret.ok:
            j = ret.json()
            user = j["_id"]
            status = j["status"]
            if status == "logged out":
                print("hello user %s" %user)
                event[user] = "login"
                
            elif status == "logged in":
                # we will not logout a user if he is logged in and one of the
                # devices is online
                event[user] = "here"

                # get the last login activity
                last_activity =j["activity"][-1]
                last_activity_time= dt.datetime.strptime(
                        last_activity["date"],
                        "%Y-%m-%dT%H:%M:%S.%fZ")
                # refresh login if refresh timeout reached
                if last_activity_time < dt.datetime.now() - refresh_timeout:
                    event[user] = "refresh"
    
    print("what to do: %s" %event)
    for user,state in event.items():
        if state == "logout":
            print("logging out %s"%user)
            ret = requests.get(shackles_host+"/api/user/"+user+"/logout")
            tell_gobbelz("Bye Bye, %s"%user)
        elif state == "here":
            print("user %s is still here"%user)
        elif state == "refresh":
            print("refreshing login of user %s" %user)
            ret = requests.get(shackles_host+"/api/user/"+user+"/login")
        elif state == "login":
            print("hello user %s" %user)
            ret = requests.get(shackles_host+"/api/user/"+user+"/login")
            tell_gobbelz("Say hello to %s"%user)
    set_last_macs(all_macs)

def tell_gobbelz(text):
    import requests
    import json
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = {'text': text}
    try:
        requests.post("http://kiosk.shack:8080/say/",
                      data=json.dumps(data), headers=headers)
    except Exception as e: print("cannot tell gobbelz: %s" %str(e))
if __name__ == "__main__":
    import time
    main()
