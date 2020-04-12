from discord.ext import commands, tasks
import discord
import asyncio
import os
from service import SubmissionCrawler
from helper import RankingDb
import json
import time
from helper import table
from helper import paginator
from helper import discord_common
from helper import common
from typing import List
from helper import badge
badge.MAX_SCORE
class RankingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        username = os.getenv('CODEFORCES_USERNAME')
        password = os.getenv('CODEFORCES_PASSWORD')
        group_id = os.getenv('CODEFORCES_GROUP_ID')
        self.crawler = SubmissionCrawler.Crawler(username, password, group_id)
        self.rank_cache = []
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

    @commands.command(brief="Lấy thông tin các huy hiệu")
    async def badge(self, ctx):
        """
            Hiện phần trăm điểm yêu cầu để đạt được huy hiệu tương ứng.
        """
        style = table.Style('{:<}  {:<}  {:<}')
        t = table.Table(style)
        t += table.Header('Tên huy hiệu', '% yêu cầu', '% giới hạn')
        t += table.Line()
        for rank in badge.RATED_RANKS:
            title = rank.title
            low = max(0, rank.low)
            hi = min(100, rank.high)
            low = "{:.2f}%".format(low)
            hi = "{:.2f}%".format(hi)
            t += table.Data(title, low, hi)
        table_str = f'```\n{t}\n```'
        embed = discord_common.cf_color_embed(
            title="% điểm yêu cầu."
            "Tổng điểm hiện tại SUM_SCORE={:.2f}".format(badge.MAX_SCORE),
            description=table_str)
        await ctx.send(embed=embed)

    @commands.command(brief="Update badge info.")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def update_badge(self, ctx, name, low, hi):
        try:
            for i in range(len(badge.RATED_RANKS)):
                if badge.RATED_RANKS[i].title == name:
                    rank = badge.RATED_RANKS[i]
                    #Rank = namedtuple('Rank', 'low high title title_abbr color_graph color_embed')
                    badge.RATED_RANKS[i] = badge.Rank(float(low), float(hi), name, rank.title_abbr, rank.color_graph, rank.color_embed)
                    await ctx.send('Ok')
                    return
            else:
                await ctx.send('Badge {0} not found'.format(name))
        except Exception as e:
            print(e)
            await ctx.send(str(e))

    # from TLE bot: https://github.com/cheran-senthil/TLE/blob/97c9bff9800b3bbaefb72ec00faa57a4911d3a4b/tle/cogs/duel.py#L410

    @commands.command(brief="Hiện bảng xếp hạng")
    async def ranklist(self, ctx):
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
            return 'Bảng xếp hạng VOJ', embed

        pages = [make_page(chunk, k) for k, chunk in enumerate(
            paginator.chunkify(self.rank_cache, _PER_PAGE))]
        paginator.paginate(self.bot, ctx.channel, pages)

    @commands.command(brief="Calculate ranking and cache it.")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def calculate_rank(self, ctx):
        start = time.perf_counter()
        message = ""
        if ctx != None:
            message = await ctx.send('<:pingreee:665243570655199246> Calculating ...')
        # calculating
        problem_points = common.get_problem_points(force=True)
        badge.MAX_SCORE = 0
        for p, point in problem_points.items():
            #remove scale
            # badge.MAX_SCORE += point
            badge.MAX_SCORE += 2
        user_data = RankingDb.RankingDb.get_data('user_data', limit=None)
        user_handles = {}
        for cf_id, handle, discord_id in user_data:
            if cf_id is None:
                continue
            user_handles[int(cf_id)] = handle

        user_points = {}
        solved_info = RankingDb.RankingDb.get_data('solved_info', limit=None)
        for user_id, problem_id, result, date in solved_info:
            handle = user_handles[int(user_id)]
            if handle not in user_points:
                user_points[handle] = 0
            if result == 'AC':
                result = 100
            result = float(result)
            #remove scale
            # user_points[handle] += result * problem_points[int(problem_id)] / 100
            user_points[handle] += result * 2 / 100
        self.rank_cache = []
        for handle, point in user_points.items():
            self.rank_cache.append((point, handle))
        self.rank_cache.sort(reverse=True)
        end = time.perf_counter()
        duration = (end - start) * 1000
        if ctx != None:
            await message.edit(content=f'Done. Calculation time: {int(duration)}ms.')

    @commands.command(brief="Test crawler")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def exclude(self, ctx, contest_id):
        open('database/contest_id_whitelist.txt', 'a').write(str(contest_id) + '\n')
        await ctx.send('ok')
    @commands.command(brief="Test crawler")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
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
            RankingDb.RankingDb.handle_new_submission(
                problem_name, short_link, verdict, user_id, handle, date)
        RankingDb.RankingDb.conn.commit()


def setup(bot):
    bot.add_cog(RankingCommand(bot))
