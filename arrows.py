import math
import random

from configs import *

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

