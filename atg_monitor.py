from os import system
from time import sleep, ctime
from sys import stdout

stdout = open('/home/joakim/work/mlog.log', 'w')

sleep(300)
while True:
    with open('/home/joakim/work/horse/heartbeat.txt', 'r') as hb_file:
        ts = int(hb_file.read())
    td = int(datetime.timestamp(datetime.now())) - ts
    if td > 600:
        system('sudo reboot')
    print('System online at {0}, with {1} idle seconds'.format(ctime(), str(td)))
    sleep(30)
    
    