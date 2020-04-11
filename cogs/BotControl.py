from discord.ext import commands
import discord
import asyncio
import os
import time
import subprocess
import textwrap
import sys
# Adapted from TLE sources.
# https://github.com/cheran-senthil/TLE/blob/master/tle/cogs/meta.py#L15


def git_history():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out
    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        branch = out.strip().decode('ascii')
        out = _minimal_ext_cmd(['git', 'log', '--oneline', '-5'])
        history = out.strip().decode('ascii')
        return (
            'Branch:\n' +
            textwrap.indent(branch, '  ') +
            '\nCommits:\n' +
            textwrap.indent(history, '  ')
        )
    except OSError:
        return "Fetching git info failed"


class BotControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     pass
    
    # from TLE bot.
    @commands.command(brief="Check if bot is still alive.")
    async def ping(self, ctx):
        """Replies to a ping."""
        start = time.perf_counter()
        message = await ctx.send('<:pingreee:665243570655199246>')
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(content=f'<:pingreee:665243570655199246>\nREST API latency: {int(duration)}ms\n'
                                    f'Gateway API latency: {int(self.bot.latency * 1000)}ms')

    @commands.command(brief="Kill bot. ")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def kill(self, ctx):
        """Kill bot"""
        await ctx.send("Dying")
        exit(0)

    @commands.command(brief='Restart bot')
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def restart(self, ctx):
        await ctx.send('Restarting...')
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @commands.command(brief="Update bot & restart")
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def update_restart(self, ctx):
        await self.git_pull(ctx)
        await self.restart(ctx)

    @commands.command(brief='Get git information')
    async def git(self, ctx):
        """Replies with git information."""
        await ctx.send('```yaml\n' + git_history() + '```')

    @commands.command(brief='Incorporates changes from the remote repository')
    @commands.check_any(commands.is_owner(), commands.has_any_role('Admin', 'Mod VNOI'))
    async def git_pull(self, ctx):
        mess = await ctx.send('Getting changes from the remote repository...')
        result = subprocess.run(
            ['git', 'pull'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        await mess.edit(content='```\n' + result + '\n```')


def setup(bot):
    bot.add_cog(BotControl(bot))
