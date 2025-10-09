"""
西瓜子弹类 - 具有抛物线轨迹和溅射伤害的强力子弹
"""
import pygame
import math
import random
from .base_bullet import BaseBullet


class MelonBullet(BaseBullet):
    """西瓜子弹类 - 抛物线飞行，着陆爆炸造成溅射伤害"""

    def __init__(self, row, col, target_col=None, constants=None, images=None, **kwargs):
        super().__init__(row, col, bullet_type="melon", constants=constants, images=images, **kwargs)

        # 西瓜子弹属性
        self.dmg = 50  # 西瓜伤害是豌豆的两倍
        self.splash_dmg = max(1, 10)  # 溅射伤害是10

        # 西瓜抛物线参数
        self.start_col = col
        self.target_col = target_col if target_col is not None else (constants['GRID_WIDTH'] if constants else 9)
        self.flight_progress = 0.0  # 飞行进度 0-1
        self.max_height = 2.0  # 最大飞行高度（网格单位）
        self.flight_speed = 0.03  # 西瓜飞行速度
        self.has_landed = False  # 是否已经落地
        self.splash_applied = False  # 是否已经应用溅射伤害
        self.has_hit_target = False  # 是否已经击中过目标（防止多次击中）

        # 添加溅射效果显示相关属性
        self.show_splash_effect = False
        self.splash_effect_timer = 0
        self.splash_effect_duration = 30  # 30帧显示溅射效果

        # 西瓜爆炸烟花效果
        self.explosion_particles = []
        self.show_explosion = False
        self.explosion_triggered = False

    def update(self, zombies_list=None):
        """更新西瓜子弹的抛物线飞行"""
        # 增加飞行进度
        self.flight_progress += self.flight_speed

        # 如果飞行进度超过1，表示已经到达目标位置
        if self.flight_progress >= 1.0:
            self.flight_progress = 1.0
            self.has_landed = True
            self.col = self.target_col
            return False  # 不移除，等待碰撞检测

        # 计算当前水平位置（线性插值）
        self.col = self.start_col + (self.target_col - self.start_col) * self.flight_progress

        # 检查是否超出屏幕右边缘
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        return self.col > grid_width

    def can_hit_zombie(self, zombie):
        """西瓜子弹的碰撞检测（仅在落地后）"""
        if zombie.is_dying:
            return False
        return self.has_landed and abs(zombie.col - self.col) < 0.5 and zombie.row == self.row

    def can_splash_hit_zombie(self, zombie):
        """检查僵尸是否在溅射范围内（扩大的椭圆范围）"""
        if not self.has_landed or zombie.is_dying:
            return False

        # 扩大椭圆范围：水平±1.0格，垂直±1.5格
        horizontal_distance = abs(zombie.col - self.col)
        vertical_distance = abs(zombie.row - self.row)

        # 修复：只排除已经受到直接伤害的僵尸，而不是排除所有接近的僵尸
        if id(zombie) in self.hit_zombies:
            return False  # 已经受到直接伤害，不再给予溅射伤害

        # 椭圆公式: (x/a)² + (y/b)² <= 1, 其中a=1.0, b=1.5
        normalized_distance = (horizontal_distance / 1.0) ** 2 + (vertical_distance / 1.5) ** 2
        return normalized_distance <= 1.0

    def apply_splash_damage(self, zombies):
        """对范围内的僵尸应用溅射伤害，返回受到溅射伤害的僵尸数量"""
        if not self.has_landed or self.splash_applied:
            return 0

        splash_count = 0
        for zombie in zombies:
            if self.can_splash_hit_zombie(zombie) and id(zombie) not in self.splash_hit_zombies:
                # 记录已溅射击中的僵尸
                self.splash_hit_zombies.add(id(zombie))

                # 溅射伤害直接作用于僵尸本体，无视护甲
                zombie.health -= self.splash_dmg
                splash_count += 1

        self.splash_applied = True  # 标记溅射伤害已应用

        if splash_count > 0:
            self.show_splash_effect = True  # 显示溅射效果
            self.splash_effect_timer = 0

        return splash_count

    def attack_zombie(self, zombie, level_settings):
        """西瓜子弹的攻击逻辑"""
        # 不攻击被魅惑的僵尸（友军）
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return 0  # 不造成伤害
        if hasattr(zombie, 'team') and zombie.team == "plant":
            return 0  # 不攻击植物阵营的单位
        if zombie.is_dying or not self.can_hit_zombie(zombie):
            return 0

        zombie_id = id(zombie)
        if zombie_id in self.hit_zombies:
            return 0

        # 检查免疫
        if (hasattr(zombie, 'immunity_chance') and
                random.random() < zombie.immunity_chance):
            self.hit_zombies.add(zombie_id)
            return 2

        # 记录已击中的僵尸
        self.hit_zombies.add(zombie_id)

        # 西瓜子弹对铁门僵尸的特殊处理：直接攻击本体
        if zombie.has_armor and zombie.armor_health > 0:
            zombie.health -= self.dmg
        else:
            zombie.health -= self.dmg

        # 触发爆炸效果
        self.create_explosion_particles()
        return 1

    def create_explosion_particles(self, performance_monitor=None):
        """创建优化后的西瓜爆炸粒子效果"""
        if self.explosion_triggered:
            return

        self.explosion_triggered = True
        self.show_explosion = True

        # 根据性能动态调整粒子数量
        if performance_monitor and performance_monitor.should_reduce_effects():
            max_particles = 30  # 低性能模式
        elif performance_monitor and performance_monitor.is_lagging():
            max_particles = 50  # 中等性能模式
        else:
            max_particles = 80  # 高性能模式

        # 获取爆炸位置
        display_col, display_row, vertical_offset = self.get_display_position()
        explosion_x = self.constants['BATTLEFIELD_LEFT'] + int(
            display_col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))
        explosion_y = (self.constants['BATTLEFIELD_TOP'] +
                       display_row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                       self.constants['GRID_SIZE'] // 2)
        explosion_y -= int(vertical_offset * self.constants['GRID_SIZE'])

        # 创建粒子
        for _ in range(max_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 2)
            size = random.randint(2, 6)
            life = random.randint(20, 60)

            color_choice = random.choice([
                (255, 100, 100),  # 红色果肉
                (255, 150, 150),  # 浅红色果肉
                (30, 30, 30),  # 黑色西瓜籽
                (100, 200, 100),  # 绿色西瓜皮
                (255, 200, 200),  # 粉红色果肉
            ])

            gravity_factor = random.uniform(0.15, 0.25)
            air_resistance = random.uniform(0.92, 0.98)

            self.explosion_particles.append({
                'x': explosion_x,
                'y': explosion_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - random.uniform(0.5, 1.5),
                'size': size,
                'color': color_choice,
                'life': life,
                'max_life': life,
                'gravity': gravity_factor,
                'resistance': air_resistance,
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-10, 10)
            })

    def update_explosion_particles(self):
        """更新爆炸粒子"""
        for particle in self.explosion_particles[:]:
            # 更新位置
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']

            # 应用重力
            particle['vy'] += particle['gravity']

            # 应用空气阻力
            particle['vx'] *= particle['resistance']
            particle['vy'] *= particle['resistance']

            # 更新旋转
            particle['rotation'] += particle['rotation_speed']

            # 减少生命值
            particle['life'] -= 1

            # 移除生命结束的粒子
            if particle['life'] <= 0:
                self.explosion_particles.remove(particle)

        # 如果所有粒子都消失了，停止显示爆炸效果
        if not self.explosion_particles:
            self.show_explosion = False

    def get_display_position(self):
        """获取用于显示的位置（包括垂直偏移）"""
        if not self.has_landed:
            # 计算抛物线的垂直偏移
            # 使用抛物线公式: y = -4h*x*(x-1)，其中h是最大高度
            vertical_offset = -4 * self.max_height * self.flight_progress * (self.flight_progress - 1)
            return self.col, self.row, vertical_offset
        else:
            return self.col, self.row, 0

    def _draw_bullet(self, surface, x, y):
        """绘制西瓜子弹"""
        # 西瓜子弹绘制逻辑
        if not self.explosion_triggered:
            if self.images and self.images.get('watermelon_bullet_img'):
                melon_bullet_img = pygame.transform.scale(self.images['watermelon_bullet_img'], (40, 40))
                surface.blit(melon_bullet_img, (x - 12, y - 12))
            else:
                pygame.draw.circle(surface, (255, 100, 100), (x, y), 8)

        if self.show_explosion:
            self.draw_explosion_particles(surface)

    def draw_explosion_particles(self, surface):
        """绘制爆炸粒子"""
        for particle in self.explosion_particles:
            # 计算透明度基于生命值
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*particle['color'], alpha)

            # 根据粒子大小选择绘制方式
            if particle['size'] <= 3:
                # 小粒子绘制为圆点
                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color,
                                   (particle['size'], particle['size']), particle['size'])
            else:
                # 大粒子绘制为旋转的小方块，模拟西瓜块
                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                # 创建旋转的矩形
                rect_surface = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
                rect_surface.fill(color)
                rotated_surface = pygame.transform.rotate(rect_surface, particle['rotation'])
                rect_rect = rotated_surface.get_rect(center=(particle['size'], particle['size']))
                particle_surface.blit(rotated_surface, rect_rect)

            # 绘制粒子到屏幕
            surface.blit(particle_surface, (int(particle['x'] - particle['size']),
                                            int(particle['y'] - particle['size'])))

    def update(self, zombies_list=None):
        """重写update方法，包含爆炸粒子更新"""
        # 更新爆炸粒子
        if self.show_explosion:
            self.update_explosion_particles()

        # 调用父类的飞行逻辑
        return self._update_melon()

    def _update_melon(self):
        """更新西瓜子弹的抛物线飞行"""
        # 增加飞行进度
        self.flight_progress += self.flight_speed

        # 如果飞行进度超过1，表示已经到达目标位置
        if self.flight_progress >= 1.0:
            self.flight_progress = 1.0
            self.has_landed = True
            self.col = self.target_col
            return False  # 不移除，等待碰撞检测

        # 计算当前水平位置（线性插值）
        self.col = self.start_col + (self.target_col - self.start_col) * self.flight_progress

        # 检查是否超出屏幕右边缘
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        return self.col > grid_width