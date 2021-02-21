import asyncio
import discord
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pickle
import re
from Defs import *
from datetime import datetime
import sqlite3 as sql

load_dotenv()
TOKEN = os.getenv('API_KEY')
client = discord.Client()

PPconn = sql.connect('PP_members.db')
SSconn = sql.connect('SS_members.db')
pc = PPconn.cursor()
sc = SSconn.cursor()

clan_list = ['PP', 'SS']
role_list = ['glad', 'war', 'sin', 'hunter', 'lock', 'mage', 'druid', 'shaman']

scope  = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('ulala.json', scope)
gss_client = gspread.authorize(creds)

registry = gss_client.open('Discord Registry').sheet1
remove = [e[0:5] for e in registry.get_all_values()]
registry = pd.DataFrame(remove[3:], columns = remove[2])

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

#Event Listener for new message
@client.event
async def on_message(message):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    #checks if the message that was sent is equal to "hello"
    if message.content.startswith('!find'):
        try:
            find = message.content.split()[1]
            for i in range(len(registry.columns) - 1):
                col_name = 'Account ' + str(i + 1)
                search = registry[registry[col_name] == find]
                if not search.empty:
                    break
            await message.channel.send(search['Discord Name'].values[0])
        except:
            await message.channel.send('User unknown')

    elif message.content == '!PPbuild':
        if message.author.guild_permissions.administrator == True:
            #get records
            #PP_members = sheet('PP_members')
            PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
            PP_teams = build_team(PP_members)
            channel = client.get_channel(741354032890773595)
            await channel.purge(limit = 10)
            await channel.send(teams(PP_teams))

    elif message.content == '!SSbuild':
        if message.author.guild_permissions.administrator == True:
            #SS_members = sheet('SS_members')
            SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
            SS_teams = build_team(SS_members)
            channel = client.get_channel(741354523947302934)
            await channel.purge(limit = 10)
            await channel.send(teams(SS_teams))

    elif message.content == '!average':
            averages = pd.read_excel("Weekly_Clan_Averages.xlsx")
            #get records
            PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
            SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
            #PP_members = sheet('PP_members')
            #SS_members = sheet('SS_members')
            #add averages to averages excel sheet1
            new_row = {'Date' : datetime.date(datetime.now()),
                    'Week' : averages.shape[0] + 1,
                    'PlanetaryPower (avg CP)' : PP_members['CP'].mean(),
                    'SolarSurfers (avg CP)' : SS_members['CP'].mean()}
            averages = averages.append(new_row, ignore_index = True)
            averages.to_excel('Weekly_Clan_Averages.xlsx', index = False)

            PP_members = PP_members.sort_values(by = ['CP'], ascending = False)
            SS_members = SS_members.sort_values(by = ['CP'], ascending = False)

            PP = averages['PlanetaryPower (avg CP)']
            SS = averages['SolarSurfers (avg CP)']

            channel = client.get_channel(741356369671618611)
            await channel.purge(limit = 10)
            await channel.send(CP("PlanetaryPower", PP_members['CP'], PP.values[-1] - PP.values[-2]))
            channel = client.get_channel(741356392337899633)
            await channel.purge(limit = 10)
            await channel.send(CP("SolarSurfers", SS_members['CP'], SS.values[-1] - SS.values[-2]))

    elif message.content == '!PPnbuild':
        if message.author.guild_permissions.administrator == True:
            #PP_members = sheet('PP_members')
            PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
            PP_teams = build_team_no_elite(PP_members)
            channel = client.get_channel(741354032890773595)
            await channel.purge(limit = 10)
            await channel.send(teams(PP_teams))
            
    elif message.content == '!SSnbuild':
        if message.author.guild_permissions.administrator == True:
            #SS_members = sheet('SS_members')
            SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
            SS_teams = build_team_no_elite(SS_members)
            channel = client.get_channel(741354523947302934)
            await channel.purge(limit = 10)
            await channel.send(teams(SS_teams))

    elif message.content == '!add':
        await message.channel.send("Which Clan? (PP or SS)")
        clan = await client.wait_for("message", check = check)
        if clan.content in clan_list:
            await message.channel.send("What's your username? (Case sensitive)")
            name = await client.wait_for("message", check = check) 
            await message.channel.send("What's your class? (glad, war, druid, shaman, sin, lock, hunter, mage)?")
            role = await client.wait_for("message", check = check)
            if role.content in role_list:
                await message.channel.send("What's your level?")
                level = await client.wait_for("message", check = check)
                await message.channel.send("What's your CP?")
                CP = await client.wait_for("message", check = check)
                await message.channel.send("Is this correct (Please answer with 'yes' or 'no'):\n```Username: %s\nClass: %s\nLevel: %s\nCP: %s```" %(name.content, role.content, level.content, CP.content))
                confirm = await client.wait_for("message", check = check)
                if confirm.content == 'yes':
                    if clan.content == 'PP':
                        pc.execute('''INSERT INTO PP_members (Username, Class, Level, CP)
                        VALUES (?, ?, ?, ?)''', (name.content, role.content, int(level.content), int(CP.content)))
                        PPconn.commit()
                        await message.channel.send("Character Successfully Added")
                    elif clan.content == 'SS':
                        sc.execute('''INSERT INTO SS_members (Username, Class, Level, CP)
                        VALUES (?, ?, ?, ?)''', (name.content, role.content, int(level.content), int(CP.content)))
                        SSconn.commit()
                        await message.channel.send("Character Successfully Added")
                else:
                    await message.channel.send("Please try again")
            else:
                await message.channel.send('Class input was wrong. Remeber it is Case Sensitive. Please try again')
        else: 
            await message.channel.send('Clan input was wrong. Remember it is Case Sensitive. Please try again')

    elif message.content == '!delete':
        await message.channel.send("Which Clan? (PP or SS)")
        clan = await client.wait_for("message", check = check)
        if clan.content in clan_list:
            await message.channel.send("What's your username? (Case sensitive)")
            name = await client.wait_for("message", check = check)
            if clan.content == 'PP':
                try:
                    pc.execute('''DELETE FROM PP_members WHERE Username=?''', (name.content, ))
                    PPconn.commit()
                    await message.channel.send("Character successfully deleted")
                except: 
                    await message.channel.send("Character not found - could not be deleted")
            elif clan.content == 'SS':
                try:
                    sc.execute('''DELETE FROM SS_members WHERE Username=?''', (name.content, ))
                    SSconn.commit()
                    await message.channel.send("Character successfully deleted")
                except:
                    await message.channel.send("Character not found - could not be deleted")
        else:
            message.channel.send('Clan input was wrong. Remember it is Case Sensitive. Please try again')

    elif message.content == '!update':
        await message.channel.send("Which Clan? (PP or SS)")
        clan = await client.wait_for("message", check = check)
        if clan.content in clan_list:
            await message.channel.send("What's your username? (Case sensitive)")
            name = await client.wait_for("message", check = check)
            await message.channel.send("What's your level?")
            level = await client.wait_for("message", check = check)
            await message.channel.send("What's your CP?")
            CP = await client.wait_for("message", check = check)
            await message.channel.send("Is this correct (Please answer with 'yes' or 'no'):\n```Username: %s\nLevel: %s\nCP: %s```" %(name.content, level.content, CP.content))
            confirm = await client.wait_for("message", check = check)
            if confirm.content == 'yes':
                if clan.content == 'PP':
                    try: 
                        pc.execute('''UPDATE PP_members SET Level=?, CP=? WHERE Username=?''',
                        (int(level.content), int(CP.content), name.content, ))
                        PPconn.commit()
                        await message.channel.send("Character successfully updated")
                    except:
                        await message.channel.send("Character not found. If you are new, please use the !add command. If you are not, make sure your username was inputted properly")
                elif clan.content == 'SS':
                    try:
                        sc.execute('''UPDATE SS_members SET Level=?, CP=? WHERE Username=?''', 
                        (int(level.content), int(CP.content), name.content, ))
                        SSconn.commit()
                        await message.channel.send("Character successfully updated")
                    except:
                        await message.channel.send("Character not found. If you are new, please use the !add command. If you are not, make sure your username was inputted properly")
            else:
                await message.channel.send("Please try again")
        else:
            await message.channel.send('Clan input was wrong. Please try again')

    elif message.content == '!change username':
        await message.channel.send("Which Clan? (PP or SS)")
        clan = await client.wait_for("message", check = check)
        if clan.content in clan_list:
            await message.channel.send("What was your username? (Case sensitive)")
            former_name = await client.wait_for("message", check = check)
            await message.channel.send("What is your new username? (Case sensitive)")
            new_name = await client.wait_for("message", check = check)
            if clan.content == 'PP':
                try:
                    pc.execute('''UPDATE PP_members SET Username =? WHERE Username =?''',
                    (new_name.content, former_name.content, ))
                    PPconn.commit()
                    await message.channel.send("Name successfully changed")
                except:
                    await message.channel.send("Character not found. Make sure username was inputted properly")
            elif clan.content == 'SS':
                try:
                    sc.execute('''UPDATE SS_members SET Username =? WHERE Username =?''',
                    (new_name.content, former_name.content, ))
                    SSconn.commit()
                    await message.channel.send("Name successfully changed")
                except:
                    await message.channel.send("Character not found. Make sure username was inputted properly")
        else:
            await message.channel.send('Clan input was wrong. Please try again')

    elif message.content == '!filter':
        if message.author.guild_permissions.administrator == True:
            PP_members = sheet('PP_members')
            SS_members = sheet('SS_members')
            PP_tank, PP_healer, PP_dps = filter_class(PP_members)
            SS_tank, SS_healer, SS_dps = filter_class(SS_members)
            PP_tank, PP_healer, PP_dps = class_list(PP_tank, PP_healer, PP_dps.head(25))
            SS_tank, SS_healer, SS_dps = class_list(SS_tank, SS_healer, SS_dps.head(25))
            channel = client.get_channel(810269541682642994)
            await channel.purge(limit = 10)
            await channel.send(PP_tank)
            await channel.send(PP_healer)
            await channel.send(PP_dps)
            channel = client.get_channel(810269806934491186)
            await channel.purge(limit = 10)
            await channel.send(SS_tank)
            await channel.send(SS_healer)
            await channel.send(SS_dps)

    elif message.content == '!raffle':
        if message.author.guild_permissions.administrator == True:
            PP = sheet('PP_participation')
            SS = sheet('SS_participation')
            combine = pd.concat([PP, SS])
            found = False
            while not found:
                user = combine.sample(replace = False)
                for i in range(len(registry.columns) - 1):
                    col_name = 'Account ' + str(i + 1)
                    search = registry[registry[col_name] == user]
                    if not search.empty:
                        break
                try:
                    await message.channel.send("%s's character %s has been chosen"
                    %(search['Discord Name'].values[0], user['Username'].values[0]))
                    found = True
                except:
                    continue

client.run(TOKEN)
