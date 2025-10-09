"""
坚果墙植物类
"""
import pygame
from .base_plant import BasePlant


class WallNut(BasePlant):
    """坚果墙：高血量防御植物"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'wall_nut_60',
        'display_name': '坚果墙',
        'category': 'defense',
        'preview_alpha': 128,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "wall_nut", constants, images, level_manager)
        # 基类已经设置了血量为1500

    def can_shoot(self):
        """坚果墙不能射击"""
        return False

    def reset_shoot_timer(self):
        """坚果墙没有射击计时器"""
        pass

    def check_for_new_wave(self, has_target_now):
        """坚果墙不需要检测新波次"""
        pass

    def find_nearest_zombie(self, zombies):
        """坚果墙不需要寻找僵尸"""
        return None

    def draw(self, surface):
        """绘制坚果墙"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('wall_nut_img'):
            surface.blit(self.images['wall_nut_img'], (x, y))
        else:
            # 默认棕色圆形
            pygame.draw.circle(surface, (139, 69, 19),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)