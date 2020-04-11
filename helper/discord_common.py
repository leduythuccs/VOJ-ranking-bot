#source TLE: https://github.com/cheran-senthil/TLE/blob/master/tle/util/discord_common.py
import asyncio
import functools
import random

import discord
from discord.ext import commands


_CF_COLORS = (0xFFCA1F, 0x198BCC, 0xFF2020)
_SUCCESS_GREEN = 0x28A745
_ALERT_AMBER = 0xFFBF00
_SUCCESS_BLUE_ = 0x198BCC


def embed_neutral(desc, color=discord.Embed.Empty):
    return discord.Embed(description=str(desc), color=color)


def embed_success(desc):
    return discord.Embed(description=str(desc), color=_SUCCESS_GREEN)

def embed_alert(desc):
    return discord.Embed(description=str(desc), color=_ALERT_AMBER)


def cf_color_embed(**kwargs):
    return discord.Embed(**kwargs, color=random.choice(_CF_COLORS))


def attach_image(embed, img_file):
    embed.set_image(url=f'attachment://{img_file.filename}')


def set_author_footer(embed, user):
    embed.set_footer(text=f'Requested by {user}', icon_url=user.avatar_url)