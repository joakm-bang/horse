import numpy as np
#import psycopg2
import mechanicalsoup
from time import sleep, time, ctime
from datetime import datetime, timedelta
import requests
import json
import os
#import pickle
import csv
#from sys import stdout

# sleep before getting to work
log_file = '/home/joakim/work/log.log'
with open(log_file, 'w') as log:
    log.write('Starting at {0}\n'.format(ctime()))
sleep(15)

def convert_to_ordinal(d):
    return(datetime.strptime(d, '%Y-%m-%d').toordinal())


def convert_to_timestamp(d):
    if d is None:
        return(None)
    else:
        return(datetime.strptime(d, '%Y-%m-%dT%H:%M:%S'))


class Browser:
    """"""

    #----------------------------------------------------------------------
    def __init__(self, settings):

        self.t = [time(), time(), time()]
        self.delayLambda = settings.delayLambda
        self.settings = settings
        self.getIP() 
        self.br = mechanicalsoup.Browser(soup_config={'features': 'lxml'})    
        self.bannedIP = settings.bannedIP
        self.error_log = settings.error_log

    #----------------------------------------------------------------------
    # Don't hammer the server
    def delay(self, minDelay=0.5, maxDelay = 30, printDelay=True):
        delta = (self.t[1]-self.t[0], self.t[2]-self.t[1], time() - self.t[2])
        self.t[0] = time()
        randomDelay = np.random.poisson(self.delayLambda)
        nap_time = min(max(randomDelay - delta[2],minDelay), maxDelay)
        if nap_time > 0:
            if printDelay:
                print('Total delay:\t' + str(round(sum(delta),2)) + ' seconds\t(' + \
                      str(round(delta[0] + delta[2],2)) + ' nap [' + str(round(delta[2],2)) + \
                      ' code + ' + str(round(delta[0],2)) + ' extra] and ' + str(round(delta[1],2)) + \
                                      ' browser).')
            sleep(nap_time)	

    #----------------------------------------------------------------------
    #Take a nap if you cannot access the webpage. Probably a timeout error.
    def nap(self, errStr, err, nap_time=60):
        divider = ' *'*30
        print(divider + '\nError:' + errStr+ '\nNapping for ' + \
              str(nap_time/60) + ' minutes\n' + divider)
        this_nap = np.random.poisson(nap_time)
        with open(self.error_log, 'a') as log_file:
            log_file.write(','.join((ctime(), errStr, str(err), str(this_nap))))
        sleep(this_nap)

    #----------------------------------------------------------------------
    #Hit the webpage
    def open(self, targetURL, maxtries=10, napTime=90, mess='Error while opening page', 
             noDelay=False):
        goon = True
        tryCount = 0
        while goon == True and tryCount < maxtries:
            tryCount = tryCount + 1
            try:
                if self.bannedIP is not None:
                    self.getIP()
                    for bannedIP in self.bannedIPs:
                        if self.ip.startswith(bannedIP):
                            print('Proxy is down.')
                            raise proxyerror()
                if not noDelay:
                    self.delay()
                    self.t[1] = time()
                    
                #timeout issue
                self.page = self.br.get(targetURL, timeout=30)
                self.t[2] = time()
                if self.page.status_code != 200:
                    raise ValueError('Bad response code')
                goon = False
            except proxyerror as perr:
                print('Proxy error')
                self.nap('Proxy error', perr, napTime)
                
            except Exception as err:
                #tryCount = maxtries + 1
                self.nap(str(err), err, napTime)
        
        if goon:
            print('Request failed')
            raise ValueError('Request failed')
        else:
            self.heartbeat()
            
    def heartbeat(self):
        # Issue heartbeat
        goon = True
        tries = 0
        while tries < 5:
            tries += 1
            try:
                with open(settings.paths['hb'] + 'heartbeat.txt', 'w') as hb_file:
                    hb_file.write(str(int(datetime.timestamp(datetime.now()))))
                    tries = 10
            except:
                print('Heartbeat error')
                sleep(5)
                    
    
    
        
    #----------------------------------------------------------------------
    #Get public ip
    def getIP(self, maxN=5, S=30):
        n = 0
        goon = True
        while n < maxN and goon:
            try:
                n = n + 1
                self.ip = requests.get('https://api.ipify.org').text
                goon = False
            except:
                try:
                    self.ip = json.loads(requests.get('http://jsonip.com').text)['ip']
                    goon = False
                except:
                    print('Error getting IP on attempt ' + str(n) + '. Sleeping for ' + str(S) + ' seconds.')
                    sleep(S)
        #if not goon:
            #self.announce_IP()

    #def announce_IP(self):
        #db.updateField(tables.info, 'time', datetime.now(), 'computer', settings.computer)
        #db.updateField(tables.info, 'ip', self.ip, 'computer', settings.computer)
        
        #monster_ip = db.getValues('ip', 'info', sels=[('computer', '=', 'monstret')])
        #self.bannedIPs += list(monster_ip)
        
class proxyerror(Exception):
    def __init__(self, value='Proxy error'):
        pass


class Atg:
    
    def __init__(self, settings):

        self.br = Browser(settings) 
        self.races_path = settings.paths.get('races', 
                                    '/media/joakim/Storage/Dropbox/atg/data/json/races/')
        self.calendar_path = settings.paths.get('calendar', 
                                       '/media/joakim/Storage/Dropbox/atg/data/json/calendardays/')
        #self.first_contact()
        
    #def first_contact(self):
        #computers = db.getValues('computer', 'info')
        #if settings.computer not in computers:
            #db.write2db({'computer':settings.computer, 
                         #'time':datetime.now(), 'ip':self.br.ip}, tables.info)
        
    def download_json(self, url, destination):
        
        if os.path.exists(destination):
            print('Skipping existing file: {0}'.format(destination.split('/')[-1]))
        else:
            try:
                self.br.open(url)
                with open(destination, 'w') as out_file:
                    json.dump(self.br.page.json(), out_file)
            except:
                    raise ValueError('Invalid JSON?')
        
    def get_all_calendars(self, start=False, end=False):
        
        def leading_zero(n):
            '''Add a leading zero if single digit'''
            s = str(n)
            if len(s) == 1:
                return ''.join(('0', s))
            else:
                return(s)

        if not end:
            end = datetime.now().toordinal() - 7
        if not start:
            start = end - 365*5
        if type(end) is str:
            end = datetime.strptime(end, '%Y-%m-%d').toordinal()
        if type(start) is str:
            start = datetime.strptime(start, '%Y-%m-%d').toordinal()
            
        
        for ordinal in range(end, start-1, -1):
            dt = datetime.fromordinal(ordinal)      # Convert to datetime
            str_date = '-'.join(map(leading_zero, (dt.year, dt.month, dt.day)))     # Conevert to atg suitable string        
            
            destination = self.calendar_path + str_date + '.json'
            if not os.path.exists(destination):
                url = 'https://www.atg.se/services/v1/calendar/day/{date}'.format(date=str_date)            # Construct the url
                self.download_json(url, destination)
                print('Downloaded {date}'.format(date=str_date))
            else:
                print('Skipped {date}'.format(date=str_date))
    
    
    
    def get_games(self):
        
        self.Q = RaceQueue()
        while not self.Q.is_empty():
            ID = self.Q.pop()
            url = 'https://www.atg.se/services/v1/games/' + ID
            destination = self.races_path + ID + '.json'
            self.download_json(url, destination)
            #db.updateField(tables.games, 'scraped', True, 'game_id', ID)
            #print('Downloaded {0}'.format(ID))
            with open(log_file, 'a') as log:
                log.write('Downloaded {0}\n'.format(ID))
        
class CalendarParser:
    
    def __init__(self, start='1900-01-01', end='2100-01-01'):
        self.start = start
        self.end = end
        self.path = settings.paths['calendar']
        self.Q = CalendarQueue(self.start, self.end)
        
    def parse(self):
        while not self.Q.is_empty():
            f = self.Q.pop()
            with open(self.path + f, 'r') as json_file:
                data = json.load(json_file)
            if len(data) > 0:
                                
                races = dict()
                
                date = data['date']
                pdate = convert_to_ordinal(date)
                keymap = {'track_id':'id', 'track_name':'name', 'sport': 'sport', 
                          'biggest_game':'biggestGameType'}
                for track in data['tracks']:
                    raceday = dict()
                    raceday['date'] = date
                    raceday['pdate'] = pdate
                    for k, v in keymap.items():
                        raceday[k] = track.get(v, None)
                    raceday['track_start_time'] = convert_to_timestamp(track.get('startTime', None))
                    raceday['n_races'] = len(track.get('races', []))
                
                    db.write2db(raceday, tables.racedays, useTimeStamp=True, 
                               insertKeys=False, commit=False)
                    
                    for race in track.get('races', []):
                        ID = race['id']
                        races[ID] = dict()
                        races[ID]['race_id'] = ID
                        races[ID]['number'] = race['number']
                        races[ID]['status'] = race['status']
                        races[ID]['start_time'] = convert_to_timestamp(race.get('startTime', None))
                
                for n in range(1,10):
                    break
                
                for game_type in data['games'].keys():
                    for game in data['games'][game_type]:

                        games = dict()
                        
                        games['game_id'] = game.get('id', None)
                        if games['game_id'] is None:
                            break
                        games['date'] = date
                        games['pdate'] = pdate
                        games['type'] = game_type
                        games['status'] = game['status']
                        games['start_time'] = convert_to_timestamp(game.get('startTime', None))
                        games['scheduled_start_time'] = convert_to_timestamp(game.get('scheduledStartTime', None))
                        games['track'] = game['tracks'][0]
                        games['n_tracks'] = len(game['tracks'])
                        games['n_races'] = len(game['races'])
                        games['scraped'] = False
                        
                        db.write2db(games, tables.games, useTimeStamp=True, 
                                    insertKeys=False, commit=False)
                        
                        for n, ID in enumerate(game['races']):
                            races[ID][game_type.lower()] = n
                
                for ID, race in races.items():
                    db.write2db(race, tables.races, useTimeStamp=True,
                                insertKeys=False, commit=False)
                
            db.updateField(tables.calendar_files, 'scraped', True, 'file_name', f)
                

class CalendarQueue:
    
    def __init__(self, start='1900-01-01', end='2100-01-01'):
        
        self.start = convert_to_ordinal(start)
        self.end = convert_to_ordinal(end)
        self.calendar_path = settings.paths['calendar']
        self.fill()
    
    def fill(self):
        self.Q = db.getValues('file_name', tables.calendar_files,
                     sels=[('pdate', '>=', self.start),
                           ('pdate', '<', self.end),
                           ('scraped', '=', False)])
        np.random.shuffle(self.Q)
                
    def pop(self):
        return(self.Q.pop())
    
    def len(self):
        return(len(self.Q))
    
    def is_empty(self):
        return(self.len() == 0)
    
    





class Settings:
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        #Defaults
        self.debug = True
        self.bannedIP = None
        self.runlocal = False
        self.runLAN = False
        self.delayLambda = 8
        self.bannedIPs = ['213.67.246.', '5.157.7.']
        self.error_log = '/media/joakim/Storage/Dropbox/atg/data/logs/browser.log'
        self.paths = {'races':'/media/joakim/Storage/Dropbox/atg/data/json/races/',
                      'calendar':'/media/joakim/Storage/Dropbox/atg/data/json/calendardays/'}
        
        self.computer = os.environ['COMPUTER_NAME']
        if self.computer.startswith('vbox'):
            #self.paths['races'] = '/home/joakim/work/horse/jsons/'
            self.paths['hb'] = '/home/joakim/work/horse/'
            self.paths['races'] = '/media/sf_Shared/json/'
            self.paths['Q'] = '/media/sf_Shared/'
        if self.computer == 'vbox1':
            self.runLAN = True
            self.pdate0 = 0
            #self.pdate1 = 734698
            self.pdate1 = 1000000
            self.game_type = 'vinnare'
        if self.computer == 'vbox2':
            self.runLAN = True
            #self.pdate0 = 734698
            self.pdate0 = 0
            self.pdate1 = 735139
            self.game_type = 'plats'
            #self.game_type = 'vinnare'
        if self.computer == 'vbox3':
            self.runLAN = True
            self.pdate0 = 735139
            self.pdate1 = 735580
            self.game_type = 'plats'
            #self.game_type = 'vinnare'
        if self.computer == 'vbox4':
            self.runLAN = True
            self.pdate0 = 735580
            self.pdate1 = 736021
            #self.game_type = 'vinnare'
            self.game_type = 'plats'
        if self.computer == 'vbox5':
            self.runLAN = True
            self.pdate0 = 736021
            self.pdate1 = 1000000
            #self.game_type = 'vinnare'
            self.game_type = 'plats'
    
        self.configure_db()

    def configure_db(self):
        self.dbconfig = dict()
        self.dbconfig[u'database'] = u'atg'
        self.dbconfig[u'user'] = os.environ['PG_USER']
        self.dbconfig[u'password'] = os.environ['PG_PASS']
        self.dbconfig[u'port'] = 5432
        if self.runlocal:
            self.dbconfig[u'host'] = 'localhost'
        elif self.runLAN:
            self.dbconfig[u'host'] = u'192.168.1.65'
        else:
            self.dbconfig[u'host'] = u'60.241.126.187'

settings = Settings()

class RaceQueue:
    
    def __init__(self):
        self.fill()
    
    def fill(self):
        
        self.IDs = []
        with open(settings.paths['Q'] + 'ids.csv', 'r') as in_file:
            reader = csv.reader(in_file)
            for row in reader:
                self.IDs.append(row)
        
        all_ids = set([x[0] for x in self.IDs if int(x[1]) > settings.pdate0 and int(x[1]) <= settings.pdate1 and x[2] == settings.game_type])
        done_ids = set([x.partition('.')[0] for x in os.listdir(settings.paths['races'])])

        self.Q = list(all_ids.difference(done_ids))
        np.random.shuffle(self.Q)
                
    def pop(self):
        return(self.Q.pop())
    
    def len(self):
        return(len(self.Q))
    
    def is_empty(self):
        return(self.len() == 0)
    

class Database:
    """"""

    #----------------------------------------------------------------------
    def __init__(self, settings, connect=True):
        
        self.connected = False
        self.settings = settings
        self.debug = settings.debug
        self.dbconfig = settings.dbconfig
        if connect:
            self.connect()

    #connect to database
    def connect(self):
        config = dict()	
        self.con = psycopg2.connect("dbname={0} user={1} password={2} host={3} port={4}".format(
                    self.dbconfig[u'database'], 
                        self.dbconfig[u'user'], 
                        self.dbconfig[u'password'], 
                        self.dbconfig[u'host'], 
                        self.dbconfig[u'port']))
        self.cur = self.con.cursor()
        self.connected = True

    
    #disconnect
    def close(self):
        if self.con.closed == 0:
            self.con.close()
        self.connected = False

    #make column name safe for database
    def safeName(self, x):
        y = x.lower()
        y = y.replace('å', 'a')
        y = y.replace('ä', 'a')
        y = y.replace('ö', 'o')
        y = y.replace('á', 'a')
        y = y.replace('à', 'a')
        y = y.replace('ø', 'o')
        y = y.replace('ü', 'u')
        for cr in y:
            crN = ord(cr)
            if (crN < 97 or crN > 122) and (crN < 48 or crN > 57) and crN != 95:
                y = y.replace(cr, '_')
        return y

    #make string value safe for database (by escaping apostrophes)
    def safeVal(self, x):
        if not (isinstance(x, str)):
            return x
        else:
            return x.replace("'", "''")


    #insert table
    def insertTable(self, table, cols_types_defaults, pkey=0, debug=settings.debug, showError=True):

        class Dummy:			
            def execute(self):				
                colStr = ''
                for n, var in enumerate(self.cols_types_defaults):
                    var = list(var)
                    colStr = colStr + var[0] + ' ' + var[1] + ' PRIMARY KEY'*(n==self.pkey)
                    if len(var) == 3:
                        colStr = colStr + ' DEFAULT ' + str(var[2])
                    colStr = colStr + ', '
                colStr = colStr.strip(', ')

                sql = 'CREATE TABLE {0} ({1})'.format(self.table, colStr)
                self.cur.execute(sql)
                self.con.commit()
                return True

        dummy = Dummy()
        dummy.table = table
        dummy.cols_types_defaults = cols_types_defaults
        dummy.pkey = pkey		
        dummy.con = self.con
        dummy.cur = self.cur
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()

    #insert column
    def insertColumn(self, table, col, varType = 'TEXT', default = '', debug=settings.debug):
        class Dummy:			
            def execute(self):
                if self.col != self.safeName(self.col):
                    raise DBerror('Tried to insert unsafe column name')
                if self.default != '':
                    self.default = ' DEFAULT ' + self.default
                self.cur.execute('ALTER TABLE {0} ADD COLUMN {1} {2} {3}'.format(
                                    self.table, 
                                        self.col, 
                                        self.varType, 
                                        self.default))
                self.con.commit()
                return True
        dummy = Dummy()
        dummy.table = table
        dummy.col = col
        dummy.varType = varType	
        dummy.default = default
        dummy.safeName = self.safeName		
        dummy.con = self.con
        dummy.cur = self.cur
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()	

    #get existing column names
    def getColumns(self, thisTable, thisScema = None, debug = settings.debug):

        class Dummy:
            def execute(self):
                self.cur.execute(
                                    "select column_name from information_schema.columns where table_name = '{0}';".format(
                                            self.thisTable)
                                )
                dmp = self.cur.fetchall()
                y = []
                for d in dmp:
                    y.append(d[0])
                return y

        dummy = Dummy()
        dummy.thisTable = thisTable
        dummy.thisScema = thisScema
        dummy.con = self.con
        dummy.cur = self.cur		
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()		



    #update field in database
    def updateField(self, thisTable, changeVar, newVal, selVar, targetVal, debug=settings.debug, commit=True):
        class Dummy:
            def execute(self):
                newVal = str(self.newVal)
                if isinstance(newVal, bool):
                    newVal = str(newVal)
                if isinstance(self.targetVal, int) or isinstance(self.targetVal, float):
                    self.cur.execute("UPDATE {0} SET {1} = '{2}' WHERE {3} = {4}".format(
                                            self.thisTable, 
                                                self.changeVar, 
                                                newVal, 
                                                self.selVar, 
                                                str(self.targetVal)))
                    if self.commit:
                        self.con.commit()
                else:
                    self.cur.execute("UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}'".format(
                                            self.thisTable, 
                                                self.changeVar, 
                                                self.safeVal(newVal), 
                                                self.selVar, 
                                                self.targetVal))
                    if self.commit:
                        self.con.commit()
                return True
        dummy = Dummy()
        dummy.thisTable = thisTable
        dummy.changeVar = changeVar
        dummy.newVal = newVal
        dummy.selVar = selVar
        dummy.targetVal = targetVal
        dummy.safeVal = self.safeVal
        dummy.commit = commit
        dummy.con = self.con
        dummy.cur = self.cur	
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()


    #write to database
    def write2db(self, thisDic, thisTable, useTimeStamp = True, insertKeys=False, debug=settings.debug, commit=True):	
        class Dummy:
            def execute(self):		

                Keys = self.thisDic.keys()
                for k in Keys:
                    if k != self.safeName(k):
                        raise SQLerror('Tried to insert unsafe column name ' + k)
                    if self.insertKeys:
                        self.insertColumn(self.thisTable, k, 'TEXT')

                cols = self.getColumns(self.thisTable)

                if self.useTimeStamp:
                    if 'db_timestamp' not in cols:
                        self.insertColumn(self.thisTable, 'db_timestamp', varType = 'TIMESTAMP')
                    self.thisDic['db_timestamp'] = 'now'
                    Keys = thisDic.keys()

                Ss = ''
                keyStr = ''
                inserts = []	
                for key in Keys:
                    if self.thisDic[key] != 'null' and self.thisDic[key] is not None:
                        inserts.append(self.safeVal(self.thisDic[key]))
                        Ss = Ss + ',%s'
                        keyStr = keyStr + ',' + key
                self.cur.execute('INSERT INTO {0} ({1}) VALUES ({2})'.format(
                                    self.thisTable, 
                                        keyStr.strip(','), 
                                        Ss.strip(',')
                                        ), tuple(inserts))
                if self.commit:
                    self.con.commit()
                return True

        dummy = Dummy()
        dummy.thisTable = thisTable
        dummy.thisDic = thisDic
        dummy.useTimeStamp = useTimeStamp
        dummy.insertKeys = insertKeys
        dummy.safeName = self.safeName
        dummy.insertColumn = self.insertColumn
        dummy.con = self.con
        dummy.cur = self.cur		
        dummy.getColumns = self.getColumns
        dummy.safeVal = self.safeVal
        dummy.commit = commit
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()





    def listCols(self, thisTable, debug=settings.debug):
        class Dummy:
            def execute(self):		
                self.cur.execute("SELECT * FROM " + self.thisTable + " LIMIT 1")
                res = [desc[0] for desc in self.cur.description]
                return(res)
        dummy = Dummy()
        dummy.thisTable = thisTable
        dummy.cur = self.cur		
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()	


    def listTables(self, schema = 'public', debug=settings.debug):
        class Dummy:
            def execute(self):		
                self.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = '{0}'".format(self.schema))
                dmp = self.cur.fetchall()
                res = []
                for d in dmp:
                    res.append(d[0])
                return(res)
        dummy = Dummy()
        dummy.schema = schema
        dummy.cur = self.cur		
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()		


    #drop table
    def dropTable(self, table, debug=settings.debug):
        class Dummy:
            def execute(self):		
                self.cur.execute('DROP TABLE {0}'.format(self.table))
                self.con.commit()
                return True
        dummy = Dummy()
        dummy.table = table
        dummy.con = self.con
        dummy.cur = self.cur			
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()



    # insert list of tuples in table
    def insertMany(self, table, cols, values, debug=settings.debug, commit=True):
        class Dummy:
            def execute(self):		
                if len(self.values) == 0:
                    return False
                ss = ','.join(['%s'] * len(self.values))
                cs = ','.join(self.cols)
                insert_query = 'insert into {0} ({1}) values {2}'.format(self.table, cs, ss)		
                self.cur.execute(insert_query, values)
                if self.commit:
                    self.con.commit()
                return True
        dummy = Dummy()
        dummy.table = table
        dummy.cols = cols
        dummy.values = values
        dummy.con = self.con
        dummy.cur = self.cur
        dummy.commit = commit
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()	



    #Read column values
    def getValues(self, thisCol, thisTable, unique = False, sels = [], debug=settings.debug, limit=None):
        class Dummy:
            def execute(self):		
                def listMe(x):
                    if isinstance(x, list) or isinstance(x, tuple):
                        return(x)
                    else:
                        return([x])

                selStr = 'WHERE '*(len(self.sels) > 0)
                for i, sel in enumerate(listMe(self.sels)):
                    isString = isinstance(sel[2], str)
                    selStr = selStr + "{0} {1} {2}{3}{4} {5}".format(
                                            sel[0], 
                                                sel[1], 
                                                "'"*isString, 
                                                str(sel[2]) if sel[2] is not None else 'Null',
                                            "'"*isString, 
                                                ' AND '*(i<len(self.sels)-1))

                self.thisCol = listMe(self.thisCol)	
                ncols = len(self.thisCol)
                if ncols > 1:
                    self.thisCol = ', '.join(self.thisCol)
                else:
                    self.thisCol = self.thisCol[0]

                sql = 'SELECT {0} {1} FROM {2} {3} {4}'.format(
                                    'DISTINCT'*unique, 
                                        self.thisCol, 
                                        self.thisTable, 
                                        selStr, 
                                        (' limit ' + str(limit))*(limit is not None))

                self.cur.execute(sql)

                x = self.cur.fetchall()

                if ncols == 1:
                    y = []
                    for xi in x:
                        y.append(xi[0])
                    if len(y) == 1:
                        return y[0]
                    else:
                        return(y)
                else:
                    if len(x) == 1:
                        return x[0]
                    else:
                        return(x)

        dummy = Dummy()
        dummy.thisCol = thisCol
        dummy.thisTable = thisTable
        dummy.unique = unique
        dummy.sels = sels
        dummy.con = self.con
        dummy.cur = self.cur
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()		

    def fillChk(self, ll, ul, lim, debug=settings.debug):
        class Dummy:
            def execute(self):
                sql = '''SELECT userid from {0} WHERE 
				public = TRUE AND scraped = TRUE AND filled = FALSE 
				AND userid in 
				(SELECT DISTINCT userid_id FROM {1} WHERE 
				userid_id > {2} AND userid_id < {3}) 
				LIMIT {4}'''.format(self.usertable, self.logtable, self.ll, self.ul, self.lim)
                self.cur.execute(sql)
                dmp = self.cur.fetchall()
                return [x[0] for x in dmp]

        dummy = Dummy()
        dummy.con = self.con
        dummy.cur = self.cur
        dummy.usertable = tables.users
        dummy.logtable = tables.logs
        dummy.ll = ll
        dummy.ul = ul
        dummy.lim = lim

        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()					



    def getSubset(self, thisCol, thisTable, sels=[], unique=False, limit=None, ul=None, ll=None, 
                      onlyEven=None, limvar=None, debug=settings.debug):
        if limvar is None:
            if isinstance(thisCol, list) or isinstance(thisCol, tuple):
                limvar = thisCol[0]
            else:
                limvar = thisCol
        if ul is not None:
            sels.append((limvar, '<=', ul))
        if ll is not None:
            sels.append((limvar, '>=', ll))
        if onlyEven is not None:
            sels.append(('mod({0},2)'.format(limvar), '=', 1-onlyEven))
        return self.getValues(thisCol, thisTable, unique=unique, sels=sels, debug=debug, limit=limit)



    def updateMany(self, thisTable, changeVars, newVals, selVar, targetVal, debug=settings.debug):
        class Dummy:
            def execute(self):
                def listMe(x):
                    if not (isinstance(x, list) or isinstance(x, tuple)):
                        x = [x]
                    return x
                self.changeVars = listMe(self.changeVars)
                self.newVals = listMe(self.newVals)
                changes = ''
                for var, val in zip(self.changeVars, self.newVals):
                    q = '' + "'"*(isinstance(val, str))
                    changes = "{0}{1} = {2}{3}{4}, ".format(changes, var, q, str(val), q)
                changes = changes.strip(', ')
                q = '' + "'"*(isinstance(self.targetVal, str))
                self.cur.execute("UPDATE {0} SET {1} WHERE {2} = {3}{4}{5}".format(
                                    self.thisTable, 
                                        changes, 
                                        self.selVar, 
                                        q, 
                                        str(self.targetVal), 
                                        q))
                self.con.commit()
                return True
        dummy = Dummy()
        dummy.thisTable = thisTable
        dummy.changeVars = changeVars
        dummy.newVals = newVals
        dummy.selVar = selVar
        dummy.targetVal = targetVal
        dummy.safeVal = self.safeVal
        dummy.con = self.con
        dummy.cur = self.cur		
        if not debug:
            return self.timeoutHandler(dummy)
        else:
            return dummy.execute()

    #tell the database that you're alive
    def imStillAlive(self, debug=settings.debug):
        class Dummy:
            def execute(self):
                computers = heroku.getValues('computer_name', 'monitor_computer')
                if settings.computer not in computers:
                    self.write2db(
                                            {
                                                    'computer_name':settings.computer, 
                                                        'ip':br.ip, 
                                                        'activity':'now', 
                                                        'email_sent':True, 
                                                        'speed':0
                                                        }, 
                                                'monitor_computer', 
                                                useTimeStamp=False)
                else:
                    br.getIP()
                    self.updateMany('monitor_computer', 
                                                        ['activity', 'ip', 'speed'], 
                                                                        ['now', br.ip, self.speed], 
                                                                        'computer_name', 
                                                                        settings.computer)
                return True
        settings.iterations = settings.iterations + 1
        if (datetime.now() - self.alivechk).total_seconds() > settings.chkFreq:
            heroku.connect()
            dummy = Dummy()
            dummy.speed = round(60*settings.iterations/(datetime.now() - self.alivechk).total_seconds(),2)
            settings.iterations = 0
            self.alivechk = datetime.now()
            dummy.updateField = self.updateField
            dummy.updateMany = self.updateMany
            dummy.write2db = self.write2db
            if not debug:
                return self.timeoutHandler(dummy)
            else:
                return dummy.execute()
            heroku.close()


    def timeoutHandler(self, obj):
        n = 0
        while (n < 11):
            n = n + 1
            try:
                if (self.con.closed > 0):
                    self.connect()
                obj.con = self.con
                obj.cur = self.cur
                return obj.execute()
            except Exception as e:
                print('Database error:\t{0}').format(str(e))
                with open(settings.error_log, 'ab') as errorOut:
                    errorOut.write(','.join((ctime(),str(e))))
                try: 
                    self.con.rollback()
                except:
                    pass
                try:
                    self.close()
                except:
                    pass
                print('Iteration {0}. Sleeping for 1 minute.'.format(str(n)))
                sleep(60)

                try:
                    try:
                        self.close()
                    except:
                        pass
                    self.connect()
                except:
                    pass

        raise DBerror('Fatal database error.')

    def populate_calendar(self):
        
        db_files = set(self.getValues('file_name', tables.calendar_files))
        disk_files = set(os.listdir(self.settings.paths['calendar']))
        files = list(filter(lambda x: x.endswith('.json'), disk_files.difference(db_files)))
        
        for f in files:
            file_path = ''.join((self.settings.paths['calendar'] + f))
            with open(file_path, 'r') as json_file:
                cal = json.load(json_file)
            if len(cal) > 0:
                out_data = dict()
                out_data['date'] = cal['date']
                out_data['file_name'] = f
                out_data['pdate'] = datetime.toordinal(datetime.strptime(cal['date'], '%Y-%m-%d'))
                out_data['tracks'] = len(cal['tracks'])
                out_data['games'] = len(cal['games'])
                out_data['file_size'] = os.path.getsize(file_path)
                out_data['scraped'] = False
                self.write2db(out_data, tables.calendar_files)

#class Tables:

    #def __init__(self, db, setuptables=True):		
        #self.db = db
        #self.calendar_files = 'calendar_files'
        #self.racedays = 'racedays'
        #self.games = 'games'
        #self.races = 'races'
        #self.info = 'info'


#db = Database(settings=settings)
#tables = Tables(db)
atg = Atg(settings=settings)
atg.get_games()


