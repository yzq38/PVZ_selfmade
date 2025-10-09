"""
寒冰仙人掌植物类
"""
import pygame
from .shooter_base import ShooterPlant


class IceCactus(ShooterPlant):
    """寒冰仙人掌：发射穿透冰弹，冻结僵尸"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'ice_cactus_60',
        'display_name': '寒冰仙人掌',
        'category': 'shooter',
        'preview_alpha': 130,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "ice_cactus", constants, images, level_manager, base_shoot_delay=90)

    def draw(self, surface):
        """绘制寒冰仙人掌"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('ice_cactus_img'):
            surface.blit(self.images['ice_cactus_img'], (x, y))
        else:
            # 默认浅蓝色圆形
            pygame.draw.circle(surface, (173, 216, 230),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)