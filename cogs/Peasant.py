# from discord.ext import commands
# from cogs import CommandBaseline

# class Peasant(commands.Cog, CommandBaseline):
#     @commands.command(name='schedule')
#     async def schedule(self, ctx, client, cursor, db):
#         "- show schedule and availability of interview spots"
#         CommandBaseline.__init__(client, cursor, db)
#         self.cursor.execute(f"SELECT * FROM schedule;")
#         schedule = self.cursor.fetchall()

#         if not schedule:
#             await ctx.reply(f"No timnes available in the schedule, contact HR")
#         out = ""
#         for row in schedule:
#             out += f"- {row[0]} {row[1]} - <@{row[2]}>\n"
        
#         await ctx.reply(out)