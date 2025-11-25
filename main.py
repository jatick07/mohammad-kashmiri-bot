from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
import logging
import os
import sqlite3
import lang
import re
import datetime
from cogs import *

load_dotenv(".env")
token = os.getenv("TOKEN")

db = sqlite3.connect('database.db')
cursor = db.cursor()

handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(intents=intents, command_prefix='$')

class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client
        print("Loaded Admin commands")

    @commands.command(name='sethr')
    @commands.has_permissions(administrator=True)
    async def sethr(self, ctx, role: discord.Role):
        "- sets the HR role that can adjust the schedule"

        if not role:
            await ctx.reply("nigga u didnt specify a role")
            return

        cursor.execute(f"UPDATE role SET role_name = '{role.name}', role_id = '{role.id}'")
        db.commit()
        await ctx.reply(f"set <@&{role.id}> as the HR role")


class HR(commands.Cog):
    def __init__(self, client):
        self.client = client
        print("Loaded HR commands")

    @commands.command(name='addtime')
    async def addtime(self, ctx, date, time, ampm, user: discord.Member):
        "- add time to schedule, for example: $addtime 28/12/2007 3:00 PM @nigga"

        cursor.execute(f"SELECT * FROM role LIMIT 1;")
        role_id = cursor.fetchone()[1]
        if role_id == 'default':
            return await ctx.reply("no role is set to run this command, run $sethr first")
        elif int(role_id) not in [r.id for r in ctx.author.roles]:
            return await ctx.reply("nigga u aint allowed to do this shit")

        time += f" {ampm}"
        date_format = re.match(r"^\d{2}/\d{2}/\d{4}$", date, re.IGNORECASE)
        time_format = re.match(r"^(1[0-2]|[1-9]):[0-5]\d\s(?:AM|PM)$", time, re.IGNORECASE)
        
        if not date_format or not time_format:
            return await ctx.reply(lang.smth_wrong)
            
        cursor.execute(f"INSERT INTO schedule VALUES ('{date}', '{time}', {user.id})")
        db.commit()

        return await ctx.send(f"added interview time for <@{user.id}> `{date} {time}`")

def initialize_database(db, cursor):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{"role"}';")
    role_table = cursor.fetchone()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{"schedule"}';")
    sched_table = cursor.fetchone()

    if not role_table or not sched_table:
        cursor.execute('CREATE TABLE role (role_name TEXT, role_id TEXT)')
        cursor.execute("INSERT INTO role (role_name, role_id) VALUES ('default', 'default')")
        cursor.execute('CREATE TABLE schedule (date TEXT, time TEXT, user INTEGER)')
        db.commit()


@client.event
async def on_ready():
    await client.add_cog(Peasant(client, cursor, db))
    await client.add_cog(Admin(client))
    await client.add_cog(HR(client))
    initialize_database(db, cursor)

    print(f"{client.user} bot is online")
    await client.wait_until_ready()
    check_schedule.start(client)

@client.event
async def on_member_join(member):
    channel = client.get_channel(1442480252780806234) 
    if channel:
        await channel.send(f"welcome ras el 3abed {member.mention}")

@tasks.loop(seconds=60)
async def check_schedule(client):
    now = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")

    cursor.execute("SELECT date, time, user FROM schedule")
    rows = cursor.fetchall()

    for date, time, user_id in rows:
        scheduled_str = f"{date} {'0' if time[1] == ':' else ''}{time}"
        print(scheduled_str + ", now: " + now)
        if scheduled_str == now:
            # RUN YOUR ACTION HERE
            channel = client.get_channel(1442479992318722089)
            await channel.send(f"nigga its `{scheduled_str}` its time for fukin interview <@{user_id}> get ur ass here ")
            cursor.execute(
                "DELETE FROM schedule WHERE date = ? AND time = ?",
                (date, time)
            )
            db.commit()

client.run(token=token)