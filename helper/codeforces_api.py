
import requests
BASE_status = 'https://codeforces.com/api/user.status?handle={0}&from=1&count=5&lang=en'
async def get_user_status(handle):
    url = BASE_status.format(handle)
    try:
        r = requests.get(url).json()
        res = []
        for x in r['result']:
            res.append(
                {
                    'verdict': x['verdict'],
                    'problem_name': x['problem']['name']
                }
            )
        return res
    except Exception as e:
        print(e)
        return []
    