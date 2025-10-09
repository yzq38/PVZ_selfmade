"""
西瓜投手植物类
"""
import pygame
from .shooter_base import ShooterPlant


class MelonPult(ShooterPlant):
    """西瓜投手：发射西瓜，造成溅射伤害"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'watermelon_60',
        'display_name': '西瓜投手',
        'category': 'catapult',
        'preview_alpha': 130,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "melon_pult", constants, images, level_manager, base_shoot_delay=100)

    def draw(self, surface):
        """绘制西瓜投手"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('watermelon_img'):
            surface.blit(self.images['watermelon_img'], (x, y))
        else:
            # 默认深绿色圆形
            pygame.draw.circle(surface, (0, 100, 0),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)