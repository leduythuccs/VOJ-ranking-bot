
import requests
from discord.ext import commands

class CodeforcesApiError(commands.CommandError):
    """Base class for all API related errors."""
    def __init__(self, message=None):
        super().__init__(message or 'Codeforces API error')

class TrueApiError(CodeforcesApiError):
    """An error originating from a valid response of the API."""
    def __init__(self, comment, message=None):
        super().__init__(message)
        self.comment = comment


class HandleNotFoundError(TrueApiError):
    def __init__(self, comment, handle):
        super().__init__(comment, f'Không tìm thấy nick `{handle}` trên codeforces')


class HandleInvalidError(TrueApiError):
    def __init__(self, comment, handle):
        super().__init__(comment, f'`{handle}` không phải là một nick hợp lệ trên codeforces')


class CallLimitExceededError(TrueApiError):
    def __init__(self, comment):
        super().__init__(comment, 'Codeforces API call limit exceeded')



BASE_status = 'https://codeforces.com/api/user.status?handle={0}&from=1&count=5&lang=en'
def get_all_problems():
    url = 'https://codeforces.com/api/problemset.problems?lang=en'
    try:
        r = requests.get(url, timeout=2).json()
        res = []
        problems = r['result']['problems']
        for p in problems:
            res.append((p['contestId'], p['index'], p['name']))
        return res
    except Exception as e:
        print(e)
        return [
            (1333, 'F', 'Kate and imperfection'),
            (1333, 'E', 'Road to 1600'), (1333,'D', 'Challenges in school №41'),
            (1333, 'C', 'Eugene and an array'), (1333, 'B', 'Kind Anton'),
            (1333, 'A', 'Little Artem'), (1332, 'G', 'No Monotone Triples'),
            (1332, 'F', 'Independent Set'), (1332, 'E', 'Height All the Same'),
            (1332, 'D', 'Walk on Matrix')
        ]
problems = get_all_problems()
async def get_user_status(handle):
    url = BASE_status.format(handle)
    try:
        resp = requests.get(url, timeout=2)
        try:
            r = resp.json()
        except Exception as e:
            comment = f'CF API did not respond with JSON, status {resp.status}.'
            raise CodeforcesApiError(comment)
        if 'comment' in r:
            comment = r['comment']
        else:
            res = []
            for x in r['result']:
                res.append(x['problem']['name'])
            return res
    except Exception as e:
        print(e)
        raise TrueApiError(str(e))
    if 'limit exceeded' in comment:
        raise CallLimitExceededError(comment)
    if 'not found' in comment:
        raise HandleNotFoundError(comment, handle)
    if 'should contain' in e.comment:
        raise HandleInvalidError(comment, handle)
                
    raise TrueApiError(comment)

    
