"""
向日葵植物类
"""
import pygame
from .base_plant import BasePlant


class Sunflower(BasePlant):
    """向日葵：产生阳光"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'sunflower_60',
        'display_name': '向日葵',
        'category': 'production',
        'preview_alpha': 128,
    }

    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "sunflower", constants, images, level_manager)

        # 产阳光参数
        self.sun_timer = 0
        self.sun_delay = 240
        self.sun_amount = 25

    def update(self):
        """更新向日葵状态，返回产生的阳光量"""
        produced_sun = 0

        # 检查是否有向日葵停产特性
        if self.level_manager and self.level_manager.has_special_feature("sunflower_no_produce"):
            # 向日葵停产，不产生阳光
            return 0

        # 速度倍率支持
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 速度倍率越高，计时器增加越快（相当于生产间隔变短）
        self.sun_timer += speed_multiplier

        if self.sun_timer >= self.sun_delay:
            produced_sun = self.sun_amount
            self.sun_timer = 0  # 重置计时器

        return produced_sun

    def can_shoot(self):
        """向日葵不能射击"""
        return False

    def reset_shoot_timer(self):
        """向日葵没有射击计时器"""
        pass

    def check_for_new_wave(self, has_target_now):
        """向日葵不需要检测新波次"""
        pass

    def find_nearest_zombie(self, zombies):
        """向日葵不需要寻找僵尸"""
        return None

    def draw(self, surface):
        """绘制向日葵"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('sunflower_img'):
            surface.blit(self.images['sunflower_img'], (x, y))
        else:
            # 默认黄色圆形
            pygame.draw.circle(surface, (255, 255, 0),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)