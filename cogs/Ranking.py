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
from helper import table
from helper import paginator
from helper import discord_common
from helper import graph_common as gc
from matplotlib import pyplot as plt
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
        self.rank_cache = []

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
    #from TLE bot: https://github.com/cheran-senthil/TLE/blob/97c9bff9800b3bbaefb72ec00faa57a4911d3a4b/tle/cogs/duel.py#L410

    @commands.command(brief="Show ranking")
    async def ranklist(self, ctx):
        """Show VOJ ranking"""
        if len(self.rank_cache) == 0:
            self.calculate_rank(ctx)
        _PER_PAGE = 10
        def make_page(chunk, page_num):
            style = table.Style('{:>}  {:<}  {:<}')
            t = table.Table(style)
            t += table.Header('#', 'Handle', 'Point')
            t += table.Line()
            for index, (point, handle) in enumerate(chunk):
                point_str = '{:.3f}'.format(point)
                t += table.Data(_PER_PAGE * page_num + index, handle, point_str)

            table_str = f'```\n{t}\n```'
            embed = discord.Embed(description=table_str)
            return 'VOJ ranking', embed

        pages = [make_page(chunk, k) for k, chunk in enumerate(paginator.chunkify(self.rank_cache, _PER_PAGE))]
        paginator.paginate(self.bot, ctx.channel, pages)

    @commands.command(brief="Show histogram of solved problems on CF.")
    async def hist(self, ctx, handle):
        """Shows the histogram of problems solved over time on Codeforces for the handles provided."""
        raw_subs = self.rankingDb.get_info_solved_problem(handle)
        if len(raw_subs) == 0:
            await ctx.send('There are no problems within the specified parameters.')
            return
        subs = []
        types = ['AC', 'IC', 'PC']
        solved_by_type = {'AC' : [], 'IC' : [], 'PC' : []}
        cnt = 0
        plt.clf()
        plt.xlabel('Time')
        plt.ylabel('Number solved')
        for problem_id, result, date in raw_subs:
            t = result
            if t != 'AC' and float(t) <= 0 + 0.01:
                t = 'IC'
            elif t != 'AC':
                t = 'PC'
            solved_by_type[t].append(date)
        
        all_times = [[datetime.strptime(date, '%Y/%m/%d') for date in solved_by_type[t]] for t in types]
        labels = ['Accepted', 'Incorrect', 'Pactial Result']
        colors = ['g','r','y']
        plt.hist(all_times, stacked=True, label=labels, bins=34, color=colors)
        total = sum(map(len, all_times))
        plt.legend(title=f'{handle}: {total}', title_fontsize=plt.rcParams['legend.fontsize'])

        plt.gcf().autofmt_xdate()
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(title='Histogram of number of solved problems over time')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)
    
    @commands.command(brief="Calculate ranking and cache it.")
    @commands.is_owner()
    async def calculate_rank(self, ctx):
        start = time.perf_counter()
        message = await ctx.send('<:pingreee:665243570655199246> Calculating ...')
        #calculating
        problem_info = self.rankingDb.get_data('problem_info', limit=None)
        problem_points = {}
        for id, problem_name, links, cnt_AC in problem_info:
            point = 80 / (40 + int(cnt_AC))
            problem_points[int(id)] = point
        user_data = self.rankingDb.get_data('user_data', limit=None)
        user_handles = {}
        for cf_id, handle, discord_id in user_data:
            user_handles[int(cf_id)] = handle

        user_points = {}
        solved_info = self.rankingDb.get_data('solved_info', limit=None)
        for user_id, problem_id, result, date in solved_info:
            handle = user_handles[int(user_id)]
            if handle not in user_points:
                user_points[handle] = 0
            if result == 'AC':
                result = 100
            result = float(result)
            user_points[handle] += result * problem_points[int(problem_id)] / 100
        self.rank_cache = []
        for handle, point in user_points.items():
            self.rank_cache.append((point, handle))
        self.rank_cache.sort(reverse=True)
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(content=f'Done. Calculation time: {int(duration)}ms.')
    @commands.command(brief="Test crawler")
    @commands.is_owner()
    async def crawl(self, ctx, l, r):
        l = int(l)
        r = int(r)
        problems = self.crawler.get_new_submissions(l, r)
        await ctx.send('Found {0} submissions.'.format(len(problems)))
        cnt = 0
        for p_info in problems:
            cnt += 1
            if cnt % 10 == 0:
                print(cnt)
            id, problem_name, short_link, handle, user_id, verdict, date = p_info
            self.rankingDb.handle_new_submission(problem_name, short_link, verdict, user_id, handle, date)
        self.rankingDb.conn.commit()

def setup(bot):
    bot.add_cog(RankingCommand(bot))
