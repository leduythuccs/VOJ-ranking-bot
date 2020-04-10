import sqlite3
import csv

class RankingDbConn:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.create_table()

    def create_table(self):
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS problem_info ('
            'id             INTEGER PRIMARY KEY AUTOINCREMENT,'
            'problem_name   TEXT,'
            'links          TEXT,'
            'cnt_AC         INTEGER'
            ')'
        )

        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS user_data ('
            'CF_id          INTEGER,'
            'handle         TEXT,'
            'discord_id     TEXT'
            ')'
        )
        
        self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_problem_info '
            'ON problem_info (problem_name)'
        )
        #yyyy/mm/dd
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS solved_info ('
            'user_id        INTEGER,'
            'problem_id     TEXT,'
            'result         TEXT,'
            'date           TEXT'
            ')'
        )

        self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_solved_info '
            'ON solved_info (user_id)'
        )

    def check_exists(self, table, where, value):
        query = (
            'SELECT 1 '
            'FROM {0} '.format(table) +
            'WHERE {0} = ?'.format(where)
        )
        res = self.conn.execute(query, (value, )).fetchone()
        return res is not None


    def add_problem(self, problem_name, problem_links):
        problem_name = problem_name.strip()
        query = (
            'SELECT links, id, cnt_AC '
            'FROM problem_info '
            'WHERE problem_name = ?'
        )
        cur = self.conn.cursor()
        res = cur.execute(query, (problem_name, )).fetchone()
        query = (
            'INSERT INTO problem_info (problem_name, links, cnt_AC) '
            'VALUES (?, ?, 0)'
        )
        if res is not None:
            if (res[0].find(problem_links) != -1):
                return res[1]
            query = (
                'REPLACE INTO problem_info (id, problem_name, links, cnt_AC) '
                'VALUES (?, ?, ?, ?)'
            )
            problem_links = res[0] + ',' + problem_links
            cur.execute(query, (res[1], problem_name, problem_links, res[2]))
        else:
            cur.execute(query, (problem_name, problem_links))
        # self.conn.commit()
        return cur.lastrowid
    
    def add_AC(self, problem_id):
        query = (
            'UPDATE problem_info '
            'SET cnt_AC = cnt_AC + 1 '
            'WHERE id = ?'
        )
        self.conn.execute(query, (problem_id, ))
        # self.conn.commit()
    # clear result of problem_id
    def remove_result(self, problem_id):
        # first, clear in table solved_info
        query = (
            'UPDATE solved_info '
            'SET result = 0 '
            'WHERE problem_id = ? '
        )
        self.conn.execute(query, (problem_id, ))
        # set cnt_AC = 0
        query = (
            'UPDATE problem_info '
            'SET cnt_AC = 0 '
            'WHERE id = ?'
        )
        self.conn.execute(query, (problem_id, ))
        # self.conn.commit()
    
    def get_problem_id(self, problem_name):
        query = (
            'SELECT id '
            'FROM problem_info '
            'WHERE problem_name = ?'
        )
        r = self.conn.execute(query, (problem_name, )).fetchone()
        if r == None:
            return None
        return r[0]
    
    def add_solved_info(self, user_id, problem_id, result, date):
        query = (
            'SELECT result '
            'FROM solved_info '
            'WHERE user_id = ? AND problem_id = ?'
        )
        pre_result = self.conn.execute(query, (user_id, problem_id)).fetchone()
        if pre_result is not None:
            pre_result = pre_result[0]
            if pre_result == 'AC':
                return
            if (result != 'AC') and (float(result) <= float(pre_result)):
                return
        
            query = (
                'UPDATE solved_info '
                'SET result = ?'
                'WHERE user_id = ? AND problem_id = ?'
            )
            self.conn.execute(query, (result, user_id, problem_id))
        else:
            query = (
                'INSERT INTO solved_info (user_id, problem_id, result, date) '
                'VALUES (?, ?, ?, ?) '
            )
            self.conn.execute(query, (user_id, problem_id, result, date))
        if result == 'AC':
            self.add_AC(problem_id)
        # self.conn.commit()
        return

    def add_user(self, CF_id, handle):
        handle = handle.lower()
        if self.check_exists('user_data', 'CF_id', CF_id):
            query = (
                'UPDATE user_data '
                'SET handle = ? '
                'WHERE CF_id = ? ' 
            )
            self.conn.execute(query, (handle, CF_id))
        elif self.check_exists('user_data', 'handle', handle):
            query = (
                'UPDATE user_data '
                'SET CF_id = ? '
                'WHERE handle = ?'
            )
            self.conn.execute(query, (CF_id, handle))
        else:
            query = (
                'INSERT INTO user_data (CF_id, handle) '
                'VALUES (?, ?)'
            )
            self.conn.execute(query, (CF_id, handle))
        # self.conn.commit()
    
    def get_info_solved_problem(self, handle):
        handle = handle.lower()
        query = (
            'SELECT CF_id '
            'FROM user_data '
            'WHERE handle = ?'
        )
        r = self.conn.execute(query, (handle, )).fetchone()
        if r is None:
            return []
        user_id = r[0]
        query = (
            'SELECT problem_id, result, date '
            'FROM solved_info '
            'WHERE user_id = ?'
        )
        r = self.conn.execute(query, (user_id, )).fetchall()
        if r is []:
            return []
        return r

    def get_problem_info(self, problem_id):
        query = (
            'SELECT problem_name, links, cnt_AC '
            'FROM problem_info '
            'WHERE id = ? '
        )
        return self.conn.execute(query, (problem_id, )).fetchone()
    
    # def get_solved_problem(self, handle):
    #     infos = self.get_info_solved_problem(handle)
    #     return infos

    def handle_new_submission(self, problem_name, problem_links,
                              result, author_id, author_handle, submission_date):
        author_handle = author_handle.lower()
        #
        problem_id = self.add_problem(problem_name, problem_links)
        # 
        self.add_solved_info(author_id, problem_id, result, submission_date)
        #
        self.add_user(author_id, author_handle)
    
    def change_handle(self, old_handle, new_handle):
        old_handle = old_handle.lower()
        new_handle = new_handle.lower()
        query = (
            'SELECT CF_id, discord_id '
            'FROM user_data '
            'WHERE handle = ?'
        )
        r = self.conn.execute(query, (old_handle, )).fetchone()
        if r is not None:
            query = (
                'UPDATE user_data '
                'SET CF_id = ?, discord_id = ?, handle = ?, '
                'WHERE handle = ?'
            )
            self.conn.execute(query, (r[0], r[1], new_handle, old_handle))
        else:
            query = (
                'INSERT INTO user_data (handle) '
                'VALUES (?)'
            )
            self.conn.execute(query, (new_handle, ))
        # self.conn.commit()
        
    def set_handle(self, discord_id, handle, force = False):
        handle = handle.lower()
        discord_id = str(discord_id)
        query = (
            'SELECT discord_id '
            'FROM user_data '
            'WHERE handle = ?'
        )
        r = self.conn.execute(query, (handle, )).fetchone()
        if r is not None and r[0] is not None and r[0] != discord_id and not force:
            return r[0]
        if r is not None:
            query = (
                'UPDATE user_data '
                'SET discord_id = ? '
                'WHERE handle = ? '
            )
        else:
            query = (
                'SELECT handle '
                'FROM user_data '
                'WHERE discord_id = ?'
            )
            r = self.conn.execute(query, (discord_id, )).fetchone()
            if r is None:
                query = (
                    'INSERT INTO user_data (discord_id, handle) '
                    'VALUES (?, ?)'
                )
            else:
                query = (
                    'UPDATE user_data '
                    'SET handle = ? '
                    'WHERE discord_id = ?'
                )
                discord_id, handle = handle, discord_id # swap
        self.conn.execute(query, (discord_id, handle))
        # self.conn.commit()
        return True
    
    def get_handle(self, discord_id):
        query = (
            'SELECT handle '
            'FROM user_data '
            'WHERE discord_id = ?'
        )
        res = self.conn.execute(query, (discord_id, )).fetchone()
        return res[0] if res else None
    
    
    
    #for local debug
    def get_data(self, table, limit = 10):
        query = (
            'SELECT * '
            'FROM {0} '.format(table)
        )
        if limit is not None:
            query +=  'LIMIT {0}'.format(limit)
        x = self.conn.execute(query).fetchall()
        return x

