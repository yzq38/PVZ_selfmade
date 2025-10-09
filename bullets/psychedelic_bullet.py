"""
迷幻子弹类 - 类似西瓜的抛物线轨迹，击中后魅惑僵尸并造成伤害
"""
import pygame
import math
import random
from .base_bullet import BaseBullet


class PsychedelicBullet(BaseBullet):
    """迷幻子弹 - 小蘑菇子弹，魅惑僵尸并造成伤害"""

    def __init__(self, row, col, target_col=None, constants=None, images=None, **kwargs):
        super().__init__(row, col, bullet_type="psychedelic", constants=constants, images=images, **kwargs)

        # 迷幻子弹属性
        self.dmg = 20  # 造成20点伤害
        self.charm_duration = 300  # 魅惑持续5秒

        # 抛物线参数（类似西瓜）
        self.start_col = col
        self.target_col = target_col if target_col is not None else (constants['GRID_WIDTH'] if constants else 9)
        self.flight_progress = 0.0
        self.max_height = 2  # 飞行高度
        self.flight_speed = 0.03  # 飞行速度
        self.has_landed = False
        self.has_hit_target = False

        # 视觉效果
        self.trail_particles = []  # 尾迹粒子
        self.charm_particles = []  # 魅惑特效粒子

    def update(self, zombies_list=None):
        """更新子弹飞行"""
        # 更新尾迹
        self.update_trail()

        # 如果已经击中目标，不再移动
        if self.has_hit_target:
            return False  # 不移除，等待游戏逻辑处理

        # 增加飞行进度
        self.flight_progress += self.flight_speed

        if self.flight_progress >= 1.0:
            self.flight_progress = 1.0
            self.has_landed = True
            self.col = self.target_col
            return False  # 着陆后不移除，等待击中僵尸

        # 计算当前位置
        self.col = self.start_col + (self.target_col - self.start_col) * self.flight_progress

        # 只有当子弹飞出屏幕右边界时才移除
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        if self.col > grid_width + 1:  # 超出屏幕边界
            return True  # 移除子弹

        return False  # 继续存在

    def can_hit_zombie(self, zombie):
        """检测是否可以击中僵尸"""
        if zombie.is_dying:
            return False

        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return False

        distance_check = abs(zombie.col - self.col) < 0.5
        row_check = zombie.row == self.row
        landed_check = self.has_landed

        return landed_check and distance_check and row_check

    def attack_zombie(self, zombie, level_settings):
        """魅惑僵尸并造成伤害"""
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

        # 记录已击中
        self.hit_zombies.add(zombie_id)

        # 计算实际伤害值
        actual_damage = self.dmg

        # 检查僵尸是否有护甲
        if zombie.has_armor and zombie.armor_health > 0:
            # 优先攻击护甲
            armor_damage = min(actual_damage, zombie.armor_health)
            zombie.armor_health -= armor_damage
            remaining_damage = actual_damage - armor_damage

            # 如果还有剩余伤害，攻击血量
            if remaining_damage > 0:
                zombie.health -= remaining_damage
        else:
            # 没有护甲，直接攻击血量
            zombie.health -= actual_damage

        # 确保血量不会变成负数
        zombie.health = max(0, zombie.health)

        # 应用魅惑效果（只有在僵尸还活着时才魅惑）
        if zombie.health > 0:
            zombie.pending_charm = self.charm_duration

        # 创建魅惑特效
        self.create_charm_effect(zombie)

        return 1  # 返回击中

    def create_charm_effect(self, zombie):
        """创建魅惑特效粒子"""
        # 在僵尸位置创建粉色爱心或星星粒子
        for _ in range(10):
            self.charm_particles.append({
                'x': self.col,
                'y': self.row,
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-2, -0.5),
                'life': 30,
                'color': random.choice([
                    (255, 182, 193),  # 浅粉色
                    (255, 105, 180),  # 热粉色
                    (219, 112, 147),  # 苍紫色
                ])
            })

    def update_trail(self):
        """更新尾迹粒子"""
        if not self.has_landed:
            # 添加新的尾迹粒子
            if random.random() < 0.6:  # 60%概率生成粒子
                display_col, display_row, vertical_offset = self.get_display_position()
                self.trail_particles.append({
                    'x': display_col,
                    'y': display_row - vertical_offset,
                    'life': 20,
                    'size': random.randint(2, 4)
                })

        # 更新现有粒子
        for particle in self.trail_particles[:]:
            particle['life'] -= 1
            particle['size'] *= 0.95
            if particle['life'] <= 0:
                self.trail_particles.remove(particle)

    def get_display_position(self):
        """获取显示位置（包括抛物线高度）"""
        if not self.has_landed:
            vertical_offset = -4 * self.max_height * self.flight_progress * (self.flight_progress - 1)
            return self.col, self.row, vertical_offset
        else:
            return self.col, self.row, 0

    def _draw_bullet(self, surface, x, y):
        """绘制迷幻子弹"""
        # 绘制尾迹
        for particle in self.trail_particles:
            alpha = int(255 * (particle['life'] / 20))
            color = (255, 192, 203, alpha)  # 粉色尾迹

            if self.constants:
                px = self.constants['BATTLEFIELD_LEFT'] + int(
                    particle['x'] * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))
                py = (self.constants['BATTLEFIELD_TOP'] +
                      particle['y'] * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                      self.constants['GRID_SIZE'] // 2)

                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color,
                                   (particle['size'], particle['size']), int(particle['size']))
                surface.blit(particle_surface, (px - particle['size'], py - particle['size']))

        # 绘制子弹本体
        if not self.has_hit_target:
            if self.images and self.images.get('small_psychedelic_bullet_img'):
                bullet_img = pygame.transform.scale(self.images['small_psychedelic_bullet_img'], (20, 20))
                surface.blit(bullet_img, (x - 15, y - 15))
            else:
                # 绘制默认的蘑菇形状
                pygame.draw.circle(surface, (219, 112, 147), (x, y - 3), 6)  # 蘑菇帽
                pygame.draw.rect(surface, (255, 228, 196), (x - 2, y - 3, 4, 6))  # 蘑菇柄

        # 绘制魅惑特效
        for particle in self.charm_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # 重力
            particle['life'] -= 1

            if particle['life'] > 0:
                alpha = int(255 * (particle['life'] / 30))
                px = self.constants['BATTLEFIELD_LEFT'] + int(
                    particle['x'] * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))
                py = (self.constants['BATTLEFIELD_TOP'] +
                      particle['y'] * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                      self.constants['GRID_SIZE'] // 2)

                # 绘制爱心形状的粒子
                size = 4
                heart_surface = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
                color = (*particle['color'], alpha)

                # 简单的心形
                pygame.draw.circle(heart_surface, color, (size, size), size // 2)
                pygame.draw.circle(heart_surface, color, (size * 2, size), size // 2)
                pygame.draw.polygon(heart_surface, color,
                                    [(size // 2, size), (size * 2.5, size),
                                     (size * 1.5, size * 2.5)])

                surface.blit(heart_surface, (px - size * 1.5, py - size * 1.5))
            else:
                self.charm_particles.remove(particle)