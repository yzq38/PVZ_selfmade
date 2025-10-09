"""
爆炸僵尸类 - 支持魅惑状态图片翻转
"""
import pygame
import math
from .base_zombie import BaseZombie


class ExplodingZombieDeathHandler:
    """处理爆炸僵尸死亡时的特殊逻辑"""

    @staticmethod
    def mark_explosion_death(zombies, explosion_area):
        """标记被爆炸杀死的僵尸，防止连锁爆炸"""
        for zombie in zombies:
            if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                zombie_row = zombie.row
                zombie_col = int(zombie.col)
                if (zombie_row, zombie_col) in explosion_area:
                    # 标记这个爆炸僵尸被爆炸杀死
                    zombie.death_by_explosion = True


class ExplodingZombie(BaseZombie):
    """爆炸僵尸实现 - 死亡时会爆炸，支持魅惑状态图片翻转"""

    def __init__(self, row, has_armor_prob=0.3, is_fast=False, wave_mode=False,
                 fast_multiplier=2.5, constants=None, sounds=None, images=None,
                 level_settings=None):
        # 设置爆炸僵尸的基础属性
        self.health = 500
        self.max_health = 500
        self.base_speed = 0.007  # 普通僵尸速度的2倍
        self.attack_dmg = 0.5
        self.size_multiplier = 1.0

        # 爆炸相关属性
        self.explosion_damage = 1500  # 爆炸伤害
        self.explosion_radius = 1.6  # 爆炸半径（格子数）
        self.has_exploded = False
        self.explosion_triggered = False
        self.explosion_timer = 0
        self.explosion_delay = 15  # 爆炸延迟（0.25秒）
        self.death_by_explosion = False  # 标记是否被爆炸性伤害杀死

        # 调用父类构造函数
        super().__init__(row, has_armor_prob, is_fast, wave_mode, fast_multiplier,
                         constants, sounds, images, level_settings, "exploding")

        # 爆炸僵尸不会有护甲
        self.has_armor = False
        self.armor_health = 0
        self.max_armor_health = 0

    def take_damage_from_explosion(self):
        """标记受到爆炸性伤害"""
        self.death_by_explosion = True

    def start_death_animation(self):
        """重写死亡动画开始方法，触发爆炸"""
        if not self.is_dying and not self.death_by_explosion:
            # 如果不是被爆炸杀死，触发自爆
            self.explosion_triggered = True
            self.explosion_timer = self.explosion_delay

        # 调用父类的死亡动画
        super().start_death_animation()

    def get_explosion_area(self):
        """获取爆炸影响的格子区域 - 修改为圆形范围"""
        explosion_area = []

        # 爆炸中心位置（僵尸的精确位置）
        explosion_center_row = self.row
        explosion_center_col = self.col

        # 计算可能受影响的格子范围（扩大搜索范围以确保不遗漏）
        search_radius = int(self.explosion_radius) + 1
        min_row = max(0, int(explosion_center_row - search_radius))
        max_row = min(4, int(explosion_center_row + search_radius))  # 战场有5行（0-4）
        min_col = max(0, int(explosion_center_col - search_radius))
        max_col = min(8, int(explosion_center_col + search_radius))  # 战场有9列（0-8）

        # 遍历搜索范围内的所有格子
        for target_row in range(min_row, max_row + 1):
            for target_col in range(min_col, max_col + 1):
                # 计算格子中心点到爆炸中心的距离
                grid_center_row = target_row + 0.5  # 格子中心的行坐标
                grid_center_col = target_col + 0.5  # 格子中心的列坐标

                # 计算欧几里得距离
                distance = math.sqrt(
                    (grid_center_row - explosion_center_row) ** 2 +
                    (grid_center_col - explosion_center_col) ** 2
                )

                # 如果距离在爆炸半径内，则包含这个格子
                if distance <= self.explosion_radius:
                    explosion_area.append((target_row, target_col))

        return explosion_area

    def update(self, plants):
        """更新爆炸僵尸状态"""
        # 如果正在爆炸倒计时
        if self.explosion_triggered and not self.has_exploded:
            self.explosion_timer -= 1
            if self.explosion_timer <= 0:
                self.explode(plants)

        # 调用父类更新
        super().update(plants)

    def explode(self, plants, zombies=None):
        """执行爆炸 - 修复：可以攻击敌对僵尸"""
        if self.has_exploded:
            return

        self.has_exploded = True

        # 获取爆炸范围
        explosion_area = self.get_explosion_area()

        # 确定当前僵尸的阵营
        current_team = getattr(self, 'team', 'zombie')

        # 对范围内的植物造成伤害（如果是敌对阵营）
        if current_team == 'zombie':  # 普通僵尸，攻击植物
            for plant in plants:
                if (plant.row, plant.col) in explosion_area:
                    plant.take_damage(self.explosion_damage)

        # 对范围内的敌对僵尸造成伤害
        if zombies:
            for zombie in zombies:
                if zombie == self:  # 跳过自己
                    continue

                zombie_team = getattr(zombie, 'team', 'zombie')

                # 只攻击不同阵营的僵尸
                if zombie_team != current_team:
                    zombie_row = zombie.row
                    zombie_col = int(zombie.col)

                    if (zombie_row, zombie_col) in explosion_area:
                        # 标记被爆炸性伤害杀死（防止连锁爆炸）
                        if hasattr(zombie, 'take_damage_from_explosion'):
                            zombie.take_damage_from_explosion()

                        # 造成爆炸伤害
                        zombie.health -= self.explosion_damage

                        # 检查是否死亡
                        if zombie.health <= 0 and not zombie.is_dying:
                            zombie.start_death_animation()

        # 播放爆炸音效
        if self.sounds and self.sounds.get("explosion"):
            self.sounds["explosion"].play()
        elif self.sounds and self.sounds.get("cherry_explosion"):
            self.sounds["cherry_explosion"].play()

    def _update_attack_logic(self, plants):
        """爆炸僵尸的攻击逻辑（与普通僵尸相同）- 修复版本"""
        # 如果被魅惑，不攻击植物
        if hasattr(self, 'is_charmed') and self.is_charmed:
            # 魅惑僵尸向右移动，不攻击植物
            if not self.is_attacking:  # 如果没在和其他僵尸战斗
                self.col += abs(self.speed)
            return

        # 先检测是否碰撞植物（同列同排）
        plant_collision = False
        attacking_plant = None

        for plant in plants:
            if plant.row == self.row and abs(self.col - plant.col) < 0.5:
                plant_collision = True
                attacking_plant = plant
                break

        # 根据碰撞情况决定行为
        if plant_collision:
            # 碰到植物，停下攻击
            self.is_attacking = True

            # 攻击植物
            if attacking_plant:
                # 使用植物的 take_damage 方法
                attacking_plant.take_damage(self.attack_dmg)

                # 控制啃咬音效播放
                bite_interval = self.constants.get('BITE_INTERVAL', 30)
                self.bite_timer += 1
                if self.bite_timer >= bite_interval:
                    if self.sounds and self.sounds.get("bite"):
                        self.sounds["bite"].play()
                    self.bite_timer = 0

                # 检查植物是否死亡
                if not attacking_plant.is_alive():
                    plants.remove(attacking_plant)
                    # 植物死亡后，僵尸可以继续移动
                    self.is_attacking = False
        else:
            # 没有碰撞植物，继续移动
            self.is_attacking = False
            self.bite_timer = 0

            # 确保速度是负的（向左）
            if self.speed > 0:
                self.speed = -abs(self.speed)
            self.col -= abs(self.speed)

    def _draw_zombie_body(self, surface, x, y, base_x, base_y, actual_size):
        """绘制爆炸僵尸本体（红色覆盖层）- 支持魅惑状态图片翻转"""
        # 如果正在爆炸倒计时，添加闪烁效果
        if self.explosion_triggered and not self.has_exploded:
            # 闪烁效果
            if self.explosion_timer % 10 < 5:  # 每10帧闪烁一次
                flash_surface = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 0, 100))  # 黄色闪烁
                surface.blit(flash_surface, (x, y))

        zombie_img = self._get_zombie_image('zombie_img')

        if zombie_img:
            # 先绘制原图
            surface.blit(zombie_img, (base_x, base_y))

            # 爆炸僵尸的红色覆盖层（始终绘制）
            red_overlay = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 80))  # 半透明红色
            surface.blit(red_overlay, (x, y))

            # 处理特殊状态效果（在红色覆盖层之上）
            if hasattr(self, 'is_frozen') and self.is_frozen:
                # 冰冻效果：使用更轻的蓝色，让红色能透出来
                ice_overlay = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
                # 降低蓝色的不透明度，让红色和蓝色混合成紫红色效果
                ice_overlay.fill((70, 130, 180, 60))  # 降低透明度从120到60
                surface.blit(ice_overlay, (x, y))
                # 冰晶效果
                self._draw_ice_crystals(surface, x, y, actual_size)
            elif self.is_stunned:
                # 眩晕效果：黄色闪光
                stun_overlay = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
                stun_overlay.fill((255, 255, 0, 60))  # 半透明黄色
                surface.blit(stun_overlay, (x, y))
        else:
            # 没有图片时使用红色矩形作为基础
            base_color = (200, 0, 0)  # 深红色作为爆炸僵尸的基础色

            # 根据状态修改颜色
            if hasattr(self, 'is_frozen') and self.is_frozen:
                # 冰冻的爆炸僵尸：紫红色（红色+蓝色混合）
                base_color = (135, 65, 90)  # 紫红色
            elif self.is_stunned:
                # 眩晕的爆炸僵尸：橙红色（红色+黄色混合）
                base_color = (255, 128, 0)  # 橙红色

            pygame.draw.rect(surface, base_color, (x, y, actual_size, actual_size))

    def _draw_zombie_to_surface(self, surface, x, y, actual_size):
        """将爆炸僵尸绘制到指定surface（用于死亡动画）- 支持魅惑状态图片翻转"""
        zombie_img = self._get_zombie_image('zombie_img')

        if zombie_img:
            surface.blit(zombie_img, (x, y))
            # 添加红色覆盖层
            red_overlay = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 80))
            surface.blit(red_overlay, (x, y))
        else:
            color = (200, 0, 0)  # 深红色
            pygame.draw.rect(surface, color, (x, y, actual_size, actual_size))

    def draw(self, surface):
        """重写绘制方法以添加爆炸倒计时指示器"""
        # 调用父类的绘制方法
        super().draw(surface)

        # 如果正在爆炸倒计时，显示警告圆圈
        if self.explosion_triggered and not self.has_exploded and self.constants:
            # 计算僵尸中心位置
            center_x = (self.constants['BATTLEFIELD_LEFT'] +
                        self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                        self.constants['GRID_SIZE'] // 2)
            center_y = (self.constants['BATTLEFIELD_TOP'] +
                        self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                        self.constants['GRID_SIZE'] // 2)

            # 绘制圆形警告范围指示器
            if self.explosion_timer < 20:  # 最后20帧显示警告圆圈
                # 计算圆圈半径（基于爆炸半径1.1格子）
                grid_size = self.constants['GRID_SIZE'] + self.constants['GRID_GAP']
                warning_radius = int(self.explosion_radius * grid_size * 0.8)  # 稍微缩小一点便于观察

                # 闪烁效果
                alpha = int(127 + 100 * math.sin(self.explosion_timer * 0.5))
                pygame.draw.circle(surface, (255, 0, 0), (int(center_x), int(center_y)), warning_radius, 3)