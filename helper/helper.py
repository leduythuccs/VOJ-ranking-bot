
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
