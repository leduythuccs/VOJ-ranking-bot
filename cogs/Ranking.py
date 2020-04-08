from discord.ext import commands, tasks
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
from collections import namedtuple
from typing import List
from helper import codeforces_api
BASE_PROBLEM_URL = 'https://codeforces.com/group/FLVn1Sc504/contest/{0}/problem/{1}'
Rank = namedtuple('Rank', 'low high title title_abbr color_graph color_embed')
# % max_score 
RATED_RANKS = [
    Rank(-10 ** 9, 0.25, 'Newbie', 'N', '#CCCCCC', 0x808080),
    Rank(0.25, 0.5, 'Pupil', 'P', '#77FF77', 0x008000),
    Rank(0.5, 2, 'Specialist', 'S', '#77DDBB', 0x03a89e),
    Rank(2, 5, 'Expert', 'E', '#AAAAFF', 0x0000ff),
    Rank(5, 10, 'Candidate Master', 'CM', '#FF88FF', 0xaa00aa),
    Rank(10, 15, 'Master', 'M', '#FFCC88', 0xff8c00),
    Rank(15, 30, 'International Master', 'IM', '#FFBB55', 0xf57500),
    Rank(30, 45, 'Grandmaster', 'GM', '#FF7777', 0xff3030),
    Rank(45, 60, 'International Grandmaster', 'IGM', '#FF3333', 0xff0000),
    Rank(60, 90, 'Legendary Grandmaster', 'LGM', '#AA0000', 0xcc0000),
    Rank(90, 10 ** 9, 'Cá nóc', 'CNCC', '#854442', 0xcc0000)
]
UNRATED_RANK = Rank(None, None, 'Unrated', None, None, None)

SET_HANDLE_SUCCESS = 'Handle for <@{0}> currently set to <https://codeforces.com/profile/{1}>'

def point2rank(point, MAX_SCORE = 100):
    if point is None:
        return UNRATED_RANK
    for rank in RATED_RANKS:
        if rank.low * MAX_SCORE / 100 <= point < rank.high * MAX_SCORE / 100:
            return rank

def _plot_rating(resp, mark='o', labels: List[str] = None, MAX_SCORE = 100):
    labels = [''] * len(resp) if labels is None else labels

    for user, label in zip(resp, labels):
        ratings, dates = [], []
        for rating, date in user:
            ratings.append(rating)
            dates.append(datetime.strptime(date, "%Y/%m/%d"))
        plt.plot(dates,
                 ratings,
                 linestyle='-',
                 marker=mark,
                 markersize=3,
                 markerfacecolor='white',
                 markeredgewidth=0.5,
                 label=label)

    gc.plot_rating_bg(RATED_RANKS, MAX_SCORE)
    plt.gcf().autofmt_xdate()

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
        self.MAX_SCORE = 0
        self.looper.start()
        self.index = 0

    
    @tasks.loop(minutes=10.0)
    async def looper(self):
        self.index += 1
        print("looping " + str(self.index))
        try:
            await self.crawl(None, 1, 100)
            await self.calculate_rank(None)
        except Exception as e:
            print(e)
        
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     pass
    
    # @commands.command(brief="Set handle for a user")
    # @commands.check_any(commands.is_owner(), commands.has_role('Admin'))
    # async def set(self, ctx, member: discord.Member, handle: str):
    #     message = ""
    #     if self.rankingDb.set_handle(member.id, handle):
    #         await ctx.send("Error: The handle {} is already associated with another user.".format(handle))
    @commands.command(brief="Identify yourself.")
    async def identify(self, ctx, handle):
        discord_id = ctx.author.id 
        await ctx.send(f'`{str(ctx.author)}`, submit a compile error to <https://codeforces.com/problemset/problem/696/A> within 60 seconds')
        for i in range(6):
            await asyncio.sleep(10)
            subs = await codeforces_api.get_user_status(handle)

            if any(sub['problem_name'] == 'Lorenzo Von Matterhorn' and sub['verdict'] == 'COMPILATION_ERROR' for sub in subs):
                x = self.rankingDb.set_handle(discord_id, handle)
                if x != True:
                    await ctx.send('Error, handle {0} is currently set to user <@{1}>'.format(handle, x))
                else:
                    await ctx.send(SET_HANDLE_SUCCESS.format(discord_id, handle))
                    self.rankingDb.conn.commit()
                return
        await ctx.send(f'Sorry `{str(ctx.author)}`, can you try again?')
    @commands.command(brief="Get badge info.")
    async def badge(self, ctx):
        """
            Show required score to get badge.
        """
        style = table.Style('{:<}  {:<}  {:<}')
        t = table.Table(style)
        t += table.Header('Badge title', 'Lowerbound %', 'Upperbound %')
        t += table.Line()
        for rank in RATED_RANKS:
            title = rank.title
            low = max(0, rank.low)
            hi = min(100, rank.high)
            low = "{:.2f}%".format(low)
            hi = "{:.2f}%".format(hi)
            t += table.Data(title, low, hi)
        table_str = f'```\n{t}\n```'
        embed = discord_common.cf_color_embed(
            title="Required % score to get badge. "
            "Current MAX_SCORE={:.2f}".format(self.MAX_SCORE),
            description=table_str)
        await ctx.send(embed=embed)
    @commands.command(brief="Update badge info.")
    @commands.is_owner()
    async def update_badge(self, ctx, name, low, hi):
        try:
            for i in range(len(RATED_RANKS)):
                if RATED_RANKS[i].title == name:
                    rank = RATED_RANKS[i]
                    #Rank = namedtuple('Rank', 'low high title title_abbr color_graph color_embed')
                    RATED_RANKS[i] = Rank(float(low), float(hi), name, rank.title_abbr, rank.color_graph, rank.color_embed)
                    await ctx.send('Ok')
                    return
            else:
                await ctx.send('Badge {0} not found'.format(name))
        except Exception as e:
            print(e)
            await ctx.send(str(e))
    @commands.command(brief='Set Codeforces handle of a user')
    @commands.check_any(commands.is_owner(), commands.has_role('Admin'))
    async def set(self, ctx, member: discord.Member, handle):
        if self.rankingDb.set_handle(member.id, handle, force=True) == True:
            await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))
            self.rankingDb.conn.commit()
        else:
            await ctx.send("Failed ?? :D ??")
    @commands.command(brief='Get handle by Discord username')
    async def get(self, ctx, member: discord.Member):
        """Show Codeforces handle of a user."""
        handle = self.rankingDb.get_handle(member.id)
        if handle is None:
            if ctx is None:
                return None
            await ctx.send(f'Handle for {member.mention} not found in database')
            return
        if ctx is None:
            return handle
        await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))

    async def get_handle(self, ctx, handle):
        if handle is None:
            handle = await self.get(None, ctx.author)
            if handle is None:
                await ctx.send(f'Handle for {ctx.author.mention} not found in database')
                return None
            return handle
        else:
            handle = handle.replace('!', '')
            if handle[0] == '<' and handle[-1] == '>':
                if len(handle) <= 3 or not handle[2:-1].isdigit():
                    await ctx.send(f'Handle {handle} is invalid.')
                    return None
                discord_id = handle[2:-1]
                handle = self.rankingDb.get_handle(discord_id)
                if handle is None:
                    await ctx.send(f'Handle for <@{discord_id}> not found in database')
                    return None
        return handle
    
    @commands.command(brief="List recent AC problems",
        usage='[handle]')
    async def stalk(self, ctx, handle = None):
        handle = await self.get_handle(ctx, handle)
        if handle is None:
            return None
        problem_list = self.rankingDb.get_info_solved_problem(handle)
        problem_list = list(filter(lambda x: x[1] == 'AC', problem_list))
        problem_list = sorted(problem_list, key=lambda x: x[2], reverse=True)
        problem_list = problem_list[:10]
        problem_list = list(map(lambda x: (self.rankingDb.get_problem_info(x[0]), x[1], x[2]), problem_list))
        if len(problem_list) == 0:
            await ctx.send(f'User `{handle}`` is not rated. No accpected submission found.')
            return
        
        msg = ''
        for p in problem_list:
            msg += to_message(p) + '\n'
        title = "Recently solved problems by " + handle

        embed = discord.Embed(title=title, description=msg)
        await ctx.send(embed=embed)
    
    def get_rating_change(self, handle):
        #problem id, result, date
        raw_subs = self.rankingDb.get_info_solved_problem(handle)
        raw_subs = list(filter(lambda x: (x[1] == 'AC') or (float(x[1]) <= 0.1), raw_subs))
        raw_subs = sorted(raw_subs, key=lambda x: x[2])

        problem_info = self.rankingDb.get_data('problem_info', limit=None)
        problem_points = {}
        for id, problem_name, links, cnt_AC in problem_info:
            point = 80 / (40 + int(cnt_AC))
            problem_points[int(id)] = point
        rating_changes = [(-1, -1)]
        rating = 0
        for problem_id, result, date in raw_subs:
            if rating_changes[-1][1] != date:
                rating_changes.append((0, date))
            if result == 'AC':
                result = 100
            rating += problem_points[int(problem_id)] * float(result) / 100
            rating_changes[-1] = (rating, date) 
        return rating_changes[1:]
    
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
            await self.calculate_rank(ctx)
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
    async def hist(self, ctx, handle = None):
        """Shows the histogram of problems solved over time on Codeforces for the handles provided."""
        handle = await self.get_handle(ctx, handle)
        if handle is None:
            return 
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
        labels = ['Accepted', 'Incorrect', 'Partial Result']
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
    
    @commands.command(brief="Plot VOJ rating graph")
    async def exp(self, ctx, handle = None):
        """Plots VOJ experience graph for the handle provided."""
        handle = await self.get_handle(ctx, handle)
        if handle is None:
            return 
        if len(self.rank_cache) == 0:
            await self.calculate_rank(ctx)
        resp = self.get_rating_change(handle)
        if len(resp) == 0:
            await ctx.send(f'User `{handle}` is not rated. No accpected submission found.')
            return
        plt.clf()
        _plot_rating([resp], MAX_SCORE=self.MAX_SCORE)
        current_rating = resp[-1][0]
        rank_title = point2rank(current_rating, self.MAX_SCORE).title + " {:.3f}".format(current_rating)
        labels = [f'\N{ZERO WIDTH SPACE}{handle} ({rank_title})']
        plt.legend(labels, loc='upper left')
        min_rating = current_rating
        max_rating = current_rating
        for rating, date in resp:
            min_rating = min(min_rating, rating)
            max_rating = max(max_rating, rating)
        min_rating -= 5 * self.MAX_SCORE / 100
        max_rating += 5 * self.MAX_SCORE / 100
        if min_rating < 0: 
            min_rating = 0
        
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(title='Experience graph in VNOI group')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)
    
    @commands.command(brief="Calculate ranking and cache it.")
    @commands.is_owner()
    async def calculate_rank(self, ctx):
        start = time.perf_counter()
        message = ""
        if ctx != None:
            message = await ctx.send('<:pingreee:665243570655199246> Calculating ...')
        #calculating
        problem_info = self.rankingDb.get_data('problem_info', limit=None)
        problem_points = {}
        self.MAX_SCORE = 0
        for id, problem_name, links, cnt_AC in problem_info:
            point = 80 / (40 + int(cnt_AC))
            problem_points[int(id)] = point
            self.MAX_SCORE += point
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
        if ctx != None:
            await message.edit(content=f'Done. Calculation time: {int(duration)}ms.')
    
    @commands.command(brief="Test crawler")
    @commands.is_owner()
    async def crawl(self, ctx, l, r):
        if self.crawler.login() == False:
            if ctx is not None:
                await ctx.send('Failed when log in to codeforces, please try later.')
            else:
                print('Failed when log in to codeforces, please try later.')
            return
        l = int(l)
        r = int(r)
        problems = self.crawler.get_new_submissions(l, r)
        if ctx is not None:
            await ctx.send('Found {0} submissions.'.format(len(problems)))
        else:
            print('Found {0} submissions.'.format(len(problems)))
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
