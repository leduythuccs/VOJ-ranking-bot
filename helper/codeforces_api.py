
import requests

BASE_status = 'https://codeforces.com/api/user.status?handle={0}&from=1&count=5&lang=en'
def get_all_problems():
    url = 'https://codeforces.com/api/problemset.problems?lang=en'
    try:
        r = requests.get(url).json()
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

    
