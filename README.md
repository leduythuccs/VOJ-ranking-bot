# VOJ-ranking-bot
 A discord bot which helps calculate ranking in a Codeforces group

## Features
### Ranking
- Create group ranking 
- Show plot about ranking
### Other
- For VNOI: get codeforces link of a [VOJ](http://vn.spoj.com/) problem 
- Some git commands to update the bot.
- Some commands about nCoVi virus.

## Installation
Clone this repository 
- `python pip install -r requirements`
- Base on file `.env-example`, create file `.env` and fill all the data: bot token, account account codeforces (for crawling submission), ...

## How to use
- Create a discord bot, add it to your discord server.
- Then use `python main.py` to run the bot. Remember to edit data in `.env`.
- Use `;voj help` to see list command

## About database
- I wrote a crawler to crawl all submission in a codeforces group, and then store all the data in file file [ranking.db](/database/ranking.db) by using SQLite3. 

- There is 3 table in that file:
    - `problem_info`, 4 columns:
        - `id`: id of a problem
        - `problem_name`: name of problem
        - `links` (TEXT): short codeforces links to problem, if a problem has more than 1 links, its links is separate with commas (i.e `274863/A`, `274863/F,272622/A`)
        - `cnt_AC`: number of user that got Accepted this problem.
    - `solved_info`. If a user submit to a problem then I will create a record has 4 columns: 
        - `user_id`: id of user, I cannot use user's handle here since users can change their handles.
        - `problem_id`: id of a problem (equal to `id` in `problem_info`)
        - `result`: result of the submission. 'AC' is accepted, or a float number equal to partial score of that submission.
        - `date`: submission time in format `YYYY/MM/DD`.
    - `user_data`, 3 columns:
        - `CF_id`: id of a user (equal to `user_id` in `problem_info`)
        - `handle`: handle of a user.
        - `discord_id`: discord id.
    
### Issues:
- What if a user change their handle?
- What if we rejudge a problem?
- What if we rename a problem? 

## Q&A
- Question: How rank is calculated? Answer: Each problem has a point, equal to `80 / (40 + x)` with `x` is number of users got accepted in that problem (`cnt_AC` in table `problem_info`). If a user submit to a problem and receive a accepted verdict, they will earn all the problem's point. If they receive a partial score, they will earn `partial_score` * `problem_point` / 100 points.
## Note
- There is some commands required `Admin` role. If you're not bot's owner, you will need `Admin` role to use those commands.
- You can update the bot (get new commit from this repository) by using `;rebuild git_pull` command. Then you can use `;rebuild restart` to restart the bot (you don't need to run it again, it's very useful since I'm running the bot in a VPS).
