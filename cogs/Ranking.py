from discord.ext import commands
import discord
import asyncio
import os
from service import SubmissionCrawler
import json
from datetime import datetime
import requests
import time


class RankingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        username = os.getenv('CODEFORCES_USERNAME')
        password = os.getenv('CODEFORCES_PASSWORD')
        group_id = os.getenv('CODEFORCES_GROUP_ID')

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     pass

    @commands.command(brief="Change log channel.")
    @commands.is_owner()
    async def change_log(self, ctx):
        """Change bot's log channel to this channel"""
        self.log_channel = ctx.channel
        await ctx.send("Successfully set log channel to " + ctx.channel.name)

def setup(bot):
    bot.add_cog(RankingCommand(bot))
