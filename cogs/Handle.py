from discord.ext import commands
import discord
import asyncio
import os
from helper import RankingDb
import requests
import time
from helper import codeforces_api
import random
SET_HANDLE_SUCCESS = 'Nick cho <@{0}> đã được set thành <https://codeforces.com/profile/{1}>'

class Handle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Set nick codeforces để dùng bot")
    async def identify(self, ctx, handle): 
        discord_id = ctx.author.id
        problem = random.choice(codeforces_api.problems)
        await ctx.send(f'`{str(ctx.author)}`, Hãy nộp một submission bị dịch lỗi tới bài <https://codeforces.com/problemset/problem/{problem[0]}/{problem[1]}> trong 60 giây')
        for i in range(6):
            await asyncio.sleep(10)
            subs = await codeforces_api.get_user_status(handle)

            if any(sub['problem_name'] == problem[2] and sub['verdict'] == 'COMPILATION_ERROR' for sub in subs):
                x = RankingDb.RankingDb.set_handle(discord_id, handle)
                if x != True:
                    await ctx.send('Lỗi, nick {0} đã được set cho user <@{1}>'.format(handle, x))
                else:
                    await ctx.send(SET_HANDLE_SUCCESS.format(discord_id, handle))
                    RankingDb.RankingDb.conn.commit()
                return
        await ctx.send(f'`{str(ctx.author)}`, thử lại pls.')

    @commands.command(brief='Set Codeforces handle of a user')
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def set(self, ctx, member: discord.Member, handle):
        if RankingDb.RankingDb.set_handle(member.id, handle, force=True) == True:
            await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))
            RankingDb.RankingDb.conn.commit()
        else:
            await ctx.send("Failed ?? :D ??")

    @commands.command(brief='Lấy nick của user tương ứng')
    async def get(self, ctx, member: discord.Member):
        """Lấy codeforces nick của user discord tương ứng."""
        handle = RankingDb.RankingDb.get_handle(member.id)
        if handle is None:
            await ctx.send(f'Không tìm thấy nick của {member.mention} trong dữ liệu.')
            return
        await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))

def setup(bot):
    bot.add_cog(Handle(bot))