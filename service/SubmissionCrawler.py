import re
import requests
import os
from bs4 import BeautifulSoup as bs
from datetime import datetime
csrf_token_pattern = r'name=["\']csrf_token["\'] value=["\'](.*?)["\']'
ftaa_pattern = r'window._ftaa = ["\'](.*?)["\']'
bfaa_pattern = r'window._bfaa = ["\'](.*?)["\']'
SUBMISSION_BASE = 'https://codeforces.com/group/{0}/status?pageIndex={1}&showUnofficial=true'

def get_date(s):
    t = s[:s.find(' ')].strip()
    t = datetime.strptime(t, '%b/%d/%Y')
    return datetime.strftime(t, '%Y/%m/%d')

class Crawler:
    def __init__(self, username, password, group_id):
        self.username = username
        self.password = password
        self.group_id = group_id
        
        self.session = requests.session()
        self.last_submission = int(open('database/last_submission.txt').read().strip())
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
        }
        self.first_un_crawl_submission = 0

    def save_last_submission(self):
        open('database/last_submission.txt', 'w').write(str(self.last_submission))

    def login(self):
        url = 'https://codeforces.com/enter'
        result = self.session.get(url, headers=self.headers)
        
        self.csrf_token = re.findall(csrf_token_pattern, result.text)[0]
        self.ftaa = re.findall(ftaa_pattern, result.text)[0]
        self.bfaa = re.findall(bfaa_pattern, result.text)[0]
        data = {
            'csrf_token': self.csrf_token,
            'ftaa': self.ftaa,
            'bfaa': self.bfaa,
            '_tta': 487,
            #stuff
            'action': 'enter',
            'handleOrEmail': self.username,
            'password': self.password,
        }
        login_result = self.session.post(url, data=data, headers=self.headers)
        return self.check_login()

    def check_login(self):
        url = 'https://codeforces.com/settings/general'
        result = self.session.get(url, headers=self.headers, allow_redirects = False)
        if not result.is_redirect:
            print(self.username + " logged to codeforces.")
            return True
        
        print('Login failed!')
        return False
    
    def get_info_submission(self, row, force = False):
        '''
            Get infomation about submission, return a tuple:
                (id, problem_name, short link to problem, handle, user_id, verdict (AC/point), date)
            - return None if the submission is judging or it's a team's submission
            - if the submission's id is less than last submission's id:
                + if 'force' set to True, the submission will re-crawl
                + otherwise, return -1
        '''
        submission_id = int(row['data-submission-id'])
        if submission_id <= self.last_submission and force == False:
            return -1
        user_id = row['partymemberids'].strip(';')
        elems = row.find_all('td')
        assert(len(elems) == 8)
        # id   WHEN    WHO     PROBLEM     LANG    VERDICT     TIME    MEMORY

        date = get_date(elems[1].text.strip())
        handle = elems[2].text.strip()
        #team
        if str(elems[2]).find('/team/') != -1:
            return None
        
        problem_name = elems[3].text.strip()
        problem_name = problem_name[problem_name.find('-')+1:].strip()

        short_link = '/'.join(re.findall('contest/(\d+)/problem/(\w+)', elems[3].a['href'])[0])
        contest_id, junk = short_link.split('/')
        if str(contest_id) in open('database/contest_id_whitelist.txt').read().strip().split('\n'):
            print("found white list submission")
            return None

        if elems[5].has_attr('waiting') and elems[5]['waiting'] != 'false':
            self.first_un_crawl_submission = min(self.first_un_crawl_submission, submission_id)
            return None
        
        verdict = elems[5].span['submissionverdict']
        if verdict == 'OK':
            verdict = 'AC'
        if verdict == 'PARTIAL':
            verdict = elems[5].span.span.text.strip()
        elif verdict != 'AC':
            verdict = '0'
        
        return (submission_id, problem_name, short_link, handle, user_id, verdict, date)


    def crawl_submissions(self, page):
        url = SUBMISSION_BASE.format(self.group_id, page)
        result = self.session.get(url, headers=self.headers)
        soup = bs(result.text, features="html.parser")
        rows = list(filter(lambda x: x.has_attr('data-submission-id'), soup.find_all('tr')))
        infos = []
        stop = False
        for row in rows:
            r = self.get_info_submission(row)
            if r is None:
                continue
            
            if r == -1:
                stop = True
                break

            infos.append(r)

        return (infos, stop)
    
    def get_new_submissions(self, l, r):
        infos = []
        self.first_un_crawl_submission = 347598374985739845
        for page in range(l, r + 1):
            print("crawling page " + str(page), end=' ')
            new_infos, stop = self.crawl_submissions(page)
            print("Found {0} new submission".format(len(new_infos)))
            infos += new_infos
            if stop:
                break
        for id, *junk in infos:
            self.last_submission = max(self.last_submission, int(id))
        if self.last_submission > self.first_un_crawl_submission:
            self.last_submission = self.first_un_crawl_submission - 1
        self.save_last_submission()
        return infos
    
        