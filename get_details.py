import subprocess
import uuid

# These are the exact functions from your app/security.py
mobo = "UNKNOWN"
bios = "UNKNOWN"
mac = "UNKNOWN"

try:
    mobo = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
    bios = subprocess.check_output('wmic bios get serialnumber', shell=True).decode().split('\n')[1].strip()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
except Exception:
    pass

print("\n" + "="*50)
print("PLEASE SHARE THESE VALUES WITH THE ADMINISTRATOR:")
print("="*50)
print(f"Motherboard UUID: {mobo}")
print(f"BIOS Serial:      {bios}")
print(f"MAC Address:      {mac}")
print("="*50)