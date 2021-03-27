import asyncio
from defs import *
import discord

role_list = ['Glad', 'War', 'Sin', 'Hunter', 'Lock', 'Mage', 'Druid', 'Shaman']

async def get_clan_abrv(message, bot):   
    def check(m):
        return m.author == message.author and m.channel == message.channel
         
    await message.send("Which Clan? Give Abbreviation (eg. PP)")
    clan = await bot.wait_for("message", check = check, timeout = 120)
    return clan.content

async def get_username(message, bot):   
    def check(m):
        return m.author == message.author and m.channel == message.channel
        
    await message.send("What is the username?")
    name = await bot.wait_for("message", check = check, timeout = 120)
    return name.content

async def get_class(message, bot):   
    def check(m):
        return m.author == message.author and m.channel == message.channel

    count = 0
    number = np.arange(1, len(role_list) + 1)
    for role in role_list:
        try:
            string = '%s\n%d: %s' %(string, number[count], role)
        except:
            string = '%d: %s' %(number[count], role)
        count += 1
    await message.send("Pick class using the number assigned: ```%s```" %(string))
    value = await bot.wait_for("message", check = check, timeout = 120)
    return role_list[int(value.content) - 1]

async def get_level_power(message, bot):   
    def check(m):
        return m.author == message.author and m.channel == message.channel
         
    await message.send("What's your level?")
    level = await bot.wait_for('message', check = check, timeout = 120)
    level = int(level.content)

    await message.send("What's your power?")
    power = await bot.wait_for("message", check = check, timeout = 120)
    power = int(power.content)
    return level, power

async def get_selection(message, bot, match_list, string_list):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.send("Which character is yours?\n```%s```" %(string_list))
    value = await bot.wait_for("message", check = check)
    return match_list[int(value.content) - 1]

async def get_confirm_member(message, bot, name, role, level, power):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.send("Is this correct (yes/no):\n```Username: %s\nClass: %s\nLevel: %s\npower: %s```" %(name, role, level, power))
    confirm = await bot.wait_for("message", check = check, timeout = 120)
    if confirm.content.lower().startswith('y'):
        return
    else:
        raise Exception

async def get_confirm_clan(message, bot, clan, abv):
    def check(m):
        return m.author == message.author and m.channel == message.channel

    await message.send("Is this correct (yes/no):```Clan: \t\t\t%s\nAbbreviation: \t%s```" %(clan, abv))
    confirm = await bot.wait_for("message", check = check, timeout = 120)
    if confirm.content.lower().startswith('y'):
        return
    else:
        raise Exception

async def id_to_user(message, bot, dataframe):
    dataframe.reset_index(inplace = True, drop = True)
    new_col = []
    dataframe = dataframe.drop(['Class', 'power'], axis = 1)
    for i in dataframe['Discord_ID']:
        await bot.wait_until_ready()
        new_col.append(bot.get_user(i))
    temp_df = pd.DataFrame(new_col, columns = ['Discord_ID'])
    dataframe['Discord_ID'] = temp_df['Discord_ID']
    await message.send(send_data(dataframe))
    return 'done'

async def get_clan_name(message, bot):
    def check(m):
        return m.author == message.author and m.channel == message.channel
    
    await message.send("What is the name of your clan?")
    clan = await bot.wait_for("message", check = check, timeout = 120)
    await message.send("What abbreviation would you like to use for your clan? Please use an abbreviation less than 5 characters long")
    abv = await bot.wait_for("message", check = check, timeout = 120)
    return clan.content, abv.content