"""
冰子弹类 - 具有冰冻效果的特殊子弹
"""
import random

import pygame
import math
from .base_bullet import BaseBullet


class IceBullet(BaseBullet):
    """冰子弹类 - 造成伤害并冰冻敌人的特殊子弹"""

    def __init__(self, row, col, constants=None, images=None, **kwargs):
        super().__init__(row, col, bullet_type="ice", constants=constants, images=images, **kwargs)

        # 冰子弹属性
        self.dmg = 30  # 寒冰子弹伤害
        self.splash_dmg = 0
        self.freeze_duration = 5000  # 冰冻持续时间（毫秒）
        self.freeze_applied_zombies = set()  # 已冻结过的僵尸集合update_freeze_effects

    def can_hit_zombie(self, zombie):
        """寒冰子弹碰撞检测"""
        if zombie.is_dying:
            return False
        # 寒冰子弹只能击中同行的僵尸
        return zombie.row == self.row and abs(zombie.col - self.col) < 0.5

    def attack_zombie(self, zombie, level_settings):
        """冰子弹的攻击逻辑 - 造成伤害并冰冻敌人"""
        # 不攻击被魅惑的僵尸（友军）
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return 0  # 不造成伤害
        if hasattr(zombie, 'team') and zombie.team == "plant":
            return 0  # 不攻击植物阵营的单位
        if zombie.is_dying or not self.can_hit_zombie(zombie):
            return 0

        zombie_id = id(zombie)

        # 对于寒冰子弹，检查是否已经冻结过这个僵尸
        if zombie_id in self.freeze_applied_zombies:
            return 0

        # 检查免疫
        if (hasattr(zombie, 'immunity_chance') and
                random.random() < zombie.immunity_chance):
            self.freeze_applied_zombies.add(zombie_id)
            return 2

        # 记录已击中的僵尸
        self.hit_zombies.add(zombie_id)

        # 应用冰冻伤害和效果
        self._apply_ice_damage_and_freeze(zombie)
        self.freeze_applied_zombies.add(zombie_id)
        return 1

    def _apply_ice_damage_and_freeze(self, zombie):
        """应用寒冰伤害和冰冻效果 - 修复版：正确处理冰车僵尸的免疫"""
        # 寒冰子弹无视防具，直接对本体造成伤害
        damage = self.dmg
        zombie.health -= damage
        zombie.health = max(0, zombie.health)  # 确保血量不为负数

        # 检查僵尸是否免疫冰冻效果（如冰车僵尸）
        if hasattr(zombie, 'is_ice_immune') and zombie.is_ice_immune:
            # 免疫冰冻的僵尸只受伤害，不受减速效果
            return

        # 应用冰冻效果（如果僵尸还活着且不免疫）
        if zombie.health > 0:
            current_time = pygame.time.get_ticks()

            # 如果僵尸已经被冰冻，重置冰冻计时器
            if getattr(zombie, 'is_frozen', False):
                zombie.freeze_start_time = current_time
            else:
                # 首次冰冻
                zombie.is_frozen = True
                zombie.freeze_start_time = current_time

                # 保存原始速度并减慢移动
                if not hasattr(zombie, 'original_speed'):
                    zombie.original_speed = zombie.speed
                zombie.speed = zombie.original_speed * 0.5  # 速度减半

    def _draw_bullet(self, surface, x, y):
        """绘制冰子弹"""
        # 尝试使用寒冰子弹图片
        ice_img = self.images.get('ice_bullet_img') if self.images else None
        if ice_img:
            # 如果有专门的寒冰子弹图片
            surface.blit(ice_img, (x - 10, y - 10))
        else:
            # 没有图片时使用蓝色水晶形状
            # 绘制主体（蓝色圆圈）
            pygame.draw.circle(surface, (100, 200, 255), (x, y), 6)
            # 绘制内部高光
            pygame.draw.circle(surface, (200, 230, 255), (x - 1, y - 1), 3)
            # 绘制冰晶效果（小的闪烁点）
            for i in range(4):
                angle = i * math.pi / 2
                sparkle_x = x + int(math.cos(angle) * 8)
                sparkle_y = y + int(math.sin(angle) * 8)
                pygame.draw.circle(surface, (255, 255, 255), (sparkle_x, sparkle_y), 1)