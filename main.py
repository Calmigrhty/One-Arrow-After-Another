import pygame
import sys
import math
import random
import json
import os

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


# ================= 箭头类 =================
class Arrow:
    def __init__(self, r, c, dir_type):
        self.r, self.c = r, c
        self.dir_type = dir_type
        self.x, self.y = c * GRID_SIZE, r * GRID_SIZE
        self.state = "idle"
        self.shake_timer = 0
        self.speed = 20
        self.is_dead = False
        self.is_hinted = False
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

    def update(self):
        if self.state == "flying":
            dr, dc = DIR_MAP[self.dir_type]
            self.x += dc * self.speed
            self.y += dr * self.speed
            if abs(self.x) > SCREEN_WIDTH or abs(self.y) > SCREEN_HEIGHT:
                self.is_dead = True
        elif self.state == "shaking":
            self.shake_timer -= 1
            if self.shake_timer <= 0: self.state = "idle"

    def draw(self, surface, offset_x, offset_y):
        if self.is_dead: return
        draw_x, draw_y = offset_x + self.x, offset_y + self.y

        if self.state == "shaking":
            shake_amt = math.sin(self.shake_timer) * 5
            if self.dir_type in [1, 2]:
                draw_x += shake_amt
            else:
                draw_y += shake_amt

        if self.is_hinted:
            pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
            glow_color = (255, int(200 + 55 * pulse), 0)
            glow_rect = pygame.Rect(draw_x + 2, draw_y + 2, GRID_SIZE - 4, GRID_SIZE - 4)
            pygame.draw.rect(surface, glow_color, glow_rect, width=4, border_radius=12)

        cx, cy = draw_x + GRID_SIZE // 2, draw_y + GRID_SIZE // 2
        shaft_len, shaft_thick, head_len, head_wide, neck = 16, 6, 18, 15, 4

        if self.dir_type == 1:
            pts = [(cx - shaft_thick, cy + shaft_len), (cx - shaft_thick, cy - neck), (cx - head_wide, cy - neck),
                   (cx, cy - head_len), (cx + head_wide, cy - neck), (cx + shaft_thick, cy - neck),
                   (cx + shaft_thick, cy + shaft_len)]
        elif self.dir_type == 2:
            pts = [(cx - shaft_thick, cy - shaft_len), (cx - shaft_thick, cy + neck), (cx - head_wide, cy + neck),
                   (cx, cy + head_len), (cx + head_wide, cy + neck), (cx + shaft_thick, cy + neck),
                   (cx + shaft_thick, cy - shaft_len)]
        elif self.dir_type == 3:
            pts = [(cx + shaft_len, cy - shaft_thick), (cx - neck, cy - shaft_thick), (cx - neck, cy - head_wide),
                   (cx - head_len, cy), (cx - neck, cy + head_wide), (cx - neck, cy + shaft_thick),
                   (cx + shaft_len, cy + shaft_thick)]
        elif self.dir_type == 4:
            pts = [(cx - shaft_len, cy - shaft_thick), (cx + neck, cy - shaft_thick), (cx + neck, cy - head_wide),
                   (cx + head_len, cy), (cx + neck, cy + head_wide), (cx + neck, cy + shaft_thick),
                   (cx - shaft_len, cy + shaft_thick)]

        pygame.draw.polygon(surface, self.color, pts)


# ================= 游戏主控制类 =================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("一箭又一箭 - 完整版")
        self.clock = pygame.time.Clock()

        self.font_title = get_chinese_font(60)
        self.font_large = get_chinese_font(40)
        self.font_normal = get_chinese_font(20)

        self.themes = [
            {"top": (30, 35, 50), "bottom": (15, 18, 25), "dot": (45, 50, 70)},
            {"top": (25, 45, 35), "bottom": (10, 20, 15), "dot": (40, 65, 50)},
            {"top": (50, 30, 40), "bottom": (25, 10, 15), "dot": (70, 45, 55)},
            {"top": (45, 25, 25), "bottom": (20, 10, 10), "dot": (65, 40, 40)}
        ]

        self.state = "START"
        self.current_level = 0
        self.bg_surface = self.create_background(self.themes[0])

        self.level_start_time = 0
        self.has_started_moving = False
        self.final_time = 0
        self.earned_stars = 0
        self.history = []

        self.is_auto_playing = False
        self.used_ai = False
        self.auto_path = []
        self.last_auto_move_time = 0
        self.no_solution_msg_timer = 0

        self.random_level_data = None
        self.random_theme_idx = 0

        self.level_records = [{'stars': 0, 'time': 999} for _ in range(len(LEVELS))]
        self.saved_progress = None
        self.load_records()

    def load_records(self):
        self.saved_progress = None
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        records = data.get("records", [])
                        for i in range(min(len(self.level_records), len(records))):
                            self.level_records[i] = records[i]
                        self.saved_progress = data.get("progress")
                    elif isinstance(data, list):
                        for i in range(min(len(self.level_records), len(data))):
                            self.level_records[i] = data[i]
            except:
                pass

    def save_all_data(self):
        progress = None
        if self.state == "PLAYING" and self.current_level != "RANDOM":
            elapsed = (pygame.time.get_ticks() - self.level_start_time) // 1000 if self.has_started_moving else 0
            progress = {
                "level": self.current_level,
                "mistakes": self.mistakes,
                "elapsed_time": elapsed,
                "has_started_moving": self.has_started_moving,
                "used_ai": self.used_ai,
                "grid": self.grid,
                "arrows": [{"r": a.r, "c": a.c, "dir_type": a.dir_type, "color": list(a.color)} for a in self.arrows if
                           not a.is_dead],
                "history": self.history
            }

        data = {"records": self.level_records, "progress": progress}
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def resume_progress(self):
        try:
            p = self.saved_progress
            self.current_level = p["level"]
            theme_idx = self.current_level % len(self.themes)
            self.bg_surface = self.create_background(self.themes[theme_idx])

            lvl = LEVELS[self.current_level]
            self.rows, self.cols = len(lvl["grid"]), len(lvl["grid"][0])
            self.max_mistakes = lvl["mistakes"]
            self.target_time = lvl["target_time"]
            self.offset_x = (SCREEN_WIDTH - self.cols * GRID_SIZE) // 2
            self.offset_y = (SCREEN_HEIGHT - self.rows * GRID_SIZE) // 2 + 50

            self.grid = p["grid"]
            self.mistakes = p["mistakes"]
            self.history = p["history"]
            self.has_started_moving = p["has_started_moving"]
            self.used_ai = p.get("used_ai", False)

            if self.has_started_moving:
                self.level_start_time = pygame.time.get_ticks() - p["elapsed_time"] * 1000
            else:
                self.level_start_time = 0

            self.arrows = []
            for a_data in p["arrows"]:
                arr = Arrow(a_data["r"], a_data["c"], a_data["dir_type"])
                arr.color = tuple(a_data["color"])
                self.arrows.append(arr)

            self.state = "PLAYING"
            self.is_auto_playing = False
            self.auto_path = []
        except:
            self.state = "LEVEL_SELECT"
        self.saved_progress = None

    def create_background(self, theme):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        top_color, bottom_color = theme["top"], theme["bottom"]
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        for x in range(0, SCREEN_WIDTH, 40):
            for y in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.circle(bg, theme["dot"], (x, y), 2)
        return bg

    def setup_level_from_data(self, level_data, theme_idx):
        self.bg_surface = self.create_background(self.themes[theme_idx])
        self.rows, self.cols = len(level_data["grid"]), len(level_data["grid"][0])
        self.mistakes, self.max_mistakes = level_data["mistakes"], level_data["mistakes"]
        self.target_time = level_data["target_time"]

        self.offset_x = (SCREEN_WIDTH - self.cols * GRID_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - self.rows * GRID_SIZE) // 2 + 50

        self.grid = [[level_data["grid"][r][c] for c in range(self.cols)] for r in range(self.rows)]
        self.arrows = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != 0: self.arrows.append(Arrow(r, c, self.grid[r][c]))

        self.level_start_time = 0
        self.has_started_moving = False
        self.history = []
        self.is_auto_playing = False
        self.used_ai = False
        self.auto_path = []
        self.no_solution_msg_timer = 0

    def load_level(self, level_idx):
        if level_idx >= len(LEVELS): return
        self.current_level = level_idx
        self.setup_level_from_data(LEVELS[level_idx], level_idx % len(self.themes))

    def init_new_random_level(self):
        self.current_level = "RANDOM"
        rows = random.randint(4, 5)
        cols = random.randint(5, 6)
        difficulty = random.randint(10, rows * cols - 5)

        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        placed = 0

        while placed < difficulty:
            valid_slots = []
            for r in range(rows):
                for c in range(cols):
                    if grid[r][c] == 0:
                        for d in [1, 2, 3, 4]:
                            if self.check_path_clear(r, c, d, grid, rows, cols):
                                valid_slots.append((r, c, d))
            if not valid_slots: break

            r, c, d = random.choice(valid_slots)
            grid[r][c] = d
            placed += 1

        self.random_level_data = {
            "grid": grid,
            "mistakes": max(3, placed // 5),
            "target_time": placed * 2
        }
        self.random_theme_idx = random.randint(0, len(self.themes) - 1)
        self.setup_level_from_data(self.random_level_data, self.random_theme_idx)

    def check_path_clear(self, r, c, dir_type, custom_grid=None, r_max=None, c_max=None):
        grid = custom_grid if custom_grid else self.grid
        rows = r_max if r_max else self.rows
        cols = c_max if c_max else self.cols
        dr, dc = DIR_MAP[dir_type]
        curr_r, curr_c = r + dr, c + dc
        while 0 <= curr_r < rows and 0 <= curr_c < cols:
            if grid[curr_r][curr_c] != 0: return False
            curr_r += dr
            curr_c += dc
        return True

    def calculate_stars(self):
        stars = 3
        mistakes_made = self.max_mistakes - self.mistakes
        if mistakes_made > 1: stars -= 1
        if self.final_time > self.target_time: stars -= 1
        self.earned_stars = max(1, stars)

    def get_solution(self):
        temp_grid = [[self.grid[r][c] for c in range(self.cols)] for r in range(self.rows)]

        def dfs(grid, path):
            arrows = [(r, c, grid[r][c]) for r in range(self.rows) for c in range(self.cols) if grid[r][c] != 0]
            if not arrows: return path
            valid_moves = [(r, c, d) for (r, c, d) in arrows if self.check_path_clear(r, c, d, grid)]
            if not valid_moves: return None
            for r, c, d in valid_moves:
                grid[r][c] = 0
                res = dfs(grid, path + [(r, c)])
                if res: return res
                grid[r][c] = d
            return None

        return dfs(temp_grid, [])

    def start_ai_solver(self):
        if self.is_auto_playing: return
        self.used_ai = True
        solution = self.get_solution()
        if solution:
            self.auto_path = solution
            self.is_auto_playing = True
            self.last_auto_move_time = pygame.time.get_ticks()
            for a in self.arrows: a.is_hinted = False
        else:
            self.no_solution_msg_timer = pygame.time.get_ticks() + 3000

    def trigger_hint(self):
        valid_arrows = [a for a in self.arrows if a.state == "idle" and self.check_path_clear(a.r, a.c, a.dir_type)]
        if valid_arrows:
            hint_arrow = random.choice(valid_arrows)
            hint_arrow.is_hinted = True

    def save_history(self):
        state = {
            "mistakes": self.mistakes,
            "grid": [[self.grid[r][c] for c in range(self.cols)] for r in range(self.rows)],
            "arrows": []
        }
        for a in self.arrows:
            state["arrows"].append({
                "r": a.r, "c": a.c, "dir_type": a.dir_type, "x": a.x, "y": a.y,
                "state": a.state, "is_dead": a.is_dead, "color": list(a.color), "is_hinted": a.is_hinted
            })
        self.history.append(state)

    def undo(self):
        if not self.history: return
        last_state = self.history.pop()
        self.is_auto_playing = False
        self.no_solution_msg_timer = 0

        self.mistakes = last_state["mistakes"]
        self.grid = [[last_state["grid"][r][c] for c in range(self.cols)] for r in range(self.rows)]

        self.arrows = []
        for a_data in last_state["arrows"]:
            new_arrow = Arrow(a_data["r"], a_data["c"], a_data["dir_type"])
            new_arrow.x, new_arrow.y = a_data["x"], a_data["y"]
            new_arrow.state, new_arrow.is_dead = a_data["state"], a_data["is_dead"]
            new_arrow.color, new_arrow.is_hinted = tuple(a_data["color"]), a_data["is_hinted"]
            self.arrows.append(new_arrow)

        if len(self.history) == 0:
            self.has_started_moving = False
            self.level_start_time = 0

    def trigger_arrow(self, grid_r, grid_c):
        for a in self.arrows: a.is_hinted = False
        for arrow in self.arrows:
            if arrow.r == grid_r and arrow.c == grid_c and arrow.state == "idle":
                self.save_history()
                if not self.has_started_moving:
                    self.has_started_moving = True
                    self.level_start_time = pygame.time.get_ticks()

                if self.check_path_clear(grid_r, grid_c, arrow.dir_type):
                    arrow.state = "flying"
                    self.grid[grid_r][grid_c] = 0
                else:
                    arrow.state = "shaking"
                    arrow.shake_timer = 20
                    self.mistakes -= 1
                    self.is_auto_playing = False
                    if self.mistakes <= 0: self.state = "GAME_OVER"
                break

    def handle_level_select_click(self, pos):
        btn_w, btn_h, spacing_x, spacing_y, cols = 100, 100, 50, 70, 3
        start_x = (SCREEN_WIDTH - (cols * btn_w + (cols - 1) * spacing_x)) // 2
        start_y = 160

        for i in range(len(LEVELS)):
            row, col = i // cols, i % cols
            bx = start_x + col * (btn_w + spacing_x)
            by = start_y + row * (btn_h + spacing_y)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            if rect.collidepoint(pos):
                self.load_level(i)
                self.state = "PLAYING"
                return

        btn_rand_w, btn_rand_h = 250, 60
        btn_rand = pygame.Rect((SCREEN_WIDTH - btn_rand_w) // 2, 530, btn_rand_w, btn_rand_h)
        if btn_rand.collidepoint(pos):
            self.init_new_random_level()
            self.state = "PLAYING"

    def handle_playing_click(self, pos):
        if self.is_auto_playing:
            self.is_auto_playing = False
            return

        btn_w = 55
        btn_ai = pygame.Rect(SCREEN_WIDTH - 75, 20, btn_w, 40)
        btn_hint = pygame.Rect(SCREEN_WIDTH - 145, 20, btn_w, 40)
        btn_undo = pygame.Rect(SCREEN_WIDTH - 215, 20, btn_w, 40)
        btn_restart = pygame.Rect(SCREEN_WIDTH - 285, 20, btn_w, 40)
        btn_menu = pygame.Rect(SCREEN_WIDTH - 355, 20, btn_w, 40)

        if btn_ai.collidepoint(pos): self.start_ai_solver(); return
        if btn_hint.collidepoint(pos): self.trigger_hint(); return
        if btn_undo.collidepoint(pos): self.undo(); return
        if btn_menu.collidepoint(pos):
            # 点菜单返回大厅前，先自动保存当前进度
            self.save_all_data()
            self.state = "LEVEL_SELECT"
            self.load_records()  # 刷新存档状态
            self.bg_surface = self.create_background(self.themes[0])
            return

        if btn_restart.collidepoint(pos):
            if self.current_level == "RANDOM":
                self.setup_level_from_data(self.random_level_data, self.random_theme_idx)
            else:
                self.load_level(self.current_level)
            return

        mx, my = pos
        grid_c, grid_r = int((mx - self.offset_x) // GRID_SIZE), int((my - self.offset_y) // GRID_SIZE)
        if 0 <= grid_r < self.rows and 0 <= grid_c < self.cols:
            if self.grid[grid_r][grid_c] != 0:
                self.trigger_arrow(grid_r, grid_c)

    def draw_text(self, text, font, color, x, y, align="center", shadow=True):
        if shadow:
            try:
                shadow_surf = font.render(text, True, (10, 10, 15))
                s_rect = shadow_surf.get_rect()
                if align == "center":
                    s_rect.center = (x + 2, y + 3)
                elif align == "topleft":
                    s_rect.topleft = (x + 2, y + 3)
                self.screen.blit(shadow_surf, s_rect)
            except:
                pass
        try:
            surface = font.render(text, True, color)
        except:
            surface = pygame.font.Font(None, 24).render("TEXT ERROR", True, color)
        rect = surface.get_rect()
        if align == "center":
            rect.center = (x, y)
        elif align == "topleft":
            rect.topleft = (x, y)
        self.screen.blit(surface, rect)

    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))

        if self.state == "START":
            self.draw_text("一箭又一箭", self.font_title, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 30)

            if self.saved_progress:
                btn_resume = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20, 160, 50)
                pygame.draw.rect(self.screen, (70, 130, 180), btn_resume, border_radius=25)
                pygame.draw.rect(self.screen, WHITE, btn_resume, width=2, border_radius=25)
                # 使用 font_normal 正常字号，彻底解决撑破格子的问题
                self.draw_text("继续游戏", self.font_normal, WHITE, btn_resume.centerx, btn_resume.centery,
                               shadow=False)

                btn_new = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 60, 160, 50)
                pygame.draw.rect(self.screen, (200, 80, 80), btn_new, border_radius=25)
                pygame.draw.rect(self.screen, WHITE, btn_new, width=2, border_radius=25)
                self.draw_text("重新开始", self.font_normal, WHITE, btn_new.centerx, btn_new.centery, shadow=False)
            else:
                self.draw_text("点击屏幕开始", self.font_large, GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)

        elif self.state == "LEVEL_SELECT":
            self.draw_text("选择关卡", self.font_title, WHITE, SCREEN_WIDTH // 2, 80)
            btn_w, btn_h, spacing_x, spacing_y, cols = 100, 100, 50, 70, 3
            start_x = (SCREEN_WIDTH - (cols * btn_w + (cols - 1) * spacing_x)) // 2
            start_y = 160
            mx, my = pygame.mouse.get_pos()

            for i in range(len(LEVELS)):
                row, col = i // cols, i % cols
                bx, by = start_x + col * (btn_w + spacing_x), start_y + row * (btn_h + spacing_y)
                rect = pygame.Rect(bx, by, btn_w, btn_h)

                bg_color = (100, 160, 210) if rect.collidepoint((mx, my)) else (70, 130, 180)
                pygame.draw.rect(self.screen, bg_color, rect, border_radius=20)
                pygame.draw.rect(self.screen, WHITE, rect, width=3, border_radius=20)
                self.draw_text(f"{i + 1}", self.font_title, WHITE, rect.centerx, rect.centery, shadow=False)

                record = self.level_records[i]
                if record['stars'] > 0:
                    stars_str = "★" * record['stars'] + "☆" * (3 - record['stars'])
                    self.draw_text(stars_str, self.font_normal, (255, 215, 0), rect.centerx, rect.bottom + 15)
                    self.draw_text(f"{record['time']}s", self.font_normal, (200, 255, 200), rect.centerx,
                                   rect.bottom + 40)
                else:
                    self.draw_text("未通关", self.font_normal, GRAY, rect.centerx, rect.bottom + 25)

            btn_rand_w, btn_rand_h = 250, 60
            btn_rand = pygame.Rect((SCREEN_WIDTH - btn_rand_w) // 2, 530, btn_rand_w, btn_rand_h)
            rand_color = (255, 120, 120) if btn_rand.collidepoint((mx, my)) else (200, 80, 80)
            pygame.draw.rect(self.screen, rand_color, btn_rand, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, btn_rand, width=3, border_radius=20)
            self.draw_text("无限随机模式", self.font_large, WHITE, btn_rand.centerx, btn_rand.centery, shadow=False)

        elif self.state == "PLAYING":
            current_time = (pygame.time.get_ticks() - self.level_start_time) // 1000 if self.has_started_moving else 0

            lvl_text = "无限随机模式" if self.current_level == "RANDOM" else f"关卡: {self.current_level + 1}"
            self.draw_text(lvl_text, self.font_normal, WHITE, 20, 20, "topleft")

            remain = sum(1 for row in self.grid for val in row if val != 0)
            self.draw_text(f"剩余: {remain}", self.font_normal, WHITE, 20, 50, "topleft")
            color = (255, 100, 100) if self.mistakes <= 1 else WHITE
            self.draw_text(f"失误: {self.mistakes}", self.font_normal, color, 20, 80, "topleft")
            time_color = (255, 150, 150) if current_time > self.target_time else (150, 255, 150)
            self.draw_text(f"用时: {current_time}s / {self.target_time}s", self.font_normal, time_color, 20, 110,
                           "topleft")

            if self.is_auto_playing:
                self.draw_text("AI 正在自动解局...", self.font_large, (100, 255, 100), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT - 60)
            if pygame.time.get_ticks() < self.no_solution_msg_timer:
                self.draw_text("当前死锁无解，请撤销！", self.font_large, (255, 80, 80), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT - 60)

            btn_w = 55
            btn_ai = pygame.Rect(SCREEN_WIDTH - 75, 20, btn_w, 40)
            btn_hint = pygame.Rect(SCREEN_WIDTH - 145, 20, btn_w, 40)
            btn_undo = pygame.Rect(SCREEN_WIDTH - 215, 20, btn_w, 40)
            btn_restart = pygame.Rect(SCREEN_WIDTH - 285, 20, btn_w, 40)
            btn_menu = pygame.Rect(SCREEN_WIDTH - 355, 20, btn_w, 40)

            pygame.draw.rect(self.screen, (200, 100, 100) if self.is_auto_playing else (120, 80, 180), btn_ai,
                             border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_ai, width=2, border_radius=15)
            self.draw_text("求解", self.font_normal, WHITE, btn_ai.centerx, btn_ai.centery, shadow=False)

            pygame.draw.rect(self.screen, (70, 130, 180), btn_hint, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_hint, width=2, border_radius=15)
            self.draw_text("提示", self.font_normal, WHITE, btn_hint.centerx, btn_hint.centery, shadow=False)

            undo_color = (70, 130, 180) if self.history else (100, 100, 100)
            pygame.draw.rect(self.screen, undo_color, btn_undo, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_undo, width=2, border_radius=15)
            self.draw_text("撤销", self.font_normal, WHITE if self.history else GRAY, btn_undo.centerx,
                           btn_undo.centery, shadow=False)

            pygame.draw.rect(self.screen, (70, 130, 180), btn_restart, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_restart, width=2, border_radius=15)
            self.draw_text("重试", self.font_normal, WHITE, btn_restart.centerx, btn_restart.centery, shadow=False)

            pygame.draw.rect(self.screen, (100, 100, 120), btn_menu, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_menu, width=2, border_radius=15)
            self.draw_text("菜单", self.font_normal, WHITE, btn_menu.centerx, btn_menu.centery, shadow=False)

            board_rect = pygame.Rect(self.offset_x - 10, self.offset_y - 10, self.cols * GRID_SIZE + 20,
                                     self.rows * GRID_SIZE + 20)
            pygame.draw.rect(self.screen, (20, 25, 35), board_rect, border_radius=15)
            pygame.draw.rect(self.screen, (50, 60, 80), board_rect, width=2, border_radius=15)

            for r in range(self.rows):
                for c in range(self.cols):
                    rect = pygame.Rect(self.offset_x + c * GRID_SIZE + 5, self.offset_y + r * GRID_SIZE + 5,
                                       GRID_SIZE - 10, GRID_SIZE - 10)
                    pygame.draw.rect(self.screen, (30, 35, 45), rect, border_radius=10)

            for arrow in self.arrows: arrow.draw(self.screen, self.offset_x, self.offset_y)

        elif self.state in ["LEVEL_CLEAR", "GAME_OVER", "GAME_WON"]:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            if self.state == "LEVEL_CLEAR":
                self.draw_text("关卡完成！", self.font_title, (100, 255, 100), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 3 - 40)
                stars_str = "★" * self.earned_stars + "☆" * (3 - self.earned_stars)
                self.draw_text(f"本次评分: {stars_str}", self.font_large, (255, 215, 0), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 2 - 30)
                self.draw_text(f"本次用时: {self.final_time}秒", self.font_normal, WHITE, SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 2 + 10)

                if self.current_level == "RANDOM":
                    self.draw_text("点击屏幕生成新关卡", self.font_large, WHITE, SCREEN_WIDTH // 2,
                                   SCREEN_HEIGHT // 2 + 90)
                    self.draw_text("返回大厅请点击左上角", self.font_normal, GRAY, SCREEN_WIDTH // 2,
                                   SCREEN_HEIGHT // 2 + 130)
                else:
                    record = self.level_records[self.current_level]
                    best_stars = "★" * record['stars'] + "☆" * (3 - record['stars'])
                    if self.used_ai:
                        self.draw_text("使用了 AI 求解，不计入记录", self.font_normal, (255, 150, 150),
                                       SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
                    else:
                        self.draw_text(f"历史最佳: {best_stars}   最快: {record['time']}秒", self.font_normal,
                                       (200, 255, 200), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
                    self.draw_text("点击屏幕进入下一关", self.font_large, WHITE, SCREEN_WIDTH // 2,
                                   SCREEN_HEIGHT // 2 + 110)

            elif self.state == "GAME_OVER":
                self.draw_text("游戏失败", self.font_title, (255, 80, 80), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("点击屏幕重新挑战本关", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

            elif self.state == "GAME_WON":
                self.draw_text("恭喜！全部通关！", self.font_title, (100, 200, 255), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 3 - 40)
                stars_str = "★" * self.earned_stars + "☆" * (3 - self.earned_stars)
                self.draw_text(f"本次评分: {stars_str}", self.font_large, (255, 215, 0), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 2 - 30)
                self.draw_text(f"本次用时: {self.final_time}秒", self.font_normal, WHITE, SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 2 + 10)
                self.draw_text("点击返回关卡选择", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110)

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_all_data()
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.state == "PLAYING":
                        if event.key == pygame.K_z:
                            self.undo()
                        elif event.key == pygame.K_h:
                            self.trigger_hint()
                        elif event.key == pygame.K_a:
                            self.start_ai_solver()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "START":
                        if self.saved_progress:
                            btn_resume = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20, 160, 50)
                            btn_new = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 60, 160, 50)
                            if btn_resume.collidepoint(event.pos):
                                self.resume_progress()
                            elif btn_new.collidepoint(event.pos):
                                self.saved_progress = None
                                self.state = "LEVEL_SELECT"
                        else:
                            self.state = "LEVEL_SELECT"
                    elif self.state == "LEVEL_SELECT":
                        self.handle_level_select_click(event.pos)
                    elif self.state == "PLAYING":
                        self.handle_playing_click(event.pos)
                    elif self.state == "LEVEL_CLEAR":
                        if self.current_level == "RANDOM":
                            if event.pos[0] < 150 and event.pos[1] < 150:
                                self.state = "LEVEL_SELECT"
                                self.bg_surface = self.create_background(self.themes[0])
                            else:
                                self.init_new_random_level()
                                self.state = "PLAYING"
                        else:
                            self.current_level += 1
                            self.load_level(self.current_level)
                            if self.state != "GAME_WON": self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        if self.current_level == "RANDOM":
                            self.setup_level_from_data(self.random_level_data, self.random_theme_idx)
                        else:
                            self.load_level(self.current_level)
                        self.state = "PLAYING"
                    elif self.state == "GAME_WON":
                        self.state = "LEVEL_SELECT"
                        self.bg_surface = self.create_background(self.themes[0])

            if self.state == "PLAYING":
                if self.is_auto_playing and self.auto_path:
                    is_animating = any(a.state != "idle" for a in self.arrows)
                    if not is_animating:
                        current_ticks = pygame.time.get_ticks()
                        if current_ticks - self.last_auto_move_time > 200:
                            next_r, next_c = self.auto_path.pop(0)
                            self.trigger_arrow(next_r, next_c)
                            self.last_auto_move_time = current_ticks

                for arrow in self.arrows: arrow.update()
                self.arrows = [a for a in self.arrows if not a.is_dead]
                remain = sum(1 for row in self.grid for val in row if val != 0)

                if remain == 0 and len(self.arrows) == 0:
                    self.final_time = (
                                                  pygame.time.get_ticks() - self.level_start_time) // 1000 if self.has_started_moving else 0
                    self.calculate_stars()

                    if self.current_level != "RANDOM" and not self.used_ai:
                        record = self.level_records[self.current_level]
                        if self.earned_stars > record['stars']:
                            record['stars'] = self.earned_stars
                            record['time'] = self.final_time
                            self.save_all_data()
                        elif self.earned_stars == record['stars'] and self.final_time < record['time']:
                            record['time'] = self.final_time
                            self.save_all_data()

                    if self.current_level != "RANDOM" and self.current_level >= len(LEVELS) - 1:
                        self.state = "GAME_WON"
                    else:
                        self.state = "LEVEL_CLEAR"

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()