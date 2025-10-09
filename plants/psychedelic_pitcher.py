"""
迷幻投手植物类 - 投掷魅惑蘑菇
"""
import math
import pygame
from .shooter_base import ShooterPlant
from .plant_registry import plant_registry
import bullets



class PsychedelicPitcher(ShooterPlant):
    """迷幻投手 - 魅惑僵尸使其倒戈"""

    # 类级别信息
    PLANT_INFO = {
        'icon_key': 'psychedelic_pitcher_60',
        'display_name': '迷幻投手',
        'category': 'shooter',
        'preview_alpha': 128,
    }

    def __init__(self, row, col, constants=None, images=None, level_manager=None):
        super().__init__(row, col, "psychedelic_pitcher", constants, images, level_manager, base_shoot_delay=90)

        # 迷幻投手特有属性
        self.shoot_interval = 240
        self.shoot_timer = 0


        # 动画相关
        self.animation_timer = 0
        self.is_throwing = False
        self.throw_animation_duration = 50

    @classmethod
    def get_plant_type(cls):
        return "psychedelic_pitcher"

    def can_shoot(self):
        """检查是否可以投掷"""
        return self.shoot_timer >= self.shoot_interval

    def reset_shoot_timer(self):
        """重置投掷计时器"""
        self.shoot_timer = 0
        self.is_throwing = True
        self.animation_timer = 0

    def update(self):
        self.shoot_timer += 1

        return 0

    def draw(self, surface):
        """绘制迷幻投手"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (
                self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (
                self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        # 使用动态尺寸而不是硬编码
        grid_size = self.constants['GRID_SIZE']

        # 绘制植物图像
        if self.images and self.images.get('psychedelic_pitcher_img'):
            img = self.images['psychedelic_pitcher_img']
            # 使用完整的方格大小，无动画效果
            img = pygame.transform.scale(img, (grid_size, grid_size))
            surface.blit(img, (x, y))
        else:
            # 默认绘制 - 使用更大的尺寸填满方格
            color = (219, 112, 147)  # 苍紫色
            # 使用更大的半径，几乎填满方格
            radius = int(grid_size * 0.4)
            pygame.draw.circle(surface, color,
                               (x + grid_size // 2,
                                y + grid_size // 2),
                               radius)

            # 添加一个更明显的标识，比如内圆
            inner_color = (255, 182, 193)  # 浅粉色
            inner_radius = int(radius * 0.6)
            pygame.draw.circle(surface, inner_color,
                               (x + grid_size // 2,
                                y + grid_size // 2),
                               inner_radius)

        # 绘制血条
        self._draw_health_bar(surface, x, y)