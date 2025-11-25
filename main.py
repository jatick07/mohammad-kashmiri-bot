from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(intents=intents, command_prefix='$')


class Peasant(commands.Cog):
    def __init__(self, client):
        self.client = client
        print("Loaded Peasant commands")

    @commands.command(name='schedule')
    async def schedule(self, ctx):
        "- show schedule and availability of interview spots"
        
        cursor.execute(f"SELECT * FROM schedule WHERE guild_id = {ctx.guild.id}")
        schedule = cursor.fetchall()

        if not schedule:
            await ctx.reply(f"No times available in the schedule, contact HR")
        
        out = ""
        for row in schedule:
            user = await client.fetch_user(row[3])
            print(row[3])
            out += f"- {row[1]} {row[2]} - *{user.name}*\n"
        
        await ctx.reply(out)


class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client
        print("Loaded Admin commands")

    @commands.command(name='sethr')
    @commands.has_permissions(administrator=True)
    async def sethr(self, ctx, role: discord.Role, channel: discord.TextChannel):
        "- sets the HR role that can adjust the schedule"
        if not role or not channel:
            await ctx.reply(lang.smth_wrong)
            return
        
        
        cursor.execute("INSERT INTO role (guild_id, role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET role_id = excluded.role_id", (ctx.guild.id, role.id))
        cursor.execute("INSERT INTO channel (guild_id, hr) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET hr = excluded.hr", (ctx.guild.id, channel.id))
        db.commit()
        
        await ctx.reply(f"set <@&{role.id}> as the HR role, and <#{channel.id}> as the HR channel")

    @commands.command(name='setwelcome')
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        "- sets the welcome channel"
        if not channel:
            await ctx.reply("nigga u didnt specify a channel")
            return
        
        cursor.execute("INSERT INTO channel (guild_id, welcome) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET welcome = excluded.welcome", (ctx.guild.id, channel.id))
        db.commit()
        
        await ctx.reply(f"set <#{channel.id}> as the welcome channel")


class HR(commands.Cog):
    def __init__(self, client):
        self.client = client
        print("Loaded HR commands")

    @commands.command(name='addtime')
    async def addtime(self, ctx, date, time, ampm, user: discord.Member):
        "- add time to schedule, for example: $addtime 28/12/2007 3:00 PM @nigga"

        cursor.execute(f"SELECT * FROM role WHERE guild_id = {ctx.guild.id};")
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
            
        cursor.execute(f"INSERT INTO schedule VALUES ({ctx.guild.id}, '{date}', '{time}', {user.id})")
        db.commit()

        return await ctx.send(f"added interview time for <@{user.id}> on `{date}` at `{time}`")

def initialize_database(db, cursor):
    cursor.execute('CREATE TABLE IF NOT EXISTS role (guild_id INTEGER PRIMARY KEY, role_id INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS schedule (guild_id INTEGER, date TEXT, time TEXT, user INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS channel (guild_id INTEGER PRIMARY KEY, welcome INTEGER, hr INTEGER)')
    db.commit()


@client.event
async def on_ready():
    await client.add_cog(Peasant(client))
    await client.add_cog(Admin(client))
    await client.add_cog(HR(client))
    initialize_database(db, cursor)

    print(f"{client.user} bot is online")
    await client.wait_until_ready()
    check_schedule.start(client)

@client.event
async def on_member_join(member):
    cursor.execute(f"SELECT * FROM channel WHERE guild_id = {member.guild.id}")
    channel = client.get_channel(cursor.fetchone()[1])

    if channel:
        await channel.send(f"welcome ras el 3abed {member.mention}")

@tasks.loop(seconds=60)
async def check_schedule(client):
    now = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")

    cursor.execute("SELECT * FROM schedule")
    rows = cursor.fetchall()

    for guild_id, date, time, user_id in rows:
        scheduled_str = f"{date} {'0' if time[1] == ':' else ''}{time}"
        print(scheduled_str + ", now: " + now)
        if scheduled_str == now:
            cursor.execute(f"SELECT * FROM channel WHERE guild_id = {guild_id}")
            channel = client.get_channel(cursor.fetchone()[2])

            await channel.send(f"nigga its `{scheduled_str}` its time for fukin interview <@{user_id}> get ur ass here ")
            cursor.execute(
                "DELETE FROM schedule WHERE date = ? AND time = ? AND user = ?",
                (date, time, user_id)
            )
            db.commit()

client.run(token=token)