"""
月亮花植物类 - 第23关特殊植物
每个月亮花为所有植物提供10%攻速加成，最高50%
"""
import pygame
import random
from .shooter_base import ShooterPlant


class MoonFlower(ShooterPlant):
    """月亮花植物类"""

    # 类级别的植物信息
    PLANT_INFO = {
        'icon_key': 'moon_flower_60',
        'display_name': '月亮花',
        'category': 'shooter',
        'preview_alpha': 128,
    }

    def __init__(self, row, col, constants=None, images=None, level_manager=None):
        # 使用猫尾草的射击间隔作为基础攻速 (30帧 = 0.5秒)
        super().__init__(row, col, "moon_flower", constants, images, level_manager, base_shoot_delay=30)

        # 月亮花特有属性
        self.damage = 30
        self.glow_effect_timer = 0
        self.glow_alpha = 100
        self.glow_increasing = True

        # 记录当前场上月亮花数量（用于显示效果）
        self.moon_flower_count = 0

    @classmethod
    def get_plant_type(cls):
        """获取植物类型标识"""
        return "moon_flower"

    def update(self):
        """更新月亮花状态，包括发光效果"""
        # 调用父类更新射击计时器
        result = super().update()

        # 更新发光效果
        self.update_glow_effect()

        return result

    def update_glow_effect(self):
        """更新月亮花的发光效果"""
        self.glow_effect_timer += 1

        # 发光透明度在100-200之间波动
        if self.glow_increasing:
            self.glow_alpha += 2
            if self.glow_alpha >= 200:
                self.glow_alpha = 200
                self.glow_increasing = False
        else:
            self.glow_alpha -= 2
            if self.glow_alpha <= 100:
                self.glow_alpha = 100
                self.glow_increasing = True

    def can_shoot(self):
        """检查是否可以射击"""
        # 月亮花需要有前方僵尸才能射击
        return super().can_shoot()

    def get_actual_shoot_delay(self):
        """
        获取实际的射击延迟（考虑月亮花加成）
        这个方法会被其他植物调用来获取加成后的攻速
        """
        base_delay = self.base_shoot_delay

        # 获取关卡射速倍率
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 应用基础射速倍率
        adjusted_delay = int(base_delay / speed_multiplier)

        # 注意：月亮花加成在 game_logic 中统一处理
        # 这里只返回基础调整后的延迟
        return adjusted_delay

    def draw(self, surface):
        """绘制月亮花和发光效果"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        # 绘制发光效果（在植物下方）
        self._draw_glow_effect(surface, x, y)

        # 绘制月亮花图像
        if self.images and self.images.get('moon_flower_img'):
            moon_flower_img = self.images['moon_flower_img']
            # 居中绘制
            img_x = x + (self.constants['GRID_SIZE'] - moon_flower_img.get_width()) // 2
            img_y = y + (self.constants['GRID_SIZE'] - moon_flower_img.get_height()) // 2
            surface.blit(moon_flower_img, (img_x, img_y))
        else:
            # 默认绘制：深蓝色花朵与月亮符号
            center_x = x + self.constants['GRID_SIZE'] // 2
            center_y = y + self.constants['GRID_SIZE'] // 2

            # 绘制花瓣（深蓝色）
            petal_color = (70, 70, 150)
            for angle in range(0, 360, 45):
                import math
                rad = math.radians(angle)
                petal_x = center_x + int(20 * math.cos(rad))
                petal_y = center_y + int(20 * math.sin(rad))
                pygame.draw.circle(surface, petal_color, (petal_x, petal_y), 8)

            # 绘制中心月亮（淡黄色）
            moon_color = (255, 255, 200)
            pygame.draw.circle(surface, moon_color, (center_x, center_y), 12)

            # 绘制月牙效果
            crescent_color = (240, 240, 180)
            pygame.draw.circle(surface, crescent_color, (center_x - 3, center_y), 10)

        # 绘制血条
        self._draw_health_bar(surface, x, y)

        # 如果有多个月亮花，显示加成效果
        if self.moon_flower_count > 1:
            self._draw_boost_indicator(surface, x, y)

    def _draw_glow_effect(self, surface, x, y):
        """绘制发光效果"""
        center_x = x + self.constants['GRID_SIZE'] // 2
        center_y = y + self.constants['GRID_SIZE'] // 2

        # 创建带透明度的surface
        glow_surface = pygame.Surface((self.constants['GRID_SIZE'] * 2, self.constants['GRID_SIZE'] * 2),
                                      pygame.SRCALPHA)

        # 绘制多层光晕
        for i in range(3):
            radius = 25 + i * 8
            alpha = max(30, self.glow_alpha - i * 40)
            color = (200, 200, 255, alpha)  # 淡蓝色光晕
            pygame.draw.circle(glow_surface, color,
                               (self.constants['GRID_SIZE'], self.constants['GRID_SIZE']),
                               radius)

        # 将光晕绘制到主surface
        surface.blit(glow_surface, (x - self.constants['GRID_SIZE'] // 2, y - self.constants['GRID_SIZE'] // 2))

    def _draw_boost_indicator(self, surface, x, y):
        """绘制攻速加成指示器"""
        # 计算加成百分比
        boost_percent = min(self.moon_flower_count * 10, 50)

        # 在植物上方显示加成百分比
        if self.constants and 'font_tiny' in dir(self):
            text = f"+{boost_percent}%"
            text_color = (255, 255, 100)  # 金黄色

            # 这里需要从外部获取字体，暂时使用默认字体
            try:
                font = pygame.font.Font(None, 16)
                text_surface = font.render(text, True, text_color)
                text_x = x + self.constants['GRID_SIZE'] // 2 - text_surface.get_width() // 2
                text_y = y - 10
                surface.blit(text_surface, (text_x, text_y))
            except:
                pass

    def set_moon_flower_count(self, count):
        """设置当前场上月亮花数量（用于显示）"""
        self.moon_flower_count = count