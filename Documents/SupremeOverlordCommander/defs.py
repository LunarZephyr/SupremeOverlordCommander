import pandas as pd
import numpy as np
import psycopg2 as psql
from datetime import datetime, date

def teams(team):
    team = team.replace(np.nan, '', regex = True)
    return "```" + team.to_string(index = False, header = True) + "```"

def send_data(data):
    return "```" + data.to_string(index = False, header = True) + "```"

def power_return(Clan, power):
    top = power[0:29]
    return ("```\n\n\n%s's mean is %d power\n%s's top 30 member power average is %d power\n%s's total power is %d power```"
    %(Clan, power.mean(), Clan, top.mean(), Clan, power.sum()))

def class_list(tank, healer, dps):
    return classes('Tanks', tank), classes('Healers', healer), classes('DPS', dps)

def classes(classes, table):
    return(classes + ": ```" + table.to_string(index = False, header = True) + "```\n")

def format_find(name):
    return("```%s %s %s %d %d %s```" %(name[1], name[0], name[2], name[3], name[4], name[5]))

def time_check(teams):
    today = datetime.now().date()
    new_col = []
    for i in teams['Updated']:
        try:
            check = (today - datetime.strptime(i, '%m-%d-%Y').date()).days
            if check > 7:
                new_col.append(['> 7 d'])
            else:
                new_col.append([])
        except:
            new_col.append([])
            continue
    try:
        temp_df = pd.DataFrame(new_col, columns = ['Updated'])
        teams['Updated'] = temp_df['Updated']
        teams.fillna('', inplace = True)
    except:
        teams['Updated'] = ''    
    return teams

def id_to_user(bot, dataframe):
    new_col = []
    dataframe = dataframe.drop(['Class', 'power'], axis = 1)
    for i in dataframe['User_ID']:
        new_col.append(bot.fetch_user(i))
    temp_df = pd.DataFrame(new_col, columns = ['User_ID'])
    dataframe['User_ID'] = temp_df['User_ID']
    return dataframe

def all_names(match):
    count = 0
    number = np.arange(1, len(match) + 1)
    match_list = []
    for name in match:
        match_list.append(name)
        try:
            string = '%s\n%d: %s' %(string, number[count], name[0])
        except:
            string = '%d: %s' %(number[count], name[0])
        count += 1
    return match_list, string

def filter_class(file):
    tanks = ['Glad', 'War']
    healers = ['Druid', 'Shaman']
    dps = ['Lock', 'Mage', 'Sin', 'Hunter']
    file = file.sort_values(by = ['power'], ascending = False)
    tank = file[file['Class'].isin(tanks)]
    healer = file[file['Class'].isin(healers)]
    dps = file[file['Class'].isin(dps)]
    return tank, healer, dps

def build_team(file):
    tank, healer, dps = filter_class(file)

    teams = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'power'])

    blank = [[''], [''], [''], ['']]
    blank_rows = pd.DataFrame(blank, columns = ['Teams'])
    format = pd.DataFrame(columns = ['Teams'])

    Elite = False
    atk_count = 0
    def_count = 0

    check = True

    format = format.append({'Teams' : 'Elite'}, ignore_index = True)
    while (def_count < 2  and tank.shape[0] > 0 and
        healer.shape[0] > 0 and dps.shape[0] > 1 and check == True):

        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'power'])

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
        elif atk_count < 3:
            format = format.append({'Teams' : 'Van ' + str(atk_count + 1)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            atk_count += 1
        elif def_count < 2:
            format = format.append({'Teams' : 'Rear ' + str(def_count + 1)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            def_count += 1

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
    teams = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'power'])

    blank = [[''], [''], [''], ['']]
    blank_rows = pd.DataFrame(blank, columns = ['Teams'])
    format = pd.DataFrame(columns = ['Teams'])

    Elite = False
    atk_count = 0
    def_count = 0

    check = True
    atk = True

    h = 3
    d = 7
    while (def_count < 1):
        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'power'])

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

        if atk_count < 3:
            format = format.append({'Teams' : 'Van ' + str(atk_count + 1)}, ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            atk_count += 1
        else:
            format = format.append({'Teams' : 'Rear ' + str(def_count + 1)}, ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            def_count += 1

        teams = teams.append(temp_team, ignore_index = True)
        teams = teams.append(pd.Series(), ignore_index = True)

    while (def_count < 2 or Elite == False):
        temp_team = pd.DataFrame(columns = ['Username', 'Class', 'Level', 'power'])

        temp_team = temp_team.append(tank.iloc[0], ignore_index = True)
        tank = tank.iloc[1:]

        temp_team = temp_team.append(healer.iloc[0], ignore_index = True)
        healer = healer.iloc[1:]

        temp_team = temp_team.append(dps.iloc[:2], ignore_index = True)
        dps = dps.iloc[2:]

        if def_count < 2:
            format = format.append({'Teams' : 'Rear ' + str(def_count + 1)},
            ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            def_count += 1
        else:
            format = format.append({'Teams' : 'Elite'}, ignore_index = True)
            format = format.append(blank_rows, ignore_index = True)
            Elite = True

        teams = teams.append(temp_team, ignore_index = True)
        teams = teams.append(pd.Series(), ignore_index = True)

    teams = pd.concat([format, teams], axis = 1)
    return teams