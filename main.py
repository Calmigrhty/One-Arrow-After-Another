import pygame
import sys
import math

# ================= 配置与常量 =================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60
GRID_SIZE = 80  # 棋盘格大小

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)
DARK_GRAY = (150, 150, 150)
BLUE = (70, 130, 180)
RED = (220, 20, 60)
GREEN = (50, 205, 50)
BG_COLOR = (245, 245, 250)

# 方向映射 (行偏移, 列偏移)
# 1: 上, 2: 下, 3: 左, 4: 右
DIR_MAP = {
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1)
}

# 关卡设计 (0表示空，1234表示方向)
LEVELS = [
    {  # 关卡 1: 最基础的消除
        "grid": [
            [0, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 4, 3, 0],
            [0, 0, 2, 0]
        ],
        "mistakes": 3
    },
    {  # 关卡 2: 存在互相阻挡
        "grid": [
            [0, 1, 0, 2],
            [4, 4, 3, 0],
            [0, 1, 0, 0],
            [0, 4, 1, 3]
        ],
        "mistakes": 4
    },
    {  # 关卡 3: 密集阵型
        "grid": [
            [1, 2, 3, 4],
            [4, 0, 0, 1],
            [1, 0, 0, 4],
            [4, 2, 1, 3]
        ],
        "mistakes": 5
    }
]


# ================= 游戏类 =================
class Arrow:
    def __init__(self, r, c, dir_type):
        self.r = r
        self.c = c
        self.dir_type = dir_type
        # 实际像素坐标 (相对棋盘左上角)
        self.x = c * GRID_SIZE
        self.y = r * GRID_SIZE

        self.state = "idle"  # idle: 静止, shaking: 碰撞晃动, flying: 飞出
        self.shake_timer = 0
        self.speed = 20
        self.is_dead = False  # 是否已完全飞出屏幕

    def update(self):
        if self.state == "flying":
            dr, dc = DIR_MAP[self.dir_type]
            self.x += dc * self.speed
            self.y += dr * self.speed
            # 飞出足够远的距离后标记死亡
            if abs(self.x) > SCREEN_WIDTH or abs(self.y) > SCREEN_HEIGHT:
                self.is_dead = True

        elif self.state == "shaking":
            self.shake_timer -= 1
            if self.shake_timer <= 0:
                self.state = "idle"

    def draw(self, surface, offset_x, offset_y):
        if self.is_dead:
            return

        draw_x = offset_x + self.x
        draw_y = offset_y + self.y

        # 处理晃动动画
        if self.state == "shaking":
            shake_amt = math.sin(self.shake_timer) * 5
            if self.dir_type in [1, 2]:  # 上下方向被阻挡，左右晃动
                draw_x += shake_amt
            else:  # 左右方向被阻挡，上下晃动
                draw_y += shake_amt

        # 绘制背景方块
        rect = pygame.Rect(draw_x + 5, draw_y + 5, GRID_SIZE - 10, GRID_SIZE - 10)
        pygame.draw.rect(surface, BLUE, rect, border_radius=10)

        # 绘制箭头 (使用多边形)
        cx, cy = draw_x + GRID_SIZE // 2, draw_y + GRID_SIZE // 2
        s = 15  # 箭头尺寸

        if self.dir_type == 1:  # 上
            pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
        elif self.dir_type == 2:  # 下
            pts = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
        elif self.dir_type == 3:  # 左
            pts = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
        elif self.dir_type == 4:  # 右
            pts = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]

        pygame.draw.polygon(surface, WHITE, pts)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("一箭又一箭 (AIGC 辅助开发版)")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48)  # 优先尝试使用黑体，不支持中文时可能回退
        self.font_normal = pygame.font.SysFont("simhei", 24)

        self.state = "START"  # START, PLAYING, LEVEL_CLEAR, GAME_OVER, GAME_WON
        self.current_level = 0
        self.load_level(self.current_level)

    def load_level(self, level_idx):
        if level_idx >= len(LEVELS):
            self.state = "GAME_WON"
            return

        level_data = LEVELS[level_idx]
        grid_data = level_data["grid"]
        self.rows = len(grid_data)
        self.cols = len(grid_data[0])
        self.mistakes = level_data["mistakes"]

        # 居中计算
        self.offset_x = (SCREEN_WIDTH - self.cols * GRID_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - self.rows * GRID_SIZE) // 2 + 50

        # 初始化逻辑网格和箭头对象
        self.grid = [[grid_data[r][c] for c in range(self.cols)] for r in range(self.rows)]
        self.arrows = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != 0:
                    self.arrows.append(Arrow(r, c, self.grid[r][c]))

    def check_path_clear(self, r, c, dir_type):
        """核心算法：检测前方是否有阻挡物"""
        dr, dc = DIR_MAP[dir_type]
        curr_r, curr_c = r + dr, c + dc

        while 0 <= curr_r < self.rows and 0 <= curr_c < self.cols:
            if self.grid[curr_r][curr_c] != 0:
                return False  # 被阻挡
            curr_r += dr
            curr_c += dc
        return True  # 无阻挡

    def handle_click(self, pos):
        # 检查重新开始按钮 (简化为屏幕右上角区域)
        btn_rect = pygame.Rect(SCREEN_WIDTH - 120, 20, 100, 40)
        if btn_rect.collidepoint(pos):
            self.load_level(self.current_level)
            return

        mx, my = pos
        # 换算为逻辑网格坐标
        grid_c = int((mx - self.offset_x) // GRID_SIZE)
        grid_r = int((my - self.offset_y) // GRID_SIZE)

        if 0 <= grid_r < self.rows and 0 <= grid_c < self.cols:
            if self.grid[grid_r][grid_c] != 0:
                # 找到被点击的箭头对象
                for arrow in self.arrows:
                    if arrow.r == grid_r and arrow.c == grid_c and arrow.state == "idle":
                        if self.check_path_clear(grid_r, grid_c, arrow.dir_type):
                            # 路径通畅，飞出
                            arrow.state = "flying"
                            self.grid[grid_r][grid_c] = 0  # 立即从逻辑网格中移除，让出路径
                        else:
                            # 路径受阻，晃动并扣除失误
                            arrow.state = "shaking"
                            arrow.shake_timer = 20
                            self.mistakes -= 1
                            if self.mistakes <= 0:
                                self.state = "GAME_OVER"
                        break

    def draw_text(self, text, font, color, x, y, align="center"):
        # 兼容处理：如果没有中文字体，可能显示方块。实际开发中建议引入 .ttf 字体文件
        try:
            surface = font.render(text, True, color)
        except Exception:
            surface = pygame.font.Font(None, font.get_height()).render(text, True, color)
        rect = surface.get_rect()
        if align == "center":
            rect.center = (x, y)
        elif align == "topleft":
            rect.topleft = (x, y)
        self.screen.blit(surface, rect)

    def draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == "START":
            self.draw_text("一箭又一箭", self.font_large, BLACK, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
            self.draw_text("点击屏幕开始", self.font_normal, DARK_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        elif self.state == "PLAYING":
            # 绘制UI
            self.draw_text(f"关卡: {self.current_level + 1}", self.font_normal, BLACK, 20, 20, "topleft")

            # 动态获取剩余箭头数量（还在网格中的）
            remain = sum(1 for row in self.grid for val in row if val != 0)
            self.draw_text(f"剩余箭头: {remain}", self.font_normal, BLACK, 20, 50, "topleft")

            # 失误次数变色警告
            color = RED if self.mistakes <= 1 else BLACK
            self.draw_text(f"剩余失误: {self.mistakes}", self.font_normal, color, 20, 80, "topleft")

            # 重新开始按钮
            btn_rect = pygame.Rect(SCREEN_WIDTH - 120, 20, 100, 40)
            pygame.draw.rect(self.screen, GRAY, btn_rect, border_radius=5)
            self.draw_text("重新开始", self.font_normal, BLACK, btn_rect.centerx, btn_rect.centery)

            # 绘制棋盘底格 (可选)
            for r in range(self.rows):
                for c in range(self.cols):
                    rect = pygame.Rect(self.offset_x + c * GRID_SIZE, self.offset_y + r * GRID_SIZE, GRID_SIZE,
                                       GRID_SIZE)
                    pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)

            # 绘制箭头
            for arrow in self.arrows:
                arrow.draw(self.screen, self.offset_x, self.offset_y)

        elif self.state in ["LEVEL_CLEAR", "GAME_OVER", "GAME_WON"]:
            if self.state == "LEVEL_CLEAR":
                self.draw_text("通关！", self.font_large, GREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("点击进入下一关", self.font_normal, BLACK, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            elif self.state == "GAME_OVER":
                self.draw_text("游戏失败", self.font_large, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("点击重新开始本关", self.font_normal, BLACK, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            elif self.state == "GAME_WON":
                self.draw_text("恭喜！全部通关！", self.font_large, BLUE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
                self.draw_text("你已经完成了所有关卡", self.font_normal, BLACK, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                    if self.state == "START":
                        self.state = "PLAYING"
                    elif self.state == "PLAYING":
                        self.handle_click(event.pos)
                    elif self.state == "LEVEL_CLEAR":
                        self.current_level += 1
                        self.load_level(self.current_level)
                        self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        self.load_level(self.current_level)
                        self.state = "PLAYING"

            if self.state == "PLAYING":
                # 更新所有箭头的动画状态
                for arrow in self.arrows:
                    arrow.update()

                # 清理已死亡的箭头
                self.arrows = [a for a in self.arrows if not a.is_dead]

                # 检测是否清空过关
                remain = sum(1 for row in self.grid for val in row if val != 0)
                if remain == 0 and len(self.arrows) == 0:  # 必须等所有动画飞完
                    self.state = "LEVEL_CLEAR"

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()