from discord.ext import commands
import discord
import asyncio
import os
import time
import subprocess
import textwrap
import sys
from helper import helper
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


class GetCodeforcesLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link = {}
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.update_link()
        pass

    def update_link(self):
        data = open('database/codeforces_link.txt').read().strip().split('\n')
        for x in data:
            name, link = x.split(' ')
            if name not in self.link:
                self.link[name] = ""
            self.link[name] += link + ','
    
    @commands.command(brief="Get codeforces link of VOJ problem")
    async def getlink(self, ctx, name):
        name = name.upper()
        if name not in self.link:
            await ctx.send('Problem {0} not found.'.format(name))
            return
        links = self.link[name].strip(',').split(',')
        links = list(map(lambda x: '<' + x + '>', links))
        await ctx.send('\n'.join(links))

    


def setup(bot):
    bot.add_cog(GetCodeforcesLink(bot))
