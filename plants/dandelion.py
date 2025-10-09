"""
蒲公英植物类
"""
import pygame
import random
from .shooter_base import ShooterPlant


class Dandelion(ShooterPlant):
    """蒲公英：释放5颗飘散种子"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'dandelion_60',
        'display_name': '蒲公英',
        'category': 'shooter',
        'preview_alpha': 110,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "dandelion", constants, images, level_manager, base_shoot_delay=120)

        # 蒲公英特有属性
        self.seeds_per_shot = 5  # 每次释放5颗种子
        self.current_seeds_count = 0  # 当前释放的种子计数

    def update(self):
        """更新蒲公英状态"""
        # 速度倍率支持
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 速度倍率越高，计时器增加越快
        self.shoot_timer += speed_multiplier
        return 0

    def create_dandelion_seeds(self, zombies_list):
        """为蒲公英创建5颗种子，随机选择目标僵尸"""
        if not zombies_list:
            return []

        seeds = []
        available_zombies = [z for z in zombies_list if z.health > 0]

        if not available_zombies:
            return []

        # 计算蒲公英的屏幕位置
        plant_x = self.col
        plant_y = self.row

        for i in range(self.seeds_per_shot):
            # 随机选择目标僵尸
            target_zombie = random.choice(available_zombies)

            # 为每颗种子添加随机发射偏移
            offset_x = random.uniform(-0.2, 0.2)
            offset_y = random.uniform(-0.2, 0.2)

            # 导入蒲公英种子类
            from bullets import DandelionSeed

            seed = DandelionSeed(
                start_x=plant_x + offset_x,
                start_y=plant_y + offset_y,
                target_zombie=target_zombie,
                constants=self.constants,
                images=self.images
            )

            seeds.append(seed)

        return seeds

    def draw(self, surface):
        """绘制蒲公英"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('dandelion_img'):
            surface.blit(self.images['dandelion_img'], (x, y))
        else:
            # 默认黄色圆形
            pygame.draw.circle(surface, (255, 255, 100),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)