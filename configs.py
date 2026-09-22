import pygame

# ================= 配置与常量 =================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60
GRID_SIZE = 80
SAVE_FILE = "save_data.json"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)

DIR_MAP = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}

# ================= 关卡设计 =================
LEVELS = [
    {"grid": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 4, 2, 0], [0, 0, 2, 0]], "mistakes": 3, "target_time": 30},
    {"grid": [[0, 1, 0, 2], [4, 4, 1, 0], [0, 1, 0, 0], [0, 3, 1, 2]], "mistakes": 4, "target_time": 45},
    {"grid": [[1, 2, 3, 4], [3, 2, 1, 1], [1, 3, 4, 4], [4, 2, 1, 1]], "mistakes": 5, "target_time": 50},
    {"grid": [[1, 1, 3, 3], [4, 1, 1, 4], [3, 4, 1, 4], [1, 1, 1, 1]], "mistakes": 3, "target_time": 45},
    {"grid": [[0, 1, 1, 1, 0], [3, 4, 1, 4, 4], [3, 3, 1, 2, 4], [3, 1, 3, 2, 4], [0, 2, 2, 2, 0]], "mistakes": 5,
     "target_time": 60}
]


# ================= 智能字体匹配 =================
def get_chinese_font(size):
    candidates = ["microsoftyahei", "simhei", "pingfangsc", "pingfang", "heiti", "stheitiregular", "arialunicodems",
                  "droidsansfallback", "songti", "stsong", "nsimsun", "simsun", "hiraginosansgb"]
    try:
        pygame.font.init()
        available_fonts = pygame.font.get_fonts()
        for name in candidates:
            if name in available_fonts: return pygame.font.SysFont(name, size)
        for name in available_fonts:
            if any(keyword in name for keyword in ["hei", "yahei", "pingfang", "song", "cjk", "fallback"]):
                return pygame.font.SysFont(name, size)
    except:
        pass
    return pygame.font.SysFont(None, size)

