import asyncio
import discord
import pandas as pd
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pickle

#load_dotenv()
#TOKEN = os.getenv('API_KEY')
#TOKEN = os.getenv('NzQ2ODMxMTk2MjM0OTczMjg2.X0GCwA.c9wkTKrVh9ghMlV1kxXQznbZVYI')

#client = discord.Client()

#@client.event
#async def on_ready():
#    print(f'{client.user} has connected to Discord!')

#connect to google spreadsheets
scope  = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('ulala.json', scope)
gss_client = gspread.authorize(creds)

registry = gss_client.open('Discord Registry').sheet1
remove = [e[0:5] for e in registry.get_all_values()]
registry = pd.DataFrame(remove[3:], columns = remove[2])

c = 0

while c < 100:
    find = input("Enter account name: ")
    for i in range(len(registry.columns)):
        col_name = 'Account ' + str(i + 1)
        print(col_name)
        search = registry[registry[col_name] == find]
        if not search.empty:
            break
    print(search['Discord Name'].values[0])

print(search['Discord Name'].values[0])

#client.run(TOKEN)
