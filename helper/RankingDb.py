from typing import Dict
import pymongo
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
un_solved_problem_cache:Dict[str, list] = {}
PROBLEM_TABLE = 'problems'
SUBMISSION_TABLE = 'submissions'
USER_TABLE = 'users'
USER_DISCORD_TABLE = 'usersDiscord'
LOG_TABLE = 'logs'
class RankingDbConn:
    def __init__(self, link, database):
        self.database = pymongo.MongoClient(link)[database]

    def insert(self, table, doc):
        return self.database[table].insert_one(doc).inserted_id

    def update(self, table, doc_filter, new_value):
        return self.database[table].update_one(doc_filter, {"$set" : new_value})

    def update_many(self, table, doc_filter, new_value):
        return self.database[table].update_many(doc_filter, {"$set" : new_value})

    def insert_many(self, table, docs):
        return self.database[table].insert_many(docs).inserted_ids

    def get_first(self, table):
        return self.database[table].find_one()

    def delete(self, table, doc):
        return self.database[table].delete_one(doc).deleted_count

    def delete_table(self, table):
        return self.database[table].drop()

    def get_table(self, table):
        return list(self.database[table].find())

    def find(self, table, doc):
        return self.database[table].find_one(doc)

    def find_all(self, table, doc):
        return self.database[table].find(doc)

    def check_exists(self, table, where, value):
        return self.find(table, {where : value}) is not None

    def log(self, msg: str):
        doc = {
            'message': msg,
            'time': datetime.now().strftime('%x %X')
        }
        self.insert(LOG_TABLE, doc)

    def add_problem(self, problem_name: str, contest_id: int,
                    problem_index: str) -> int:
        problem_name = problem_name.strip()
        problem = self.find(PROBLEM_TABLE, {'name': problem_name})
        if problem is not None:
            return problem['cntAC']
        doc = {
            'name': problem_name,
            'contestId': contest_id,
            'index': problem_index,
            'cntAC': 0
        }
        self.insert(PROBLEM_TABLE, doc)
        return 0

    def add_AC(self, problem_name: str, current_AC: int):
        self.update(PROBLEM_TABLE, {'name': problem_name}, {'cntAC': current_AC + 1})

    def add_solved_info(self, problem_name: str, point: float, submission_contest: int, submission_id: int, codeforces_id: int, timestamp: int, current_AC: int) -> None:
        doc = {
            'problemName': problem_name,
            'point': point,
            'contest': submission_contest,
            'id': submission_id,
            'accepted': (point >= 100),
            'codeforcesId': codeforces_id,
            'timestamp': timestamp
        }

        pre_result = self.find(SUBMISSION_TABLE, {'problemName': problem_name, 'codeforcesId': codeforces_id})
        if pre_result is not None:
            pre_point = pre_result['point']
            if (pre_point >= point):
                return
            self.update(SUBMISSION_TABLE, pre_result, doc)
        else:
            self.insert(SUBMISSION_TABLE, doc)
        if point >= 100:
            self.add_AC(problem_name, current_AC)

    def add_user(self, CF_id: int, handle: str):
        doc = self.find(USER_TABLE, {'codeforcesId': CF_id})
        if doc is None:
            self.insert(USER_TABLE, {'handle': handle, 'codeforcesId': CF_id})
        elif doc['codeforcesId'] != CF_id:
            old_handle = doc['codeforcesId']
            self.update(USER_TABLE, {'handle': old_handle}, {'handle': handle})
            msg = f"User id: {CF_id} change handle from {old_handle} to {handle}."
            self.insert(LOG_TABLE, msg)
    
    def get_handle_by_cf_id(self, CF_id: int):
        doc = self.find(USER_TABLE, {'codeforcesId': CF_id})
        return doc['handle'] if doc is not None else None

    def get_cf_id_by_handle(self, handle: str):
        doc = self.find(USER_TABLE, {'handle': handle})
        return doc['codeforcesId'] if doc is not None else None

    def get_info_solved_problem(self, handle):
        cf_id = self.get_cf_id_by_handle(handle)
        if cf_id is None:
            return []
        #problem_name, point, date
        problems = self.find_all(SUBMISSION_TABLE, {'codeforcesId': cf_id})
        return list(map(lambda x: (x['problemName'], x['point'], datetime.fromtimestamp(x['timestamp']).strftime('%Y/%m/%d')), problems))

    def get_problem_info(self, problem_name: str):
        problem = self.find(PROBLEM_TABLE, {'name': problem_name})
        if problem == None:
            return None
        return (problem['name'], str(problem['contestId']) + '/' + problem['index'], problem['cntAC'])


    def handle_new_submission(self, handle: str, codeforces_id: int,
                              submission_contest: int, submission_id: int,
                              point: float, problem_name: str, contest_id: int,
                              problem_index: str, timestamp: int) -> None:
        handle = handle.lower()

        self.add_user(codeforces_id, handle)
        #
        current_AC = self.add_problem(problem_name, contest_id, problem_index)
        #
        self.add_solved_info(problem_name, point, submission_contest, submission_id, codeforces_id, timestamp, current_AC)
        # clear cache
        global un_solved_problem_cache
        if point >= 100:
            if handle in un_solved_problem_cache is True:
                un_solved_problem_cache.pop(handle)



    def set_handle(self, discord_id: int, handle: str) -> int:
        handle = handle.lower()
        doc = self.find(USER_DISCORD_TABLE, {'handle': handle})
        if doc is not None:
            return doc['discordId']
        pre_handle = self.get_handle(discord_id)
        if pre_handle is None:
            self.insert(USER_DISCORD_TABLE, {'handle': handle, 'discordId': discord_id})
        else:
            self.update(USER_DISCORD_TABLE, {'handle': pre_handle}, {'handle': handle})
        return 0

    def get_handle(self, discord_id: int):
        doc = self.find(USER_DISCORD_TABLE, {'discordId' : discord_id})
        return doc['handle'] if doc is not None else None

    def get_all_problems(self):
        return self.get_table(PROBLEM_TABLE)

link = os.getenv('MONGO_LINK')
RankingDb = RankingDbConn(link, "crawlerDb")