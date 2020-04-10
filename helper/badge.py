from collections import namedtuple
Rank = namedtuple('Rank', 'low high title title_abbr color_graph color_embed')
MAX_SCORE = None
# % max_score
RATED_RANKS = [
    Rank(-10 ** 9, 0.25, 'Newbie', 'N', '#CCCCCC', 0x808080),
    Rank(0.25, 1, 'Pupil', 'P', '#77FF77', 0x008000),
    Rank(1, 2, 'Specialist', 'S', '#77DDBB', 0x03a89e),
    Rank(2, 5, 'Expert', 'E', '#AAAAFF', 0x0000ff),
    Rank(5, 10, 'Candidate Master', 'CM', '#FF88FF', 0xaa00aa),
    Rank(10, 15, 'Master', 'M', '#FFCC88', 0xff8c00),
    Rank(15, 30, 'International Master', 'IM', '#FFBB55', 0xf57500),
    Rank(30, 45, 'Grandmaster', 'GM', '#FF7777', 0xff3030),
    Rank(45, 60, 'International Grandmaster', 'IGM', '#FF3333', 0xff0000),
    Rank(60, 90, 'Legendary Grandmaster', 'LGM', '#AA0000', 0xcc0000),
    Rank(90, 10 ** 9, 'Cá nóc', 'CNCC', '#854442', 0xcc0000)
]
UNRATED_RANK = Rank(None, None, 'Unrated', None, None, None)

def point2rank(point, MAX_SCORE=100):
    if point is None:
        return UNRATED_RANK
    for rank in RATED_RANKS:
        if rank.low * MAX_SCORE / 100 <= point < rank.high * MAX_SCORE / 100:
            return rank