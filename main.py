import os
from dotenv import load_dotenv
from discord.ext import commands
current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)
load_dotenv()

token = os.getenv('DISCORD_TOKEN')

# bot
bot = commands.Bot(command_prefix=';voj ')
print(bot.command_prefix)
bot.load_extension("cogs.Ranking")
bot.load_extension("cogs.BotControl")
bot.load_extension("cogs.GetCodeforcesLink")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_command_error(ctx, error):
    print(error)
    await ctx.send('Error: ' + str(error))

bot.run(token)
