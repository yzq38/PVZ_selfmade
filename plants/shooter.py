"""
豌豆射手植物类
"""
import pygame
from .shooter_base import ShooterPlant


class Shooter(ShooterPlant):
    """豌豆射手：发射豌豆子弹"""

    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'pea_shooter_60',
        'display_name': '豌豆射手',
        'category': 'shooter',
        'preview_alpha': 128,
    }

    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "shooter", constants, images, level_manager, base_shoot_delay=60)

    @classmethod
    def get_plant_type(cls):
        """重写以返回正确的植物类型"""
        return "shooter"  # 确保返回 "shooter" 而不是其他值

    def draw(self, surface):
        """绘制豌豆射手"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('pea_shooter_img'):
            surface.blit(self.images['pea_shooter_img'], (x, y))
        else:
            # 默认绿色圆形
            pygame.draw.circle(surface, (0, 255, 0),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)