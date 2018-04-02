import json
from datetime import datetime
import re

f = 'C:/personal/kuse/vinnare1.json'

with open(f, 'r') as json_file:
    js = json.load(json_file)


import requests
f2 = 'C:/personal/kuse/vinnare_tmp.json'
url = 'https://www.atg.se/services/v1/games/vinnare_2017-05-05_19_4'
r = requests.get(url)
with open(f2, 'w') as json_file:
    json.dump(r.json(), json_file)
with open(f2, 'r') as json_file:
    js = json.load(json_file)
print(js['races'][0]['result']['victoryMargin'])


#def getkey(k, js):
    #return js.get(k, None)
    
#race = dict()

#race_id = js['id']

#def extract_keys(js, dbkeys, corners=[]):
    #dic = dict()
    #for corner in corners:
        #dic[corner[1]] = js.get(corner[0], None)   
    #pat = r'^(.+)(_)(.{1})(.*)$'
    #for k_db in dbkeys:
        #k_js = k_db
        #m = re.match(pat, k_js)
        #while m is not None:
            #g = m.groups()
            #k_js = ''.join((g[0], g[2].upper(), g[3]))
            #m = re.match(pat, k_js)
        #dic[k_db] = js.get(k_js, None)
    #return(dic)

def parse_time(s):
    if s is None:
        return None
    else:
        try:
            return(datetime.strptime(s, '%Y-%m-%dT%H:%M:%S'))
        except ValueError:
            return(datetime.strptime(s, '%Y-%m-%d'))

def parse_lap_time(kmt):
    t = int(kmt.get('minutes', 0))*60*10 + int(kmt.get('seconds', 0))*10 + int(kmt.get('tenths', 0))
    if t == 0:
        return(None)
    else:
        return(t)
# Race
race = dict()
for k_db, k_js in (('odds_id', 'id'), ('status', 'status'), ('current_version', 'currentVersion')):
    race[k_db] = js.get(k_js, None)

for k_db, k_js in (('race_id', 'id'), ('name', 'name'), ('number', 'number'), ('distance', 'distance'), ('start_method', 'startMethod'), ('sport','sport'), ('status','status'),('media_id', 'mediaId')):
    race[k_db] = js['races'][0].get(k_js, None)


race_id = js['races'][0]['id']
track_id = js['races'][0]['track']['id']

race['start_time'] = parse_time(js['races'][0].get('startTime', None))
race['scheduled_start_time'] = parse_time(js['races'][0].get('scheduledStartTime', None))
race['date'] = parse_time(js['races'][0].get('date', None))
race['track_id'] = track_id
race['track_name'] = js['races'][0]['track'].get('name', None)
race['condition'] = js['races'][0]['track'].get('condition', None)
race['victory_margin'] = js['races'][0]['result'].get('victoryMargin', None)

# Prize
prize = dict()
prize['race_id'] = race_id
prize_string = js['races'][0].get('prize', None)
if prize_string is not None:
    pat = r'^Pris:\s?([0-9\.-]*)\s?\((\d*).*\)$'
    m = re.match(pat, prize_string)
    if m is None:
        raise(ValueError)
    else:
        g = m.groups()
        prize['n_prizes'] = int(g[1])
        sump = 0
        for n, pstr in enumerate(g[0].split('-')):
            p = int(pstr.replace('.',''))
            prize['prize_{0}'.format(n + 1)] = p
            sump += p
        prize['sum_prizes'] = sump
        prize['avg_prizes'] = round(sump/(1 + n))

# terms
terms = dict()
for n, t in enumerate(js['races'][0].get('terms', None)):
    terms['term_{0}'.format(str(n+1))] = t

#start
start = dict()
for s in js['races'][0]['starts']:
    start['number'] = s['number']
    start_id = 'S'.join((race_id, str(start['number'])))
    start['start_id'] = start_id
    
    horse = s['horse']
    horse_id = horse['id']
    start['horse_id'] = horse_id
    start['post_position'] = s.get('postPosition', None)
    start['horse_age'] = horse.get('age', None)
    start['money'] = horse.get('money', None)
    start['horse_home_track'] = horse['homeTrack']['id']
    
    
    trainer = horse['trainer']
    trainer_id = trainer['id']
    start['trainer_id'] = trainer_id
    start['trainer_home_track'] = trainer['homeTrack']['id']
    start['trainer_location'] = trainer['location']
    start['trainer_license'] = trainer['license']
    
    owner = horse['owner']
    owner_id = owner['id']
    start['owner_id'] = owner_id
    
    driver = s['driver']
    start['driver_id'] = driver['id']
    start['driver_location'] = driver['location']
    start['driver_home_track'] = driver['homeTrack']
    start['driver_license'] = driver['license']
    start['silks'] = driver['silks']
    
    res = s['result']
    start['finish_order'] = res['finishOrder']
    
    # kilometer time
    kmt = res['kmTime']
    if 'code' in kmt.keys():
        start['km_time_code'] = kmt['code']
    else:
        start['km_time_code'] = -1
        start['km_time'] = parse_lap_time(kmt)
    
    start['galloped'] = res.get('galloped', False)
    start['disqualified'] = res.get('disqualified', False)
    start['final_odds'] = res.get('finalOdds', None)
    start['start_number'] = res.get('startNumber', None)

    # horse
    H['horse_id'] = horse_id
    H['color'] = horse['color']
    H['name'] = horse['name']
    H['nationality'] = horse['nationality']
    H['birth_year'] = race['date'].year - horse['age']
    H['sex'] = horse['sex']
    breeder_id = horse['breeder']['id']
    H['breeder_id'] = breeder_id
    
    # breeder
    breeder = dict()
    breeder['breeder_id'] = breeder_id
    breeder['name'] = horse['breeder']['name']
    breeder['location'] = horse['breeder']['location']
    
    # record
    record = dict()
    r = horse['record']
    record['start_id'] = start_id
    record['code'] = r.get('code', None)
    record['start_method'] = r['startMethod']
    record['distance'] = r.get('distance', None)
    record['time'] = parse_lap_time(r.get('time', {}))
    
    # trainer
    t = dict()
    t['trainer_id'] = trainer_id
    t['first_name'] = trainer['lastName']
    t['last_name'] = trainer['firstName']
    t['short_name'] = trainer['shortName']
    t['birth'] = trainer['birth']
    
    # trainer stats
    trainer_stats = []
    ts = trainer['statistics']['years']
    for year in ts:
        t_stat = dict()
        t_stat['start_id'] = start_id
        t_stat['year'] = year
        t_stat['starts'] = ts[year]['starts']
        t_stat['earnings'] = ts[year]['earnings']
        t_stat['win_percentage'] = ts[year]['winPercentage']
        for pn in range(1,4):
            pns = str(pn)
            t_stat['place_{0}'.format(pns)] = ts[year]['placement'][pns]
    
    # shoes
    shoes = dict()
    hs = horse['shoes']
    shoes['start_id'] = start_id
    shoes['reported'] = hs['reported']
    if shoes['reported']:
        for pos in ('front', 'back'):
            shoes['{0}_has'.format(pos)] = hs[pos].get('hasShoe', None)
            shoes['{0}_changed'.format(pos)] = hs[pos].get('changed', None)
    
    # owner
    owner = dict()
    owner['start_id'] = start_id
    owner['owner_id'] = horse['owner']['id']
    owner['owner_name'] = horse['owner']['name']
    
    # breeder
    breeder = dict()
    breeder['start_id'] = start_id
    breeder['breeder_id'] = horse['breeder']['id']
    breeder['breeder_name'] = horse['breeder']['name']
    breeder['breeder_location'] = horse['breeder']['location']
    
    # horse stats
    horse_stats = []
    #ts = trainer['statistics']['years']
    #for year in ts:
        #t_stat = dict()
        #t_stat['start_id'] = start_id
        #t_stat['year'] = year
        #t_stat['starts'] = ts[year]['starts']
        #t_stat['earnings'] = ts[year]['earnings']
        #t_stat['win_percentage'] = ts[year]['winPercentage']
        #for pn in range(1,4):
            #pns = str(pn)
            #t_stat['place_{0}'.format(pns)] = ts[year]['placement'][pns]    
    
   
    
    
    

    
    
    
    
    
    
    
    
  # git chk 2 
    


'prize'

dbkeys = ['name', 'number', 'distance', 'start_method', 'sport', 'victory_margin', 'status', 'media_id', 'current_version']
corners = [('id', 'race_id')]



condition
track_id
start_time
scheduled_start_time

date = getkey('date')
if date is not None:
    date = datetime.strptime(date, '%Y-%m-%d')
race['date'] = date




