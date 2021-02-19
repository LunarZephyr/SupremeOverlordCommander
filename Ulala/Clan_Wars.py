import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from Defs import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pickle

scope  = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('ulala.json', scope)
client = gspread.authorize(creds)

averages = pd.read_excel("Weekly_Clan_Averages.xlsx")
#PP_members = pd.read_excel("PP_members.xlsx")
PP_sheet = client.open('PP_members').sheet1
SS_sheet = client.open('SS_members').sheet1
#NN_sheet = client.open('NN_members').sheet1

PP_members = pd.DataFrame.from_dict(PP_sheet.get_all_records())
SS_members = pd.DataFrame.from_dict(SS_sheet.get_all_records())
#NN_members = pd.DataFrame.from_dict(NN_sheet.get_all_records())

#filters
PP_members, PP_tanks, PP_healers, PP_dps = filter_class(PP_members)
SS_members, SS_tanks, SS_healers, SS_dps = filter_class(SS_members)
#NN_members, NN_tanks, NN_healers, NN_dps = filter_class(NN_members)

#insert weekly average to averages
new_row = {'Date' : datetime.date(datetime.now()),
           'Week' : averages.shape[0] + 1,
           'PlanetaryPower (avg CP)' : PP_members['CP'].mean(),
           'SolarSurfers (avg CP)' : SS_members['CP'].mean()}
           #'NauticalNebula (avg CP)' : NN_members['CP'].mean()}
averages = averages.append(new_row, ignore_index = True)
#averages.to_excel('Weekly_Clan_Averages.xlsx', index = False)

#class counts
#print('PP_Tanks: %d\t PP_Healers: %d\t PP_DPS: %d' %(PP_tanks.shape[0],
#PP_healers.shape[0], PP_dps.shape[0]))
#print('SS_Tanks: %d\t SS_Healers: %d\t SS_DPS: %d' %(SS_tanks.shape[0],
#SS_healers.shape[0], SS_dps.shape[0]))

#save class files to csv
#PP_tanks.to_excel('PP_tanks.xlsx', index = False)
#PP_healers.to_excel('PP_healers.xlsx', index = False)
#PP_dps.to_excel('PP_dps.xlsx', index = False)
#SS_tanks.to_excel('SS_tanks.xlsx', index = False)
#SS_healers.to_excel('SS_healers.xlsx', index = False)
#SS_dps.to_excel('SS_dps.xlsx', index = False)

#teams
PP_teams = build_team(PP_tanks, PP_healers, PP_dps)
SS_teams = build_team(SS_tanks, SS_healers, SS_dps)
#NN_teams = build_team(NN_tanks, NN_healers, NN_dps)

PP_teams.to_excel('PP_teams.xlsx', index = False)
SS_teams.to_excel('SS_teams.xlsx', index = False)
#NN_teams.to_excel('NN_teams.xlsx', index = False)

#average CP plots
week = averages['Week']
PP = averages['PlanetaryPower (avg CP)']
SS = averages['SolarSurfers (avg CP)']
#NN = averages['NauticalNebula (avg CP)'][16:]
#NN = NN[16:]

print('\nPlanetaryPower mean is ', PP_members['CP'].mean(), 'CP')
print("PlanetaryPower grew", PP.values[-1] - PP.values[-2], "CP")
print("PlanetaryPower's total power is %d CP" %(PP_members['CP'].sum()))

print('\nSolarSurfers mean is ', SS_members['CP'].mean(), 'CP')
print("SolarSurfers grew", SS.values[-1] - SS.values[-2], "CP")
print("SolarSurfers' total power is %d CP" %(SS_members['CP'].sum()))

#print('\nNauticalNebula mean is ', NN_members['CP'].mean(), 'CP')
#print("NauticalNebula grew", NN.values[-1] - NN.values[-2], "CP")

PP_intercept, PP_slope = linfit(week, PP)
SS_intercept, SS_slope = linfit(week, SS)
NN_intercept, NN_slope = linfit(week, NN)

plot = plt.figure(figsize = (7, 10))
ppss = plot.add_subplot(2, 1, 1)
ppss.plot(week, PP, 'mo')
ppss.plot(week, PP_intercept + PP_slope*week, "m--", label = "PlanetaryPower", alpha = 0.6)
ppss.plot(week, SS, 'ro')
ppss.plot(week, SS_intercept + SS_slope*week, "r--", label = "SolarSurfers", alpha = 0.6)

ppss.set_xticks(range(1, week.values[-1] + 1), 2)
ppss.set_title('Average CP over time')
ppss.set_xlabel('Time in Weeks')
ppss.set_ylabel('Average CP')
ppss.legend(loc = 'upper left')
ppss.grid(b = True, which = 'major', color = '#666666', linestyle = '-', alpha = 0.1)

nn = plot.add_subplot(2, 1, 2)
nn.plot(week[16:] - 16, NN, 'bo')
nn.plot(week[16:] - 16, NN_intercept + NN_slope*(week[16:] - 16), "b--", label = "NauticalNebula", alpha = 0.6)

nn.set_xticks(range(1, week.values[-1] + 1))
nn.set_title('Average CP over time')
nn.set_xlabel('Time in Weeks')
nn.set_ylabel('Average CP')
nn.legend(loc = 'upper left')
nn.grid(b = True, which = 'major', color = '#666666', linestyle = '-', alpha = 0.1)

plt.tight_layout()
plt.show(block = True)
