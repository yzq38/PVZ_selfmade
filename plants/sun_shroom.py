"""
阳光菇植物类
"""
import pygame
from .base_plant import BasePlant


class SunShroom(BasePlant):
    """阳光菇：产生阳光，但速率比向日葵慢20%"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'sun_shroom_60',
        'display_name': '阳光菇',
        'category': 'production',
        'preview_alpha': 128,
    }

    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "sun_shroom", constants, images, level_manager)

        # 产阳光参数
        self.sun_timer = 0
        self.sun_delay = 480
        self.sun_amount = 25  # 和向日葵一样的产量

        # 阳光菇的特殊视觉效果（可选）
        self.glow_timer = 0
        self.glow_intensity = 0

    def update(self):
        """更新阳光菇状态，返回产生的阳光量"""
        produced_sun = 0

        # 速度倍率支持
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 速度倍率越高，计时器增加越快（相当于生产间隔变短）
        self.sun_timer += speed_multiplier

        if self.sun_timer >= self.sun_delay:
            produced_sun = self.sun_amount
            self.sun_timer = 0  # 重置计时器

        # 更新发光效果计时器
        self.glow_timer += 1
        self.glow_intensity = abs((self.glow_timer % 120) - 60) / 60.0  # 0到1的周期性变化

        return produced_sun

    def can_shoot(self):
        """阳光菇不能射击"""
        return False

    def reset_shoot_timer(self):
        """阳光菇没有射击计时器"""
        pass

    def check_for_new_wave(self, has_target_now):
        """阳光菇不需要检测新波次"""
        pass

    def find_nearest_zombie(self, zombies):
        """阳光菇不需要寻找僵尸"""
        return None

    def draw(self, surface):
        """绘制阳光菇"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('sun_shroom_img'):
            # 绘制阳光菇图片
            surface.blit(self.images['sun_shroom_img'], (x, y))

            # 绘制发光效果（可选）
            if self.glow_intensity > 0.5:
                # 创建发光效果
                glow_surface = pygame.Surface((self.constants['GRID_SIZE'], self.constants['GRID_SIZE']),
                                              pygame.SRCALPHA)
                glow_color = (255, 255, int(100 + 155 * self.glow_intensity), int(50 * self.glow_intensity))
                pygame.draw.circle(glow_surface, glow_color,
                                   (self.constants['GRID_SIZE'] // 2, self.constants['GRID_SIZE'] // 2),
                                   int(self.constants['GRID_SIZE'] // 3 * (1 + self.glow_intensity * 0.2)))
                surface.blit(glow_surface, (x, y))
        else:
            # 默认绘制：紫色蘑菇形状
            center_x = x + self.constants['GRID_SIZE'] // 2
            center_y = y + self.constants['GRID_SIZE'] // 2

            # 绘制蘑菇柄
            pygame.draw.rect(surface, (150, 100, 200),
                             (center_x - 8, center_y, 16, 20))

            # 绘制蘑菇帽
            pygame.draw.circle(surface, (200, 150, 255),
                               (center_x, center_y - 5),
                               self.constants['GRID_SIZE'] // 3)

            # 绘制发光点
            if self.glow_intensity > 0.5:
                pygame.draw.circle(surface, (255, 255, 200),
                                   (center_x, center_y - 5),
                                   int(5 + self.glow_intensity * 3))

        # 绘制血条
        self._draw_health_bar(surface, x, y)