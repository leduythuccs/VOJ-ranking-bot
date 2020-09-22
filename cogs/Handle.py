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

    @commands.command(brief="Set nick codeforces để dùng bot.",
    usage="nick codeforces của bạn.")
    async def identify(self, ctx, handle): 
        """
        Dùng command này để set nick codeforces.
        Bot sẽ yêu cầu bạn nộp một code bị dịch lỗi tới bài nào đó trong vòng 60s.
        Nếu nick codeforces mình là `leduykhongngu` thì mình dùng:
        ;voj identify leduykhongngu
        """
        discord_id = ctx.author.id
        tmp = RankingDb.RankingDb.get_handle(discord_id)
        if tmp is not None:
            await ctx.send('Ông identify lần 2 làm cái gì. Có nick {0} chưa đủ à'.format(tmp))
            return
        subs = await codeforces_api.get_user_status(handle)
        problem = random.choice(codeforces_api.problems)
        await ctx.send(f'<@{str(ctx.author.id)}>, Hãy nộp một submission bị DỊCH LỖI tới bài <https://codeforces.com/problemset/problem/{problem[0]}/{problem[1]}> trong 60 giây')
        for i in range(6):
            await asyncio.sleep(10)
            subs = await codeforces_api.get_user_status(handle)
            if any(sub == problem[2] for sub in subs):
                x = RankingDb.RankingDb.set_handle(discord_id, handle)
                if x != 0:
                    await ctx.send('Lỗi, nick {0} đã được set cho user <@{1}>. Gọi @Cá nóc cắn cáp nếu cần giúp đỡ'.format(handle, x))
                else:
                    await ctx.send(SET_HANDLE_SUCCESS.format(discord_id, handle))
                return
        await ctx.send(f'<@{str(ctx.author.id)}>, thử lại pls. Dùng `;voj help identify` nếu cần giúp đỡ.')

    @commands.command(brief='Set Codeforces handle of a user')
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def set(self, ctx, member: discord.Member, handle):
        # message = (
        #     "Vẫn đang được dev, xin quay lại sau ...\n"
        #     "~~Vì lý do đặc biệt nên xem xét dùng các command sau:\n"
        #     "- Nếu user chưa identify bao giờ -> ;voj set_new @member handle\n"
        #     "- Nếu user muốn đổi acc codeforces -> ;voj change @member new_handle\n"
        #     "- Nếu user dùng acc discord mới -> ;voj ~~"
        # )
        # await ctx.send(message)
        # return
        # await ctx.send("Cẩn thận khi dùng cái này, nên hú Thức cho chắc.")
        if RankingDb.RankingDb.set_handle(member.id, handle) == 0:
            await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))
        else:
            await ctx.send("Failed ?? :D ??")

    @commands.command(brief='Lấy nick của user tương ứng')
    async def get(self, ctx, member: discord.Member):
        """
        Lấy codeforces nick của user discord tương ứng.
        Nếu mình muốn lấy nick codeforces của Cá Nóc Cắn Cáp, thì dùng:
        ;voj get @cá nóc cắn cáp (tag vào)
        """
        handle = RankingDb.RankingDb.get_handle(member.id)
        if handle is None:
            await ctx.send(f'Không tìm thấy nick của {member.mention} trong dữ liệu. Xin hãy dùng command ;voj identify nick_cf')
            return
        await ctx.send(SET_HANDLE_SUCCESS.format(member.id, handle))

def setup(bot):
    bot.add_cog(Handle(bot))