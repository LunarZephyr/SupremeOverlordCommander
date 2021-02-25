import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3 as sql

scope  = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('ulala.json', scope)
gss_client = gspread.authorize(creds)

def thread_function(name):
    logging.info("Thread %s: starting", name)

def sheet(sheet):
    try:
        data = gss_client.open(sheet).sheet1
        return pd.DataFrame.from_dict(data.get_all_records())
    except:
        print('Spreadsheet not found')

def teams(team):
    team = team.replace(np.nan, '', regex = True)
    return "```" + team.to_string(index = False, header = True) + "```"

def send_data(data):
    data = data.drop(['Class', 'CP', 'Level'], axis = 1)
    return "```" + data.to_string(index = False, header = True) + "```"

def CP(Clan, CP, growth):
    top = CP[0:29]
    return ("```\n\n\n%s's mean is %d CP\n%s's top 30 member CP average is %d CP\n%s's grew %d CP\n%s's total power is %d CP```"
    %(Clan, CP.mean(), Clan, top.mean(), Clan, growth, Clan, CP.sum()))

def class_list(tank, healer, dps):
    return classes('Tanks', tank), classes('Healers', healer), classes('DPS', dps)

def classes(classes, table):
    return(classes + ": ```" + table.to_string(index = False, header = True) + "```\n")

def filter_class(file):
    tanks = ['Glad', 'War']
    healers = ['Druid', 'Shaman']
    dps = ['Lock', 'Mage', 'Sin', 'Hunter']

    file = file.sort_values(by = ['CP'], ascending = False)

    tank = file[file['Class'].isin(tanks)]
    healer = file[file['Class'].isin(healers)]
    dps = file[file['Class'].isin(dps)]

    return tank, healer, dps

def build_team(file):
    tank, healer, dps = filter_class(file)

    teams = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])

    blank = [[''], [''], [''], ['']]
    blank_rows = pd.DataFrame(blank, columns = ['Teams'])
    format = pd.DataFrame(columns = ['Teams'])

    Elite = False
    atk_count = 3
    def_count = 2

    check = True
    atk = True

    format = format.append({'Teams' : 'Elite'}, ignore_index = True)
    while (atk_count > 0 and tank.shape[0] > 0 and
        healer.shape[0] > 0 and dps.shape[0] > 1 and check == True):

        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])

        dps_count = 1

        temp_team = temp_team.append(tank.iloc[0], ignore_index = True)
        tank = tank.iloc[1:]

        temp_team = temp_team.append(healer.iloc[0], ignore_index = True)
        healer = healer.iloc[1:]

        temp_team = temp_team.append(dps.iloc[0], ignore_index = True)
        dps2 = dps.iloc[1]
        class_check = dps2['Class']

        while class_check == dps.iloc[0]['Class'] and check == True:
            try:
                dps_count += 1
                dps2 = dps.iloc[dps_count]
                class_check = dps2['Class']
            except:
                dps_count = 1
                dps2 = dps.iloc[dps_count]
                check = False

        if Elite == False:
            format = format.append(blank_rows)
            Elite = True
        elif atk_count > 0 and atk == True:
            format = format.append({'Teams' : 'Vanguard ' + str(atk_count)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            atk = False
            atk_count -= 1
        elif def_count > 0 and atk == False:
            atk = True
            format = format.append({'Teams' : 'Rear Guard ' + str(def_count)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            def_count -= 1

        temp_team = temp_team.append(dps2, ignore_index = True)
        dps = dps.drop(dps.index[dps_count])
        dps = dps.iloc[1:]
        dps.reset_index(inplace = True, drop = True)

        teams = teams.append(temp_team, ignore_index = True)
        teams = teams.append(pd.Series(), ignore_index = True)

    teams = pd.concat([format, teams], axis = 1)
    return teams

def build_team_no_elite(file):
    tank, healer, dps = filter_class(file)
    healer.reset_index(inplace = True, drop = True)
    dps.reset_index(inplace = True, drop = True)
    teams = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])

    blank = [[''], [''], [''], ['']]
    blank_rows = pd.DataFrame(blank, columns = ['Teams'])
    format = pd.DataFrame(columns = ['Teams'])

    Elite = False
    atk_count = 3
    def_count = 2

    check = True
    atk = True

    h = 3
    d = 7
    while (atk_count > 1 or def_count > 0):
        print(atk_count)
        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])

        dps_count = d

        temp_team = temp_team.append(tank.iloc[0], ignore_index = True)
        tank = tank.iloc[1:]

        if h >= 0:
            temp_team = temp_team.append(healer.iloc[h], ignore_index = True)
            healer = healer.drop([h])
            h -= 1
        else:
            temp_team = temp_team.append(healer.iloc[0], ignore_index = True)
            healer = healer.iloc[1:]

        temp_team = temp_team.append(dps.iloc[0], ignore_index = True)
        if d > 1:
            dps2 = dps.iloc[d]
            class_check = dps2['Class']
        else:
            d = 1
            dps2 = dps.iloc[d]

        while class_check == dps.iloc[0]['Class'] and check == True:
            if dps_count > 1:
                dps_count -= 1
                dps2 = dps.iloc[dps_count]
                class_check = dps2['Class']
            else:
                dps_count = d
                dps2 = dps.iloc[dps_count]
                check = False

        temp_team = temp_team.append(dps2, ignore_index = True)

        dps = dps.drop([dps_count])
        dps = dps.iloc[1:]
        dps.reset_index(inplace = True, drop = True)
        d -= 2

        if atk_count > 1 and atk == True:
            format = format.append({'Teams' : 'Vanguard ' + str(atk_count)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            atk = False
            atk_count -= 1
        elif def_count > 0 and atk == False:
            atk = True
            format = format.append({'Teams' : 'Rear Guard ' + str(def_count)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            def_count -= 1

        teams = teams.append(temp_team, ignore_index = True)
        teams = teams.append(pd.Series(), ignore_index = True)

    while (atk_count > 0 or Elite == False):
        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])

        temp_team = temp_team.append(tank.iloc[0], ignore_index = True)
        tank = tank.iloc[1:]

        temp_team = temp_team.append(healer.iloc[0], ignore_index = True)
        healer = healer.iloc[1:]

        temp_team = temp_team.append(dps.iloc[:2], ignore_index = True)
        dps = dps.iloc[1:]

        if atk_count > 0:
            format = format.append({'Teams' : 'Vanguard ' + str(atk_count)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            atk_count -= 1
        else:
            format = format.append({'Teams' : 'Elite'}, ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            Elite = True

        teams = teams.append(temp_team, ignore_index = True)
        teams = teams.append(pd.Series(), ignore_index = True)

    teams = pd.concat([format, teams], axis = 1)
    return teams


def leftovers(class_2_roster, class_3_roster):
    temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'CP'])
    if class_2_roster.shape[0] > 1 and class_3_roster.shape[0] >= 1:
        temp_team = temp_team.append(class_2_roster.iloc[0:2])
        class_2_roster = class_2_roster.iloc[2:]
        try:
            temp_team = temp_team.append(class_3_roster.iloc[0:2])
            class_3_roster = class_3_roster.iloc[2:]
        except:
            temp_team = temp_team.append(class_3_roster)
            class_3_roster = class_3_roster[0:0]
            try:
                temp_team = temp_team.append(class_2_roster.iloc[0])
                class_2_roster = class_2_roster.iloc[1:]
            except:
                return temp_team, class_2_roster, class_3_roster
    elif class_2_roster.shape[0] == 1 and class_3_roster.shape[0] > 0:
        temp_team = temp_team.append(class_2_roster.iloc[0])
        class_2_roster = class_2_roster.iloc[1:]
        try:
            temp_team = temp_team.append(class_3_roster.iloc[0:3])
            class_3_roster = class_3_roster.iloc[3:]
        except:
            temp_team = temp_team.append(class_3_roster)
            class_3_roster = class_3_roster[0:0]
    elif class_2_roster.shape[0] == 0 and class_3_roster.shape[0] > 0:
        try:
            temp_team = temp_team.append(class_3_roster[0:4])
            class_3_roster = class_3_roster.iloc[4:]
        except:
            temp_team = temp_team.append(class_3_roster)
            class_3_roster = class_3_roster[0:0]
    elif class_2_roster.shape[0] > 0 and class_3_roster.shape[0] == 0:
        try:
            temp_team = temp_team.append(class_2_roster[0:4])
            class_2_roster = class_2_roster.iloc[4:]
        except:
            temp_team = temp_team.append(class_2_roster)
            class_2_roster = class_2_roster[0:0]
    return temp_team, class_2_roster, class_3_roster
