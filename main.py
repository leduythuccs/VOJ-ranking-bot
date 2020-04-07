import os
from dotenv import load_dotenv
from discord.ext import commands
import seaborn as sns
from matplotlib import pyplot as plt
def setup():
    # Make required directories.
    os.makedirs('temp_dir', exist_ok=True)

    # matplotlib and seaborn
    plt.rcParams['figure.figsize'] = 7.0, 3.5
    sns.set()
    options = {
        'axes.edgecolor': '#A0A0C5',
        'axes.spines.top': False,
        'axes.spines.right': False,
    }
    sns.set_style('darkgrid', options)

current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)
load_dotenv()

setup()

token = os.getenv('DISCORD_TOKEN')
# bot
bot = commands.Bot(command_prefix=';voj ')
print(bot.command_prefix)
bot.load_extension("cogs.Ranking")
bot.load_extension("cogs.BotControl")
bot.load_extension("cogs.GetCodeforcesLink")
bot.load_extension("cogs.CoronaCommand")
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_command_error(ctx, error):
    print(error)
    await ctx.send('Error: ' + str(error))

bot.run(token)
