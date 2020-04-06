from discord.ext import commands
import discord
import asyncio
import os
from service import SubmissionCrawler
from helper import RankingDb
import json
from datetime import datetime
import requests
import time
BASE_PROBLEM_URL = 'https://codeforces.com/group/FLVn1Sc504/contest/{0}/problem/{1}'
def days_between(d1, d2 = None):
    if d2 is None:
        d2 = datetime.today()
    d1 = datetime.strptime(d1, "%Y/%m/%d")
    return (d2 - d1).days
def to_message(p):
    #p[0][0] -> name
    #p[0][1] -> links
    #p[0][2] -> cnt_AC
    #p[1] -> result
    #p[2] -> DATE
    links = p[0][1].strip(',').split(',')
    links = list(map(lambda x: BASE_PROBLEM_URL.format(x.split('/')[0], x.split('/')[1]), links))
    msg = ""
    if len(links) == 1:
        msg = "[{0}]({1}) ".format(p[0][0], links[0])
    else:
        msg = p[0][0] + " "
        for i, link in enumerate(links):
            msg += "[link{0}]({1}) ".format(i + 1, link)
    diff = days_between(p[2])
    if diff == 1:
        msg += "(1 day ago)"
    elif diff > 1:
        msg += "({0} days ago)".format(diff)
    return msg

class RankingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        username = os.getenv('CODEFORCES_USERNAME')
        password = os.getenv('CODEFORCES_PASSWORD')
        group_id = os.getenv('CODEFORCES_GROUP_ID')
        self.rankingDb = RankingDb.RankingDbConn('database/ranking.db')
        self.crawler = SubmissionCrawler.Crawler(username, password, group_id)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     pass
    
    # @commands.command(brief="Set handle for a user")
    # @commands.check_any(commands.is_owner(), commands.has_role('Admin'))
    # async def set(self, ctx, member: discord.Member, handle: str):
    #     message = ""
    #     if self.rankingDb.set_handle(member.id, handle):
    #         await ctx.send("Error: The handle {} is already associated with another user.".format(handle))
    @commands.command(brief="List recent AC problems",
        usage='[handle]')
    async def stalk(self, ctx, handle):
        problem_list = self.rankingDb.get_info_solved_problem(handle)
        problem_list = list(filter(lambda x: x[1] == 'AC', problem_list))
        problem_list = sorted(problem_list, key=lambda x: x[2], reverse=True)
        problem_list = problem_list[:10]
        problem_list = list(map(lambda x: (self.rankingDb.get_problem_info(x[0]), x[1], x[2]), problem_list))
        msg = ''
        for p in problem_list:
            msg += to_message(p) + '\n'
        title = "Recently solved problems by " + handle
        embed = discord.Embed(title=title, description=msg)
        await ctx.send(embed=embed)

    # @commands.command(brief="Change log channel.")
    # @commands.is_owner()
    # async def change_log(self, ctx):
    #     """Change bot's log channel to this channel"""
    #     self.log_channel = ctx.channel
    #     await ctx.send("Successfully set log channel to " + ctx.channel.name)
    @commands.command(brief="Test crawler")
    @commands.is_owner()
    async def crawl(self, ctx):
        problems = self.crawler.get_new_submissions()
        await ctx.send('Found {0} submissions.'.format(len(problems)))
        for p_info in problems:
            id, problem_name, short_link, handle, user_id, verdict, date = p_info
            self.rankingDb.handle_new_submission(problem_name, short_link, verdict, user_id, handle, date)

def setup(bot):
    bot.add_cog(RankingCommand(bot))
