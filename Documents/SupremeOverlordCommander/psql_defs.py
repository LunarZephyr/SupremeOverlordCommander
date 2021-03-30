import pandas as pd
import numpy as np
import psycopg2 as psql
from datetime import datetime, date
import sqlite3 as sql
import asyncio
from defs import *
from async_defs import *
import discord

conn = psql.connect("host = localhost dbname = maindb user = fomalhaut password = fomalumn")
c = conn.cursor()

role_list = ['Glad', 'War', 'Sin', 'Hunter', 'Lock', 'Mage', 'Druid', 'Shaman']

def registration_check(message, bot):
    c.execute('''SELECT commands FROM Servers WHERE Server_ID = (%s)''', (message.guild.id, ))
    if c.fetchall()[0][0] == 'yes':
        return True
    else:
        return False
    
def deregister(before, after):
    if len(after.roles) < len(before.roles):
        for role in before.roles:
            if role not in after.roles:
                oldRole = role
        if oldRole.id == 824766740159266826:
            try:
                c.execute('''UPDATE Servers SET Commands = (%s) WHERE Representative = (%s)''', ('no', before.id))
                conn.commit()
            except:
                conn.rollback()

async def search_clan(message, bot):
    abv = await get_clan_abrv(message, bot)
    c.execute('''SELECT Clan_Name FROM Clans WHERE clan_abbreviation ~* (%s) AND server_id = (%s)''', (abv, message.guild.id, ))
    return c.fetchall()[0][0]

def db_add_server(bot, guild):
    try:
        c.execute('''INSERT INTO Servers (Server_ID, Server_Name) VALUES (%s, %s)''', (guild.id, str(bot.get_guild(guild.id))))
        conn.commit()
    except:
        conn.rollback()

async def db_add_clan(message, bot):
    clan, abv = await get_clan_name(message, bot)
    try:
        await get_confirm_clan(message, bot, clan, abv)
    except:
        await message.send('Please try again')
        return
    try:
        c.execute('''INSERT INTO Clans (Server_ID, Clan_Name, Clan_Abbreviation) VALUES (%s, %s, %s)''', (message.guild.id, clan, abv))
        conn.commit()
        await message.send('The clan was successfully registered. Please remember the abbreviation used')
    except:
        conn.rollback()
        await message.send('A clan with that name already exists')
        return

async def db_add_member(message, bot):
    today = datetime.now().strftime('%m-%d-%Y')
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    username = await get_username(message, bot)
    role = await get_class(message, bot)
    try:
        level, power = await get_level_power(message, bot)
    except:
        await message.send('An integer was not inputted. Please try again')
        return
    try:
        await get_confirm_member(message, bot, username, role, level, power)
    except:
        await message.send('Please try again')
        return
    try:
        c.execute('''INSERT INTO Members (Clan_Name, Username, Class, Level, power, Updated) VALUES (%s, %s, %s, %s, %s, %s)''', (clan, username, role, level, power, today))
        conn.commit()
        await message.send('Character successfully added')
        return
    except:
        conn.rollback()
        await message.send('Character was not able to be added')

async def db_delete_members(message, bot):
    try:
        clan = await search_clan(message, bot)
    except: 
        await message.send('Clan was not found. Please try again')
        return
    users = await get_username(message, bot)
    users = users.split(', ')
    for username in users:
        try:
            c.execute('''DELETE FROM Members WHERE Username = (%s) AND Clan_Name = (%s)''', (username, clan))
            conn.commit()
            await message.send('%s succesfully deleted' %(username))
        except:            
            conn.rollback()
            await message.send('%s could not be deleted' %(username))  

async def build_teams(message, bot):
    try:
        clan = await search_clan(message, bot)
    except: 
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT username, class, level, power, updated FROM Members WHERE Clan_Name = (%s)''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Username', 'Class', 'Level', 'power', 'Updated']
    team = build_team(member)
    await message.channel.send(teams(team))

async def build_teams_toss_elite(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT username, class, level, power, updated FROM Members WHERE Clan_Name = (%s)''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Username', 'Class', 'Level', 'power', 'Updated']
    team = build_team_no_elite(member)
    await message.channel.send(teams(team))

async def list_members(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT username, class, level, power, updated FROM Members WHERE Clan_Name = (%s)''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Username', 'Class', 'Level', 'power', 'Updated']
    member = time_check(member)
    tank, healer, dps = filter_class(member)
    tank, healer, dps = class_list(tank, healer, dps.head(25))
    await message.channel.send(tank)
    await message.channel.send(healer)
    await message.channel.send(dps)

async def get_averages(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT power FROM Members WHERE Clan_Name = (%s)''', (clan, ))
    power = pd.DataFrame(c.fetchall())
    power.columns = ['power']
    power = power.sort_values(by = ['power'], ascending = False)
    await message.channel.send(power_return(clan, power['power']))

async def show_status(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT username, class, power, updated FROM Members WHERE Clan_Name = (%s)''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Username', 'Class', 'power', 'Updated']
    tank, healer, dps = filter_class(member)
    await message.send('tanks\n' + send_data(tank.drop(['power'], axis = 1)))
    await message.send('healers\n' + send_data(healer.drop(['power'], axis = 1)))
    await message.send('dps\n' + send_data(dps.drop(['power'], axis = 1)))

async def map_discord_to_ingame(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT Discord_ID, username, power, class FROM Members WHERE Clan_Name = (%s) AND Discord_ID IS NOT NULL''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Discord_ID', 'Username', 'power', 'Class']
    tank, healer, dps = filter_class(member)
    a, b, z = await id_to_user(message, bot, tank), await id_to_user(message, bot, healer), await id_to_user(message, bot, dps)

async def get_unknowns(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    c.execute('''SELECT username FROM Members WHERE Clan_Name = (%s) AND Discord_ID IS NULL''', (clan, ))
    member = pd.DataFrame(c.fetchall())
    member.columns = ['Username']
    await message.channel.send(send_data(member))

async def tag_character(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    username = await get_username(message, bot)
    c.execute('''SELECT Username FROM Members WHERE Username ~* (%s) AND Clan_Name = (%s)''', (username, clan))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        name = match[0][0]
    else:
        match_list, string_list = all_names(match)
        name = (await get_selection(message, bot, match_list, string_list))[0]
    await message.channel.send('What is their Discord Username and number in the format of username#1234 (eg. Fomalhaut#9333)')
    user = await bot.wait_for("message", check = check, timeout = 120)
    test = bot.get_all_members()
    try:
        user = user.content.split('#')
        user_id = discord.utils.get(bot.get_all_members(), name = user[0], discriminator = user[1]).id
    except:
        await message.channel.send('User not found')
        return  
    try:
        c.execute('''UPDATE Members SET Discord_ID=(%s) WHERE Username=(%s) AND Clan_Name = (%s)''', (user_id, name, clan)) 
        conn.commit()
        await message.channel.send("ID successfully set") 
    except:
        conn.rollback()
        await message.channel.send("ID could not be set")

async def id_me(message, bot):
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    username = await get_username(message, bot)
    c.execute('''SELECT Username FROM Members WHERE Username ~* (%s) AND Clan_Name = (%s)''', (username, clan))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        name = match[0][0]
    else:
        match_list, string_list = all_names(match)
        name = (await get_selection(message, bot, match_list, string_list))[0]
    try:
        c.execute('''UPDATE Members SET Discord_ID = (%s) WHERE Username = (%s) AND Clan_Name = (%s)''', (message.author.id, name, clan))
        conn.commit()
        await message.channel.send("ID sucessfully set")
    except:
        conn.rollback()
        await message.channel.send("ID could not be set")

async def find_character(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    username = await get_username(message, bot)
    c.execute('''SELECT Username, Discord_ID, Class, Level, power, Updated FROM Members WHERE Username ~* (%s) AND Clan_Name = (%s)''', (username, clan))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        name = list(match[0])
    else:
        match_list, string_list = all_names(match)
        name = list(await get_selection(message, bot, match_list, string_list))
    name[1] = bot.get_user(name[1])
    if name[1] == None:
        name[1] = 'Unknown user'
    await message.channel.send(format_find(name))

async def update_character(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    today = datetime.now().strftime('%m-%d-%Y')
    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    username = await get_username(message, bot)
    c.execute('''SELECT Username FROM Members WHERE Username ~* (%s) AND Clan_Name = (%s)''', (username, clan))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        name = match[0][0]
    else:
        match_list, string_list = all_names(match)
        name = (await get_selection(message, bot, match_list, string_list))[0]
    try:
        level, power = await get_level_power(message, bot)
    except:
        await message.send('An integer was not entered. Please try again')
        return                      
    await message.send("Is this correct (yes/no):\n```Username: %s\nLevel: %s\npower: %s```" %(name, level, power))
    confirm = await bot.wait_for("message", check = check)
    if confirm.content.lower().startswith('y'):
        c.execute('''UPDATE Members SET Level=(%s), power=(%s), Updated =(%s) WHERE Username=(%s) AND Clan_Name = (%s)''', (level, power, today, name, clan))
        conn.commit()
        await message.send("Character successfully updated")
    else:
        conn.rollback()
        await message.send("Please try again")

async def allow_commands(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.send("What is the name of your server?")
    server = await bot.wait_for("message", check = check, timeout = 120)
    c.execute('''SELECT server_name FROM servers WHERE server_name ~* (%s)''', (server.content, ))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        server = match[0][0]
    else:
        match_list, string_list = all_names(match)
        server = (await get_selection(message, bot, match_list, string_list))[0]
    await message.send("Is this the name of your server: %s?" %(server))
    confirm = await bot.wait_for("message", check = check)
    if confirm.content.lower().startswith('y'):
        try:
            c.execute('''UPDATE Servers SET Commands = (%s), Representative = (%s) WHERE Server_Name = (%s)''', ('yes', message.author.id, server))
            conn.commit()
            await message.send("Server succesfully registered")
        except:
            conn.rollback()
            await message.send("Server could not be registered")

async def change_username(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    try:
        clan = await search_clan(message, bot)
    except:
        await message.send('Clan was not found. Please try again')
        return
    await message.send("What is your new username? (Case sensitive)")
    new_name = await bot.wait_for("message", check = check, timeout = 120)
    await message.send("What was your previous username? (Case sensitive)")
    former_name = await bot.wait_for("message", check = check, timeout = 120)
    c.execute('''SELECT Username FROM Members WHERE Username ~* (%s) AND Clan_Name ~* (%s)''', (former_name.content, clan))
    match = c.fetchall()
    if match == []:
        await message.send('No match found')
        return
    elif len(match) == 1:
        former_name = match[0][0]
    else:
        match_list, string_list = all_names(match)
        former_name = (await get_selection(message, bot, match_list, string_list))[0]
    try:
        c.execute('''UPDATE Members SET Username =(%s) WHERE Username =(%s) AND Clan_Name = (%s)''',(new_name.content, former_name, clan))
        conn.commit()
        await message.send("Username successfully changed")
    except:
        conn.rollback()
        await message.send("The username could not be changed")
