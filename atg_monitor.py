from os import system
from time import sleep

sleep(300)
while True:
    with open('/home/joakim/work/horse/heartbeat.txt', 'r') as hb_file:
        ts = int(hb_file.read())
    td = int(datetime.timestamp(datetime.now())) - ts
    if td > 600:
        system('sudo reboot')
    sleep(30)
    
    