from datetime import datetime
from discord.ext import commands
class FilterError(commands.CommandError):
    pass
class ParamParseError(FilterError):
    pass

def time_format(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds


def pretty_time_format(seconds):
    days, hours, minutes, seconds = time_format(seconds)
    timespec = [
        (days, 'day', 'days'),
        (hours, 'hour', 'hours'),
        (minutes, 'minute', 'minutes'),
        (seconds, 'second', 'seconds')
    ]
    timeprint = [(cnt, singular, plural) for cnt, singular, plural in timespec if cnt]

    def format_(triple):
        cnt, singular, plural = triple
        return f'{cnt} {singular if cnt == 1 else plural}'

    return ' '.join(map(format_, timeprint))

def parse_date(arg):
    try:
        if len(arg) == 8:
            fmt = '%d%m%Y'
        elif len(arg) == 6:
            fmt = '%m%Y'
        elif len(arg) == 4:
            fmt = '%Y'
        else:
            raise ValueError
        return datetime.strptime(arg, fmt)
    except ValueError:
        raise ParamParseError(f'{arg} is an invalid date argument')

class DayFilter():
    def __init__(self):
        self.low = datetime.strptime("2000", "%Y")
        self.hi = datetime.strptime("3000", "%Y")
    def filter(self, date):
        return self.low <= date and date < self.hi
    
    def parse(self, args):
        args = list(set(args))
        handle = None
        for arg in args:
            if arg[0:2] == 'd<':
                self.hi = min(self.hi, parse_date(arg[2:]))
            elif arg[0:3] == 'd>=':
                self.low = max(self.low, parse_date(arg[3:]))
            else:
                handle = arg
        return handle