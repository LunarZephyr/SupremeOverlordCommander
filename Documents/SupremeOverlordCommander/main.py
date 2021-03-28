import asyncio
import discord
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import pickle
import re
from defs import *
from async_defs import *
from psql_defs import *
from datetime import datetime
import sqlite3 as sql
import psycopg2 as psql
from discord.ext import tasks, commands

load_dotenv()
intents = discord.Intents.default()
intents.members = True
TOKEN = os.getenv('API_KEY')
bot = commands.Bot(command_prefix = '!', intents = intents)

#PSQL connector
conn = psql.connect("dbname = Ulala user = admin password = fomalumn")
c = conn.cursor()

testconn = sql.connect('SS_members.db')
tc = testconn.cursor()

role_list = ['Glad', 'War', 'Sin', 'Hunter', 'Lock', 'Mage', 'Druid', 'Shaman']

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(status = discord.Status.online, activity = discord.Game("Not Fit To Rule"), afk = False)

@bot.event
async def on_guild_join(guild):
    db_add_server(bot, guild)

@bot.command()
@commands.has_role('Bot User')
async def register(message):
    if message.guild.id == 824764313319374929:
        await allow_commands(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def add_clan(message):
    if registration_check(message, bot):
        await db_add_clan(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def add_member(message):
    #adds only one user at a time
    if registration_check(message, bot):
        await db_add_member(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def delete(message):
    #deletes multiple characters at once
    if registration_check(message, bot):
        await db_delete_members(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def build(message):
    if registration_check(message, bot):
       await build_teams(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def tbuild(message):
    if registration_check(message, bot):
        await build_teams_toss_elite(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def average(message):
    if registration_check(message, bot):
        await get_averages(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def members(message):
    if registration_check(message, bot):
        await list_members(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def status(message):
    if registration_check(message, bot):
        await show_status(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def tag(message):
    if registration_check(message, bot):
        await tag_character(message, bot)

#have not tested map function
@bot.command()
@commands.has_permissions(administrator = True)
async def map(message):
    if registration_check(message, bot):
        await map_discord_to_ingame(message, bot)

@bot.command()
@commands.has_permissions(administrator = True)
async def unknown(message):
    if registration_check(message, bot):
        await get_unknowns(message, bot)

@bot.command()
async def id(message):
    if registration_check(message, bot):
        await id_me(message, bot)

@bot.command()
async def find(message):
    if registration_check(message, bot):
        await find_character(message, bot)

@bot.command()
async def update(message):
    if registration_check(message, bot):
        await update_character(message, bot)

@bot.command()
async def change(message):
    if registration_check(message, bot):
        await change_username(message, bot)

#@bot.command()
#async def shutdown(message):
#    await message.bot.logout()

bot.run(TOKEN)
