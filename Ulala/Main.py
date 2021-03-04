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
import time
import schedule
import sqlite3 as sql
import threading
from discord.ext import tasks, commands

#SS_members = sheet('SS_members')

load_dotenv()
TOKEN = os.getenv('API_KEY')
bot = commands.Bot(command_prefix = '$')

PPconn = sql.connect('PP_members.db')
SSconn = sql.connect('SS_members.db')
pc = PPconn.cursor()
sc = SSconn.cursor()

clan_list = ['PP', 'SS']
role_list = ['Glad', 'War', 'Sin', 'Hunter', 'Lock', 'Mage', 'Druid', 'Shaman']

scope  = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('ulala.json', scope)
gss_client = gspread.authorize(creds)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(status = discord.Status.online, activity = discord.Game("Not fit to rule"), afk = False)

@bot.command(
    help = "The standard 'build teams' function. Assigns teams based on power, from Elite to Van 3 all the way down to Van 1. The teams are sent to the appropriate channels",
    brief = "Contact admins if this command is needed"
)
@commands.has_permissions(administrator = True)
async def build(message, clan):
    if clan.lower() == 'all' or clan.upper() == clan_list[0]:
        PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
        PP_teams = build_team(PP_members.iloc[:, :4])
        channel = bot.get_channel(741354032890773595)
        await channel.purge(limit = 10)
        await channel.send(teams(PP_teams))
    if clan.lower() == 'all' or clan.upper() == clan_list[1]:
        SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
        SS_teams = build_team(SS_members.iloc[:, :4])
        channel = bot.get_channel(741354523947302934)
        await channel.purge(limit = 10)
        await channel.send(teams(SS_teams))

@bot.command(
    help = "The modified 'build teams' function. Van 3 to Rear 1 are mediated, with the rest filling into Van 1 and Elite. The teams are sent to the appropriate channels",
    brief = "Contact admins if this command is needed"
)
@commands.has_permissions(administrator = True)
async def nbuild(message, clan):
    if clan.lower() == 'all' or clan.upper() == clan_list[0]:
        PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
        PP_teams = build_team_no_elite(PP_members.iloc[:, :4])
        channel = bot.get_channel(741354032890773595)
        await channel.purge(limit = 10)
        await channel.send(teams(PP_teams))
    if clan.lower() == 'all' or clan.upper() == clan_list[1]:
        SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
        SS_teams = build_team_no_elite(SS_members.iloc[:, :4])
        channel = bot.get_channel(741354523947302934)
        await channel.purge(limit = 10)
        await channel.send(teams(SS_teams))

@bot.command(
    help = "Filters the database and returns tanks, healers, and the top 30 dps. Shows each character's CP, level, and date of last update",
    brief = 'Contact admins if command is needed'
)
@commands.has_permissions(administrator = True)
async def member(message):
    PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
    SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
    PP_tank, PP_healer, PP_dps = filter_class(PP_members)
    SS_tank, SS_healer, SS_dps = filter_class(SS_members)
    PP_tank, PP_healer, PP_dps = class_list(PP_tank, PP_healer, PP_dps.head(25))
    SS_tank, SS_healer, SS_dps = class_list(SS_tank, SS_healer, SS_dps.head(25))
    channel = bot.get_channel(810269541682642994)
    await channel.purge(limit = 10)
    await channel.send(PP_tank)
    await channel.send(PP_healer)
    await channel.send(PP_dps)
    channel = bot.get_channel(810269806934491186)
    await channel.purge(limit = 10)
    await channel.send(SS_tank)
    await channel.send(SS_healer)
    await channel.send(SS_dps)

@bot.command(
    help = 'Calculates averages and change of averages and sends it to the appropriate channels',
    brief = 'Contact admins if this command is needed'
)
@commands.has_permissions(administrator = True)
async def average(message, clan):
    averages = pd.read_excel("Weekly_Clan_Averages.xlsx")
    #get records
    PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
    SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
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
    channel = bot.get_channel(741356369671618611)
    await channel.purge(limit = 10)
    await channel.send(CP_return("PlanetaryPower", PP_members['CP'], PP.values[-1] - PP.values[-2]))
    channel = bot.get_channel(741356392337899633)
    await channel.purge(limit = 10)
    await channel.send(CP_return("SolarSurfers", SS_members['CP'], SS.values[-1] - SS.values[-2]))

@bot.command(
    help = 'Adds a new character to the database',
    brief = 'Contact admin/elder if this command is needed'
)
#@commands.has_permissions(administrator = True)
@commands.has_role('Elder')
async def add(message):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    today = datetime.now().strftime('%m-%d-%Y')
    await message.send("Which Clan? (eg. PP)")
    clan = await bot.wait_for("message", check = check, timeout = 120)
    if clan.content.upper() in clan_list:
        await message.send("What's your username? (Case sensitive)")
        name = await bot.wait_for("message", check = check, timeout = 120) 
        await message.send("What's your class? Please pick from the following: Glad, War, Druid, Shaman, Sin, Lock, Hunter, Mage")
        role = await bot.wait_for("message", check = check, timeout = 120)
        if role.content.lower().capitalize() in role_list:
            await message.send("What's your level?")
            level = await bot.wait_for('message', check = check, timeout = 120)
            try:
                level = int(level.content)
            except:
                await message.send('An integer was not entered. Please try again')
                return
            await message.send("What's your CP?")
            CP = await bot.wait_for("message", check = check, timeout = 120)
            try:    
                CP = int(CP.content)
            except:
                await message.send('Message timeout or integer was not entered. Please try again')
                return
            await message.send("Is this correct (yes/no):\n```Username: %s\nClass: %s\nLevel: %s\nCP: %s```" %(name.content, role.content, level, CP))
            confirm = await bot.wait_for("message", check = check, timeout = 120)
            if confirm.content.lower().startswith('y'):
                if clan.content.upper() == clan_list[0]:
                    pc.execute('''INSERT INTO PP_members (Username, Class, Level, CP, Updated)
                    VALUES (?, ?, ?, ?, ?)''', (name.content, role.content.lower().capitalize(), level, CP, today))
                    PPconn.commit()
                    await message.channel.send("Character Successfully Added")
                else:
                #elif clan.content.upper() == clan_list[1]
                    sc.execute('''INSERT INTO SS_members (Username, Class, Level, CP, Updated)
                    VALUES (?, ?, ?, ?, ?)''', (name.content, role.content.lower().capitalize(), level, CP, today))
                    SSconn.commit()
                    await message.send("Character Successfully Added")
            else:
                await message.send("Please try again")
        else:
            await message.send('Class input was wrong. Please try again')
    else: 
        await message.send('Clan input was wrong. Please try again')

@bot.command(
    help = 'Deletes an existing character from the database',
    brief = 'Contact admin/elder if this command is needed'
)
#@commands.has_permissions(administrator = True)
@commands.has_role('Elder')
async def delete(message):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.send("Which Clan? (eg. PP)")
    clan = await bot.wait_for("message", check = check)
    if clan.content.upper() in clan_list:
        await message.send("What's your username? (Case sensitive)")
        name = await bot.wait_for("message", check = check)
        if clan.content.upper() == clan_list[0]:
            pc.execute('''DELETE FROM PP_members WHERE Username=?''', (name.content, ))
            PPconn.commit()
            await message.send("Character successfully deleted")
        else:
            sc.execute('''DELETE FROM SS_members WHERE Username=?''', (name.content, ))
            SSconn.commit()
            await message.send("Character successfully deleted")
    else:
        message.send('Clan input was wrong. Please try again')

@bot.command(
    help = 'Displays the last update time of each character',
    brief = 'Contact admins or elders if this command is needed'
)
#@commands.has_permissions(administrator = True)
@commands.has_role('Elder')
async def status(message, clan):
    if clan.upper() == clan_list[0] or clan.lower() == 'all':
        PP_members = pd.read_sql_query('SELECT * FROM PP_members;', PPconn)
        tank, healer, dps = filter_class(PP_members)
        await message.send('tanks\n' + send_data(tank))
        await message.send('healers\n' + send_data(healer))
        print(send_data(dps))
        await message.send('dps\n' + send_data(dps))
    if clan.upper() == clan_list[1] or clan.lower() == 'all':
        SS_members = pd.read_sql_query('SELECT * FROM SS_members;', SSconn)
        tank, healer, dps = filter_class(SS_members)
        await message.send('tanks\n' + send_data(tank))
        await message.send('healers\n' + send_data(healer))
        await message.send('dps\n' + send_data(dps))
    
@bot.command(
    help = 'Searches database for the character and outputs Discord User who owns the character if user is in the database',
    brief = "Find character's user"
)
async def find(message, user):
    registry = gss_client.open('Discord Registry').sheet1
    remove = [e[0:5] for e in registry.get_all_values()]
    registry = pd.DataFrame(remove[3:], columns = remove[2])
    for i in range(len(registry.columns) - 1):
        col_name = 'Account ' + str(i + 1)
        search = registry[registry[col_name] == user]
        if not search.empty:
            break
    try:
        await message.send(search['Discord Name'].values[0])
    except:
        await message.send('User unknown')

@bot.command(
    help = 'Update an existing character in the database',
    brief = 'Update an existing character in the database'
)
async def update(message):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    today = datetime.now().strftime('%m-%d-%Y')
    await message.send("Which Clan? (eg. PP)")
    clan = await bot.wait_for("message", check = check, timeout = 120)
    if clan.content.upper() in clan_list:
        await message.send("What's your username?")
        name = await bot.wait_for("message", check = check, timeout = 120)
        if clan.content.upper() == 'PP':
            match = pc.execute('''SELECT Username FROM PP_members WHERE Username LIKE ?''', ('%'+name.content+'%', )).fetchall()
            if match == []:
                await message.send('No match found')
                return
            elif len(match) == 1:
                name = match[0][0]
            else:
                match_list, string_list = all_names(match)
                await message.channel.send("Which character is yours?\n```%s```" %(string_list))
                value = await bot.wait_for("message", check = check)
                name = match_list[int(value.content) - 1]
        elif clan.content.upper() == 'SS':
            match = sc.execute('''SELECT Username FROM SS_members WHERE Username LIKE ?''', ('%'+name.content+'%', )).fetchall()
            if match == []:
                await message.send('No match found')
                return
            elif len(match) == 1:
                name = match[0][0]
            else:
                match_list, string_list = all_names(match)
                await message.send("Which character is yours?\n```%s```" %(string_list))
                value = await bot.wait_for("message", check = check)
                name = match_list[int(value.content) - 1]                         
        await message.send("What's your level?")
        level = await bot.wait_for("message", check = check, timeout = 120)
        try:
            level = int(level.content)
        except:
            await message.send('An integer was not entered. Please try again')
            return
        await message.send("What's your CP?")
        CP = await bot.wait_for("message", check = check, timeout = 120)
        try:
            CP = int(CP.content)
        except:
            await message.send('An integer was not entered. Please try again')
            return
        await message.send("Is this correct (yes/no):\n```Username: %s\nLevel: %s\nCP: %s```" %(name, level, CP))
        confirm = await bot.wait_for("message", check = check)
        if confirm.content.lower().startswith('y'):
            if clan.content.upper() == 'PP':
                pc.execute('''UPDATE PP_members SET Level=?, CP=?, Updated =? WHERE Username=?''',
                (level, CP, today, name, ))
                PPconn.commit()
                await message.send("Character successfully updated")
            else:
                sc.execute('''UPDATE SS_members SET Level=?, CP=?, Updated =? WHERE Username=?''', 
                (level, CP, today, name, ))
                SSconn.commit()
                await message.send("Character successfully updated")
        else:
            await message.send("Please try again")
    else:
        await message.send('Clan input was wrong. Please try again')

@bot.command(
    help = 'Change the name of an existing character in the database',
    brief = 'Change the name of an existing character in the database'
)
async def change(message):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.channel.send("Which Clan? (PP or SS)")
    clan = await bot.wait_for("message", check = check, timeout = 120)
    if clan.content.upper() in clan_list:
        await message.send("What is your new username? (Case sensitive)")
        new_name = await bot.wait_for("message", check = check, timeout = 120)
        await message.send("What was your previous username? (Case sensitive)")
        former_name = await bot.wait_for("message", check = check, timeout = 120)
        if clan.content.upper() == 'PP':
            match = pc.execute('''SELECT Username FROM PP_members WHERE Username LIKE ?''', ('%'+former_name.content+'%', )).fetchall()
            if match == []:
                await message.send('No match found')
                return
            elif len(match) == 1:
                former_name = match[0][0]
            else:
                match_list, string_list = all_names(match)
                await message.send("Which character is yours?\n```%s```" %(string_list))
                value = await bot.wait_for("message", check = check)
                former_name = match_list[int(value.content) - 1]
            pc.execute('''UPDATE PP_members SET Username =? WHERE Username =?''',
            (new_name.content, former_name, ))
            PPconn.commit()
            await message.send("Name successfully changed")
        else:
            match = sc.execute('''SELECT Username FROM SS_members WHERE Username LIKE ?''', ('%'+former_name.content+'%', )).fetchall()
            if match == []:
                await message.send('No match found')
                return
            elif len(match) == 1:
                former_name = match[0][0]
            else:
                match_list, string_list = all_names(match)
                await message.channel.send("Which character is yours?\n```%s```" %(string_list))
                value = await bot.wait_for("message", check = check)
                former_name = match_list[int(value.content) - 1]
            sc.execute('''UPDATE SS_members SET Username =? WHERE Username =?''',
            (new_name.content, former_name, ))
            SSconn.commit()
            await message.channel.send("Name successfully changed")
    else:
        await message.channel.send('Clan input was wrong. Please try again')

bot.run(TOKEN)
