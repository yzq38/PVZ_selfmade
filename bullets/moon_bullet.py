"""
月亮子弹类 - 月亮花发射的特殊子弹
"""
import pygame
import math
from .base_bullet import BaseBullet


class MoonBullet(BaseBullet):
    """月亮子弹类"""

    def __init__(self, row, col, **kwargs):
        super().__init__(row, col, bullet_type="moon", **kwargs)

        # 月亮子弹特有属性
        self.dmg = 25  # 伤害值
        self.speed = 0.08  # 与普通豌豆子弹相同的速度
        self.rotation = 0  # 旋转角度
        self.glow_timer = 0  # 发光效果计时器

        # 飞行轨迹相关
        self.initial_col = col
        self.wave_amplitude = 0.1  # 波动幅度（轻微上下波动）
        self.wave_frequency = 0.1  # 波动频率

    def update(self, zombies_list=None):
        """更新月亮子弹位置"""
        # 检查传送门穿越（如果支持）
        if self.supports_portal_travel and not self.has_traveled_through_portal:
            if self._check_portal_travel():
                pass

        # 正常移动
        self.col += self.speed

        # 更新旋转角度（月亮自转效果）
        self.rotation += 5
        if self.rotation >= 360:
            self.rotation = 0

        # 更新发光效果计时器
        self.glow_timer += 1

        # 检查边界
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        return self.col > grid_width

    def get_display_position(self):
        """获取用于显示的位置（带有轻微波动效果）"""
        display_col = self.col
        display_row = self.row

        # 添加轻微的垂直波动
        distance_traveled = self.col - self.initial_col
        vertical_offset = math.sin(distance_traveled * self.wave_frequency * math.pi) * self.wave_amplitude

        return display_col, display_row, vertical_offset

    def _draw_bullet(self, surface, x, y):
        """绘制月亮子弹"""
        # 如果有月亮子弹图像
        if self.images and self.images.get('small_moon_img'):
            moon_img = self.images['small_moon_img']

            # 旋转图像
            rotated_img = pygame.transform.rotate(moon_img, self.rotation)

            # 居中绘制
            rect = rotated_img.get_rect(center=(x, y))
            surface.blit(rotated_img, rect)
        else:
            # 默认绘制：小月亮形状
            self._draw_default_moon(surface, x, y)

        # 绘制发光效果
        self._draw_moon_glow(surface, x, y)

    def _draw_default_moon(self, surface, x, y):
        """绘制默认的月亮形状"""
        # 主体月亮（淡黄色）
        moon_color = (255, 255, 200)
        pygame.draw.circle(surface, moon_color, (x, y), 8)

        # 月牙阴影效果（稍暗的黄色）
        shadow_color = (240, 240, 180)
        pygame.draw.circle(surface, shadow_color, (x - 2, y), 6)

        # 添加一些"环形山"细节
        crater_color = (245, 245, 190)
        pygame.draw.circle(surface, crater_color, (x + 2, y - 2), 2)
        pygame.draw.circle(surface, crater_color, (x - 1, y + 3), 1)

    def _draw_moon_glow(self, surface, x, y):
        """绘制月亮的发光效果"""
        # 计算发光强度（随时间变化）
        glow_intensity = 100 + int(50 * math.sin(self.glow_timer * 0.1))

        # 创建带透明度的surface
        glow_surface = pygame.Surface((40, 40), pygame.SRCALPHA)

        # 绘制光晕
        for radius in range(15, 5, -2):
            alpha = max(20, glow_intensity - (15 - radius) * 10)
            color = (255, 255, 220, alpha)  # 淡黄色光晕
            pygame.draw.circle(glow_surface, color, (20, 20), radius)

        # 将光晕绘制到主surface
        surface.blit(glow_surface, (x - 20, y - 20))

    def can_hit_zombie(self, zombie):
        """检查是否可以击中僵尸（只击中同一行）"""
        if zombie.is_dying:
            return False

        # 基本距离检查
        distance_check = abs(zombie.col - self.col) < 0.5

        # 月亮子弹只能击中同一行的僵尸
        if self.has_traveled_through_portal:
            row_check = zombie.row == self.row
        else:
            row_check = zombie.row == self.original_row

        return distance_check and row_check

    def _apply_damage(self, zombie):
        """对僵尸造成伤害"""
        if zombie.has_armor and zombie.armor_health > 0:
            zombie.armor_health -= self.dmg
            if zombie.armor_health < 0:
                zombie.health += zombie.armor_health
                zombie.armor_health = 0
        else:
            zombie.health -= self.dmg