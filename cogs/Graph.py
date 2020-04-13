from discord.ext import commands, tasks
import discord
import asyncio
import os
from helper import RankingDb
import json
from datetime import datetime
import time
from helper import discord_common
from helper import graph_common as gc
from helper.common import DayFilter
from helper import common
from matplotlib import pyplot as plt
from typing import List
from helper import badge


BASE_PROBLEM_URL = 'https://codeforces.com/group/FLVn1Sc504/contest/{0}/problem/{1}'

WHILELIST_USER_IDs = ['328391']
TAGS = ['Dynamic programming', 'Data structure', 'Geometry', 'Graph', 'Math', 'String', 'Ad-hoc', 'Other']


def _plot_rating(resp, mark='o', labels: List[str] = None, MAX_SCORE=100):
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

    gc.plot_rating_bg(badge.RATED_RANKS, MAX_SCORE)
    plt.gcf().autofmt_xdate()


def days_between(d1, d2=None):
    if d2 is None:
        d2 = datetime.today()
    d1 = datetime.strptime(d1, "%Y/%m/%d")
    return (d2 - d1).days

def to_message(p):
    # p[0][0] -> name
    # p[0][1] -> links
    # p[0][2] -> cnt_AC
    # p[1] -> result
    # p[2] -> DATE
    links = p[0][1].strip(',').split(',')
    links = list(map(lambda x: BASE_PROBLEM_URL.format(x.split('/')[0], x.split('/')[1]), links))
    msg = ""
    if len(links) == 1:
        msg = "[{0}]({1}) ".format(p[0][0], links[0])
    else:
        msg = "[{0}]({1}) ".format(p[0][0], links[0])
        for i, link in enumerate(links[1:]):
            msg += "[link{0}]({1}) ".format(i + 2, link)
    diff = days_between(p[2])
    if diff == 1:
        msg += "(1 day ago)"
    elif diff > 1:
        msg += "({0} days ago)".format(diff)
    return msg


class Graph(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tag = {}
        data = json.load(open('database/problem_tag.json'))
        for x in data:
            self.tag[x] = data[x]

    @commands.command(brief="Biểu đồ các bài đã giải theo tag.",
                      usage='[handle] [d>=[[dd]mm]yyyy] [d<[[dd]mm]yyyy]')
    async def tagbar(self, ctx, *args):
        """
        Hiện biểu đồ các bài đã giải theo tag của nick codeforces tương ứng.
        Ví dụ ;voj tagbar CKQ
        """
        filt = DayFilter()
        handle = filt.parse(args)
        handle = await common.get_handle(ctx, handle)
        if handle is None:
            return
        #id result date
        problem_list = RankingDb.RankingDb.get_info_solved_problem(handle)
        problem_list = list(filter(lambda x: x[1] == 'AC' or (float(x[1]) >= 100 - 0.1), problem_list))
        problem_list = list(filter(lambda x: filt.filter(datetime.strptime(x[2], '%Y/%m/%d')), problem_list))
        if len(problem_list) == 0:
            await ctx.send('Không tìm thấy submission của `{0}` với các tham số hiện tại.'.format(handle))
            return
        problem_info = RankingDb.RankingDb.get_data('problem_info', limit=None)
        id_to_name = {}
        #id, name, link, cntAC
        for id, name, link, cnt_AC in problem_info:
            name = name[:name.find('-')].strip()
            id_to_name[int(id)] = name
        cnt = {'No tag' : 0}
        for tag in TAGS:
            cnt[tag] = 0
        for id, *junks in problem_list:
            id = int(id)
            tags = []
            if id not in id_to_name:
                tags = ['No tag']
            else:
                name = id_to_name[id]
                if name not in self.tag:
                    tags = ['No tag']
                else:
                    tags = self.tag[name]
            for tag in tags:
                if tag not in cnt:
                    cnt[tag] = 0
                cnt[tag] += 1
        #///
        plt.clf()
        plt.xlabel('Tag')
        plt.ylabel('Number solved')
        x_pos = list(range(len(TAGS)))
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:pink', 'tab:olive', 'tab:cyan']
        plt.bar(x_pos, [cnt[x] for x in TAGS], color=colors)
        plt.xticks(x_pos, TAGS)
        for index, value in enumerate(TAGS):
            if cnt[value] < 10:
                plt.text(index - 0.1, cnt[value], str(cnt[value]))
            elif cnt[value] < 100:
                plt.text(index - 0.15, cnt[value], str(cnt[value]))
            else:
                plt.text(index - 0.25, cnt[value], str(cnt[value]))
        
        total = len(problem_list)
        plt.legend(title=f"{handle}: {total} ({cnt['No tag']} no tag)",
                   title_fontsize=plt.rcParams['legend.fontsize'])
        plt.gcf().autofmt_xdate()
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(
            title='Số lượng bài giải được trong từng category')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)
    @commands.command(brief="Lấy danh sách các bài vừa làm",
                      usage='[handle] [d>=[[dd]mm]yyyy] [d<[[dd]mm]yyyy]')
    async def stalk(self, ctx, *args):
        """
        Top 10 bài vừa làm gần nhất.
        Ví dụ ;voj stalk CKQ
        """
        filt = DayFilter()
        handle = filt.parse(args)
        handle = await common.get_handle(ctx, handle)
        if handle is None:
            return
        problem_list = RankingDb.RankingDb.get_info_solved_problem(handle)
        problem_list = list(filter(lambda x: x[1] == 'AC' or (float(x[1]) >= 100 - 0.1), problem_list))
        problem_list = list(filter(lambda x: filt.filter(datetime.strptime(x[2], '%Y/%m/%d')), problem_list))
        if len(problem_list) == 0:
            await ctx.send('Không tìm thấy submission của `{0}` với các tham số hiện tại.'.format(handle))
            return
        problem_list = sorted(problem_list, key=lambda x: x[2], reverse=True)[:10]
        problem_list = list(map(lambda x: (RankingDb.RankingDb.get_problem_info(x[0]), x[1], x[2]), problem_list))

        msg = ''
        for p in problem_list:
            msg += to_message(p) + '\n'
        title = "Các bài vừa được giải bởi " + handle

        embed = discord.Embed(title=title, description=msg)
        await ctx.send(embed=embed)

    def get_rating_change(self, handle):
        # problem id, result, date
        raw_subs = RankingDb.RankingDb.get_info_solved_problem(handle)
        raw_subs = list(filter(lambda x: (x[1] == 'AC') or (float(x[1]) > 0.01), raw_subs))
        raw_subs = sorted(raw_subs, key=lambda x: x[2])
        problem_points = common.get_problem_points()
        rating_changes = [(-1, -1)]
        rating = 0
        for problem_id, result, date in raw_subs:
            if rating_changes[-1][1] != date:
                rating_changes.append((0, date))
            if result == 'AC':
                result = 100
            # rating += problem_points[int(problem_id)] * float(result) / 100
            rating += 2 * float(result) / 100
            rating_changes[-1] = (rating, date)
        return rating_changes[1:]

    @commands.command(brief="Hiện phân phối điểm")
    async def distrib(self, ctx):
        """
        Hiện phân phối điểm của các bài tập.
        """
        bin_size = 0.2
        bins = 10

        height = [0] * bins
        problem_points = common.get_problem_points()
        for p, point in problem_points.items():
            height[min(bins - 1, int(point // bin_size))] += 1
        x = [k * bin_size for k in range(bins)]
        label = ['{:.2f} ({})'.format(r, c) for r,c in zip(x, height)]
        colors = []
        for rank in badge.RATED_RANKS:
            colors.append('#' + '%06x' % rank.color_embed)
        colors = colors[:bins]
        assert len(colors) > 0, 'Expected colors len is greater than 0'
        while len(colors) < bins:
            colors.append(colors[-1])
        
        plt.clf()
        plt.xlabel('Point')
        plt.ylabel('Number of problems')
        plt.xticks(rotation=45)
        plt.bar(x, height, bin_size*0.9, color=colors, tick_label=label)
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(
            title="Phân phối điểm của bài tập VOJ")
        discord_common.attach_image(embed, discord_file)
        # discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)
    @commands.command(brief="Hiện historgram về thời gian làm bài",
                      usage='[handle] [d>=[[dd]mm]yyyy] [d<[[dd]mm]yyyy]')
    async def hist(self, ctx, *args):
        """Hiện histogram về thời gian làm bài của handle cho trước.
        Ví dụ ;voj hist CKQ d<16022020 d>=05062019
        """
        filt = DayFilter()
        handle = filt.parse(args)
        handle = await common.get_handle(ctx, handle)
        if handle is None:
            return
        raw_subs = RankingDb.RankingDb.get_info_solved_problem(handle)
        raw_subs = list(filter(lambda x: filt.filter(
            datetime.strptime(x[2], '%Y/%m/%d')), raw_subs))
        if len(raw_subs) == 0:
            await ctx.send('Không tìm thấy submission của `{0}` với các tham số hiện tại.'.format(handle))
            return
        subs = []
        types = ['AC', 'IC', 'PC']
        solved_by_type = {'AC': [], 'IC': [], 'PC': []}
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

        all_times = [[datetime.strptime(date, '%Y/%m/%d')
                      for date in solved_by_type[t]] for t in types]
        labels = ['Accepted', 'Incorrect', 'Partial Result']
        colors = ['g', 'r', 'y']
        plt.hist(all_times, stacked=True, label=labels, bins=34, color=colors)
        total = sum(map(len, all_times))
        plt.legend(title=f'{handle}: {total}',
                   title_fontsize=plt.rcParams['legend.fontsize'])

        plt.gcf().autofmt_xdate()
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(
            title='Số bài làm theo thời gian.')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)

    @commands.command(brief="Hiện histogram của toàn group.",
                      usage='[d>=[[dd]mm]yyyy] [d<[[dd]mm]yyyy]')
    async def group_hist(self, ctx, *args):
        """Hiện histogram của toàn group.
        Ví dụ ;voj group_hist  d<16022020 d>=05062019
        """
        filt = DayFilter()
        handle = filt.parse(args)

        solved_info = RankingDb.RankingDb.get_data('solved_info', limit=None)
        raw_subs = []
        for user_id, problem_id, result, date in solved_info:
            if str(user_id) not in WHILELIST_USER_IDs:
                raw_subs.append((problem_id, result, date))

        raw_subs = list(filter(lambda x: filt.filter(datetime.strptime(x[2], '%Y/%m/%d')), raw_subs))
        if len(raw_subs) == 0:
            await ctx.send('Không tìm thấy submission với các tham số hiện tại.')
            return
        subs = []
        types = ['AC', 'IC', 'PC']
        solved_by_type = {'AC': [], 'IC': [], 'PC': []}
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

        all_times = [[datetime.strptime(date, '%Y/%m/%d')
                      for date in solved_by_type[t]] for t in types]
        labels = ['Accepted', 'Incorrect', 'Partial Result']
        colors = ['g', 'r', 'y']
        plt.hist(all_times, stacked=True, label=labels, bins=34, color=colors)
        total = sum(map(len, all_times))
        plt.legend(
            title=f'VNOI Group: {total}', title_fontsize=plt.rcParams['legend.fontsize'])

        plt.gcf().autofmt_xdate()
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(
            title='Số bài làm theo thời gian.')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed, file=discord_file)

    @commands.command(brief="Hiện biểu đồ kinh nghiệm",
                      usage='[handle] [d>=[[dd]mm]yyyy] [d<[[dd]mm]yyyy]')
    async def exp(self, ctx, *args):
        """
        Hiện biểu đồ kinh nghiệm của handle cho trước.
        Ví dụ ;voj exp CKQ d<16022020 d>=05062019
        """
        filt = DayFilter()
        handle = filt.parse(args)
        handle = await common.get_handle(ctx, handle)
        if handle is None:
            return
        if badge.MAX_SCORE == None:
            await ctx.send('Ranking chưa được tính, ping Cá Nóc.')
            return
        resp = self.get_rating_change(handle)
        resp = list(filter(lambda x: filt.filter(
            datetime.strptime(x[1], '%Y/%m/%d')), resp))
        if len(resp) == 0:
            await ctx.send('Không tìm thấy submission của `{0}` với các tham số hiện tại.'.format(handle))
            return
        plt.clf()
        _plot_rating([resp], MAX_SCORE=badge.MAX_SCORE)
        current_rating = resp[-1][0]
        current_badge = badge.point2rank(current_rating, badge.MAX_SCORE)
        rank_title = current_badge.title + " {:.3f}".format(current_rating)
        labels = [f'\N{ZERO WIDTH SPACE}{handle} ({rank_title})']
        plt.legend(labels, loc='upper left')
        min_rating = current_rating
        max_rating = current_rating
        for rating, date in resp:
            min_rating = min(min_rating, rating)
            max_rating = max(max_rating, rating)
        max_rating = max(max_rating, min(100, current_badge.high) * badge.MAX_SCORE)

        min_rating -= 5 * badge.MAX_SCORE / 100
        max_rating += 5 * badge.MAX_SCORE / 100
        if min_rating < 0:
            min_rating = 0
        msg = ""
        if current_badge.high < 100:
            upper_bound = current_badge.high * badge.MAX_SCORE
            nxt_badge = badge.point2rank(upper_bound + 1)
            msg = "{} cố lên, chỉ cần khoảng {:.2f} exp nữa là lên {} rồi {}.".format(
                ctx.author.mention, upper_bound, nxt_badge.title
                '<:megu_hi:699156503705288754>'
            )
        discord_file = gc.get_current_figure_as_file()
        embed = discord_common.cf_color_embed(
            title='Biểu đồ kinh nghiệm trong group VNOI.')
        discord_common.attach_image(embed, discord_file)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(msg, embed=embed, file=discord_file)

def setup(bot):
    bot.add_cog(Graph(bot))
