from os import system
from time import sleep, ctime

with open('/home/joakim/work/mlog.log', 'w') as status_file:
    status_file.write('Starting at {0}\n'.format(ctime()))

sleep(300)
while True:
    with open('/home/joakim/work/horse/heartbeat.txt', 'r') as hb_file:
        ts = int(hb_file.read())
    td = int(datetime.timestamp(datetime.now())) - ts
    if td > 600:
        system('sudo reboot')
    with open('/home/joakim/work/mlog.log', 'a') as status_file:
        status_file.write('System online at {0}, with {1} idle seconds\n'.format(ctime(), str(td)))
    sleep(30)
    
    