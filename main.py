import pygame
import sys
import math
import random

# ================= 配置与常量 =================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60
GRID_SIZE = 80  # 棋盘格大小

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)

# 方向映射 (行偏移, 列偏移)
DIR_MAP = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}

# ================= 关卡设计 =================
LEVELS = [
    {  # 关卡 1: 最基础的消除
        "grid": [
            [0, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 4, 2, 0],
            [0, 0, 2, 0]
        ],
        "mistakes": 3
    },
    {  # 关卡 2: 存在互相阻挡
        "grid": [
            [0, 1, 0, 2],
            [4, 4, 1, 0],
            [0, 1, 0, 0],
            [0, 3, 1, 2]
        ],
        "mistakes": 4
    },
    {  # 关卡 3: 密集阵型
        "grid": [
            [1, 2, 3, 4],
            [3, 2, 1, 1],
            [1, 3, 4, 4],
            [4, 2, 1, 1]
        ],
        "mistakes": 5
    },
    {
        "grid": [
            [1, 1, 3, 3],
            [4, 1, 1, 4],
            [3, 4, 1, 4],
            [1, 1, 1, 1]
        ],
        "mistakes": 3,
        "target_time": 15
    },
    {
        "grid": [
            [0, 1, 1, 1, 0],
            [3, 4, 1, 4, 4],
            [3, 3, 1, 2, 4],
            [3, 1, 3, 2, 4],
            [0, 2, 2, 2, 0]
        ],
        "mistakes": 5,
        "target_time": 25
    }
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
        pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()

        self.font_title = get_chinese_font(60)
        self.font_large = get_chinese_font(40)
        self.font_normal = get_chinese_font(20)

        self.themes = [
            {"top": (30, 35, 50), "bottom": (15, 18, 25), "dot": (45, 50, 70)},
            {"top": (25, 45, 35), "bottom": (10, 20, 15), "dot": (40, 65, 50)},
            {"top": (50, 30, 40), "bottom": (25, 10, 15), "dot": (70, 45, 55)},
        ]

        self.state = "START"
        self.current_level = 0
        self.bg_surface = self.create_background(self.themes[0])

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

    def load_level(self, level_idx):
        if level_idx >= len(LEVELS): return

        theme_idx = level_idx % len(self.themes)
        self.bg_surface = self.create_background(self.themes[theme_idx])

        level_data = LEVELS[level_idx]
        grid_data = level_data["grid"]
        self.rows, self.cols = len(grid_data), len(grid_data[0])
        self.mistakes = level_data["mistakes"]

        self.offset_x = (SCREEN_WIDTH - self.cols * GRID_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - self.rows * GRID_SIZE) // 2 + 50

        self.grid = [[grid_data[r][c] for c in range(self.cols)] for r in range(self.rows)]
        self.arrows = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != 0: self.arrows.append(Arrow(r, c, self.grid[r][c]))

    def check_path_clear(self, r, c, dir_type):
        dr, dc = DIR_MAP[dir_type]
        curr_r, curr_c = r + dr, c + dc
        while 0 <= curr_r < self.rows and 0 <= curr_c < self.cols:
            if self.grid[curr_r][curr_c] != 0: return False
            curr_r += dr
            curr_c += dc
        return True

    def handle_level_select_click(self, pos):
        """处理关卡选择界面的点击"""
        btn_w, btn_h = 100, 100
        spacing_x, spacing_y = 40, 40
        cols = 3
        start_x = (SCREEN_WIDTH - (cols * btn_w + (cols - 1) * spacing_x)) // 2
        start_y = 200

        for i in range(len(LEVELS)):
            row, col = i // cols, i % cols
            bx = start_x + col * (btn_w + spacing_x)
            by = start_y + row * (btn_h + spacing_y)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            if rect.collidepoint(pos):
                self.current_level = i
                self.load_level(self.current_level)
                self.state = "PLAYING"
                return

    def handle_playing_click(self, pos):
        """处理游戏界面的点击 (含返回菜单和重新开始)"""
        btn_restart = pygame.Rect(SCREEN_WIDTH - 110, 20, 90, 40)
        btn_menu = pygame.Rect(SCREEN_WIDTH - 210, 20, 90, 40)

        if btn_restart.collidepoint(pos):
            self.load_level(self.current_level)
            return
        if btn_menu.collidepoint(pos):
            self.state = "LEVEL_SELECT"
            self.bg_surface = self.create_background(self.themes[0])  # 菜单页恢复默认背景
            return

        mx, my = pos
        grid_c, grid_r = int((mx - self.offset_x) // GRID_SIZE), int((my - self.offset_y) // GRID_SIZE)

        if 0 <= grid_r < self.rows and 0 <= grid_c < self.cols:
            if self.grid[grid_r][grid_c] != 0:
                for arrow in self.arrows:
                    if arrow.r == grid_r and arrow.c == grid_c and arrow.state == "idle":
                        if self.check_path_clear(grid_r, grid_c, arrow.dir_type):
                            arrow.state = "flying"
                            self.grid[grid_r][grid_c] = 0
                        else:
                            arrow.state = "shaking"
                            arrow.shake_timer = 20
                            self.mistakes -= 1
                            if self.mistakes <= 0: self.state = "GAME_OVER"
                        break

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
            self.draw_text("点击屏幕开始", self.font_large, GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)

        elif self.state == "LEVEL_SELECT":
            self.draw_text("选择关卡", self.font_title, WHITE, SCREEN_WIDTH // 2, 80)
            btn_w, btn_h, spacing_x, spacing_y, cols = 100, 100, 40, 40, 3
            start_x = (SCREEN_WIDTH - (cols * btn_w + (cols - 1) * spacing_x)) // 2
            start_y = 180
            mx, my = pygame.mouse.get_pos()

            for i in range(len(LEVELS)):
                row, col = i // cols, i % cols
                bx, by = start_x + col * (btn_w + spacing_x), start_y + row * (btn_h + spacing_y)
                rect = pygame.Rect(bx, by, btn_w, btn_h)

                # 鼠标悬停高亮
                bg_color = (100, 160, 210) if rect.collidepoint((mx, my)) else (70, 130, 180)
                pygame.draw.rect(self.screen, bg_color, rect, border_radius=20)
                pygame.draw.rect(self.screen, WHITE, rect, width=3, border_radius=20)
                self.draw_text(f"{i + 1}", self.font_title, WHITE, rect.centerx, rect.centery, shadow=False)

        elif self.state == "PLAYING":
            self.draw_text(f"⭐ 关卡: {self.current_level + 1}", self.font_normal, WHITE, 20, 20, "topleft")
            remain = sum(1 for row in self.grid for val in row if val != 0)
            self.draw_text(f"🏹 剩余箭头: {remain}", self.font_normal, WHITE, 20, 50, "topleft")
            color = (255, 100, 100) if self.mistakes <= 1 else WHITE
            self.draw_text(f"❤️ 剩余失误: {self.mistakes}", self.font_normal, color, 20, 80, "topleft")

            # 绘制返回菜单按钮
            btn_menu = pygame.Rect(SCREEN_WIDTH - 210, 20, 90, 40)
            pygame.draw.rect(self.screen, (100, 100, 120), btn_menu, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_menu, width=2, border_radius=15)
            self.draw_text("菜单", self.font_normal, WHITE, btn_menu.centerx, btn_menu.centery, shadow=False)

            # 绘制重新开始按钮
            btn_restart = pygame.Rect(SCREEN_WIDTH - 110, 20, 90, 40)
            pygame.draw.rect(self.screen, (70, 130, 180), btn_restart, border_radius=15)
            pygame.draw.rect(self.screen, WHITE, btn_restart, width=2, border_radius=15)
            self.draw_text("重试", self.font_normal, WHITE, btn_restart.centerx, btn_restart.centery, shadow=False)

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
                self.draw_text("关卡完成！", self.font_title, (100, 255, 100), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("点击屏幕进入下一关", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            elif self.state == "GAME_OVER":
                self.draw_text("游戏失败", self.font_title, (255, 80, 80), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("点击屏幕重新挑战本关", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            elif self.state == "GAME_WON":
                self.draw_text("恭喜！全部通关！", self.font_title, (100, 200, 255), SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT // 3)
                self.draw_text("点击返回关卡选择", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "START":
                        self.state = "LEVEL_SELECT"
                    elif self.state == "LEVEL_SELECT":
                        self.handle_level_select_click(event.pos)
                    elif self.state == "PLAYING":
                        self.handle_playing_click(event.pos)
                    elif self.state == "LEVEL_CLEAR":
                        self.current_level += 1
                        self.load_level(self.current_level)
                        if self.state != "GAME_WON": self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        self.load_level(self.current_level)
                        self.state = "PLAYING"
                    elif self.state == "GAME_WON":
                        self.state = "LEVEL_SELECT"
                        self.bg_surface = self.create_background(self.themes[0])

            if self.state == "PLAYING":
                for arrow in self.arrows: arrow.update()
                self.arrows = [a for a in self.arrows if not a.is_dead]
                remain = sum(1 for row in self.grid for val in row if val != 0)
                if remain == 0 and len(self.arrows) == 0:
                    if self.current_level >= len(LEVELS) - 1:
                        self.state = "GAME_WON"
                    else:
                        self.state = "LEVEL_CLEAR"

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()