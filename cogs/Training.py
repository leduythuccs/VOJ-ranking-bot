from discord.ext import commands
import discord
import asyncio
import os
import time
import subprocess
import textwrap
import sys
from helper import RankingDb
from helper import discord_common
from helper import common
import random
import json
# Adapted from TLE sources.
# https://github.com/cheran-senthil/TLE/blob/master/tle/cogs/meta.py#L15

def to_message(p, problem_point):
    # p[0] -> id
    # p[1] -> name
    # p[2] -> link
    # p[3] -> cnt_AC
    links = p[2].strip(',').split(',')
    links = list(map(lambda x: "https://codeforces.com/group/FLVn1Sc504/contest/{0}/problem/{1}".format(x.split('/')[0], x.split('/')[1]), links))
    msg = ""
    if len(links) == 1:
        msg = "[{0}]({1}) ".format(p[1], links[0])
    else:
        msg = "[{0}]({1}) ".format(p[1], links[0])
        for i, link in enumerate(links[1:]):
            msg += "[link{0}]({1}) ".format(i + 2, link)
    msg += "({:.2f} exp)".format(problem_point[int(p[0])])
    return msg
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:  
        return False

class Training(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link = {}
        self.solution_links = {}
        self.tag = {}
        self.category = {}
    @commands.Cog.listener()
    async def on_ready(self):
        self.update_link()
        
        self.problems_cache = RankingDb.RankingDb.get_data('problem_info', limit=None)

    def update_link(self):
        data = open('database/codeforces_link.txt').read().strip().split('\n')
        for x in data:
            name, link = x.split(' ')
            if name not in self.link:
                self.link[name] = ""
            self.link[name] += link + ','
        self.tag = json.load(open('database/full_tag.json'))
        self.category = json.load(open('database/category.json'))

    def get_un_solved_problem(self, handle):
        if handle not in RankingDb.un_solved_problem_cache:
            problem_list = RankingDb.RankingDb.get_info_solved_problem(handle)
            problem_list = list(filter(lambda x: (x[1] == 'AC' or (float(x[1]) > 100 - 0.1)), problem_list))
            #id, result, data
            problem_list = set(map(lambda x: int(x[0]), problem_list))
            #id, name, link, cnt_AC
            un_solved_problem = list(filter(lambda x: int(x[0]) not in problem_list, self.problems_cache))
            RankingDb.un_solved_problem_cache[handle] = un_solved_problem
        return RankingDb.un_solved_problem_cache[handle]

    @commands.command(brief="Lấy link bài tập trên codeforces.")
    async def getlink(self, ctx, name):
        """
        Lấy link của bài tập trên codeforces, ví dụ nếu mình muốn lấy link bài AZNET thì dùng:
        ;voj getlink AZNET
        """
        name = name.upper()
        if name not in self.link:
            await ctx.send('Không tìm thấy bài {0}.'.format(name))
            return
        links = self.link[name].strip(',').split(',')
        links = list(map(lambda x: '<' + x + '>', links))
        await ctx.send('\n'.join(links))

    @commands.command(brief="Đề xuất bài tập.",
                      usage="[tag] [lower_point] [upper_point]")
    async def gimme(self, ctx, *args):
        """
        Đề xuất một số bài tập theo dạng. 
        Có một số tag sau đây: [DP, DS, geometry, graph, math, string, ad-hoc, other]
        Ví dụ ;voj gimme DP 0.2 0.5 là list các bài DP có độ khó từ 0.2 tới 0.5
        """
        low = 0 - 0.1
        hi = 2 + 0.1
        bound = []
        tag = ""
        for arg in args:
            if is_float(arg):
                bound.append(float(arg))
            else:
                tag = arg
        if len(bound) == 1:
            low = max(low, bound[0])
        elif len(bound) == 2:
            low = max(low, bound[0])
            hi = min(hi, bound[1])
        category = tag.upper()
        if category != "" and category not in self.category:
            await ctx.send('không tìm thấy category `{0}`. '.format(tag) +
                           'Chỉ dùng các tag sau đây `[DP, DS, geometry, graph, math, string, ad-hoc, other]`. '
                           'Tham khảo trang <http://vnoi.info/problems/list/> để có danh sách tag chi tiết hơn.')
            return
        handle = await common.get_handle(ctx, None)
        if handle is None:
            return
        problem_point = common.get_problem_points()
        un_solved_problem = self.get_un_solved_problem(handle)
        if category != "":
            un_solved_problem = list(filter(lambda x: x[1][:x[1].find('-')].strip() in self.category[category], un_solved_problem))
        un_solved_problem = list(filter(lambda p: low <= problem_point[int(p[0])] and problem_point[int(p[0])] <= hi, un_solved_problem))
        if len(un_solved_problem) == 0:
            await ctx.send('Không tìm được bài tập nào với các tham số hiện tại.')
            return
        problems = random.sample(un_solved_problem, k = min(10, len(un_solved_problem)))
        if tag == "":
            tag = "ngẫu nhiên"
        title = "{0} bài {1}".format(len(problems), tag)
        msg = ""
        for p in problems:
            msg += to_message(p, problem_point) + "\n"
        embed=discord.Embed(title=title,description=msg.strip(), color=discord_common._SUCCESS_BLUE_)
        discord_common.set_author_footer(embed, ctx.author)
        await ctx.send(embed=embed)
        
    @commands.command(brief="Lấy lời giải của bài tập.")
    async def solution(self, ctx, name):
        """
        Lấy lời giải của bài tập, nếu mình muốn lấy giải bài AZNET thì dùng:
        ;voj solution AZNET
        Lưu ý là có rất ít bài có giải.
        """
        name = name.upper()
        # if name not in self.solution_links:
        #     await ctx.send('Tự mà nghĩ đi chứ tôi lấy đâu ra giải cho ông.')
        #     return
        link = 'https://vnoi.info/problems/list_solutions/{}/'.format(name)
        embed=discord.Embed(description='[{0}]({1})'.format(name, link), color=discord_common._SUCCESS_BLUE_)
        if ctx.author.id != 554842563170009089:
            await ctx.send('Đọc giải ít thôi. Lưu ý là có thể link vnoi info không tồn tại <:sadness:662197924918329365>.', embed=embed)
        else:
            await ctx.send(embed=embed)
    @commands.command(brief="Lấy tag của một bài tập")
    async def tag(self, ctx, name):
        """
        Lấy tag của một bài tập, nếu mình muốn lấy tag của bài C11FBR thì dùng:
        ;voj tag C11FBR
        """
        name = name.upper()
        if name not in self.tag:
            await ctx.send('Hong tìm thấy tag của bài {0} <:testing:665243100028862514>'.format(name))
            return
        msg = '\n'.join(self.tag[name])
        embed = discord.Embed(description=msg, color=discord_common._SUCCESS_BLUE_)
        await ctx.send(embed=embed)
    
def setup(bot):
    bot.add_cog(Training(bot))
