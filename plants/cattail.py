"""
猫尾草植物类
"""
import pygame
from .shooter_base import ShooterPlant


class Cattail(ShooterPlant):
    """猫尾草：全地图追踪攻击"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'cattail_60',
        'display_name': '猫尾草',
        'category': 'shooter',
        'preview_alpha': 130,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "cattail", constants, images, level_manager, base_shoot_delay=45)

    def find_nearest_zombie(self, zombies):
        """为猫尾草查找最近的僵尸（全地图范围）"""
        nearest_zombie = None
        min_distance = float('inf')

        for zombie in zombies:
            # 移除位置限制，检测全图僵尸
            dx = zombie.col - self.col
            dy = zombie.row - self.row
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

        return nearest_zombie

    def draw(self, surface):
        """绘制猫尾草"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('cattail_img'):
            surface.blit(self.images['cattail_img'], (x, y))
        else:
            # 默认紫色圆形
            pygame.draw.circle(surface, (128, 0, 128),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)