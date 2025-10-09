"""
闪电花植物类
"""
import pygame
import random
import math
from .shooter_base import ShooterPlant


class LightningFlower(ShooterPlant):
    """闪电花：链式闪电攻击"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'lightning_flower_60',
        'display_name': '闪电花',
        'category': 'shooter',
        'preview_alpha': 130,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "lightning_flower", constants, images, level_manager, base_shoot_delay=120)

        # 闪电花特殊属性
        self.chain_damage = 60  # 首个目标伤害
        self.chain_reduction = 0.7  # 每次跳跃伤害递减
        self.max_chains = 4  # 最大跳跃次数
        self.chain_range = 3.0  # 闪电跳跃范围（格子距离）

        # 闪电视觉效果
        self.lightning_effects = []  # 存储闪电视觉效果
        self.show_lightning = False
        self.lightning_timer = 0
        self.lightning_duration = 15

    def update(self):
        """更新闪电花状态"""
        # 速度倍率支持
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 速度倍率越高，计时器增加越快
        self.shoot_timer += speed_multiplier

        # 更新闪电视觉效果
        self.update_lightning_effects()

        return 0

    def perform_lightning_attack(self, zombies_list, sounds=None):
        """执行闪电链式攻击 - 修复：排除魅惑僵尸"""
        if not zombies_list:
            return 0

        # 找到同行最近的僵尸作为起始目标
        initial_target = None
        min_distance = float('inf')

        for zombie in zombies_list:
            # *** 关键修复：跳过魅惑僵尸 ***
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

            if zombie.row == self.row and zombie.col > self.col and zombie.health > 0:
                distance = zombie.col - self.col
                if distance < min_distance:
                    min_distance = distance
                    initial_target = zombie

        if not initial_target:
            return 0

        # 开始链式攻击
        chain_targets = []
        current_target = initial_target
        current_damage = self.chain_damage
        zombies_hit = 0

        # 清空之前的闪电效果
        self.lightning_effects.clear()

        for chain_count in range(self.max_chains):
            if not current_target or current_target.health <= 0:
                break

            # *** 再次确认当前目标不是魅惑僵尸 ***
            if hasattr(current_target, 'is_charmed') and current_target.is_charmed:
                break
            if hasattr(current_target, 'team') and current_target.team == "plant":
                break

            # 记录攻击目标和伤害
            chain_targets.append({
                'zombie': current_target,
                'damage': int(current_damage),
                'chain_index': chain_count
            })

            # 对当前目标造成伤害
            old_health = current_target.health
            if current_target.has_armor and current_target.armor_health > 0:
                current_target.armor_health -= int(current_damage)
                if current_target.armor_health < 0:
                    current_target.health += current_target.armor_health
                    current_target.armor_health = 0
            else:
                current_target.health -= int(current_damage)

            current_target.health = max(0, current_target.health)
            zombies_hit += 1

            # 检查僵尸是否需要开始死亡动画
            if current_target.health <= 0 and not current_target.is_dying:
                if hasattr(current_target, 'zombie_type') and current_target.zombie_type == "exploding":
                    if not hasattr(current_target, 'death_by_explosion'):
                        current_target.death_by_explosion = False
                    if not current_target.death_by_explosion:
                        current_target.explosion_triggered = True
                        current_target.explosion_timer = current_target.explosion_delay
                current_target.start_death_animation()

            # 创建闪电视觉效果
            self.create_lightning_effect(self.row, self.col, current_target.row, current_target.col)

            # 寻找下一个跳跃目标
            next_target = self.find_next_lightning_target(current_target, zombies_list, chain_targets)
            if not next_target:
                break

            # 如果有下一个目标，创建跳跃闪电效果
            if next_target:
                self.create_lightning_effect(current_target.row, current_target.col,
                                             next_target.row, next_target.col)

            # 更新伤害和目标
            current_damage *= self.chain_reduction
            current_target = next_target

        # 激活闪电视觉效果
        if self.lightning_effects:
            self.show_lightning = True
            self.lightning_timer = 0

            # 播放闪电音效
            if sounds and sounds.get("lightning_attack"):
                sounds["lightning_attack"].play()

        return zombies_hit

    def find_next_lightning_target(self, current_zombie, zombies_list, chain_targets):
        """寻找下一个闪电跳跃目标 - 修复：排除魅惑僵尸"""
        hit_zombies = {target['zombie'] for target in chain_targets}
        next_target = None
        min_distance = float('inf')

        for zombie in zombies_list:
            if (zombie in hit_zombies or zombie.health <= 0 or
                    zombie.is_dying or zombie == current_zombie):
                continue

            # *** 关键修复：跳过魅惑僵尸 ***
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

            # 计算距离
            dx = zombie.col - current_zombie.col
            dy = zombie.row - current_zombie.row
            distance = (dx * dx + dy * dy) ** 0.5

            # 在跳跃范围内且是最近的
            if distance <= self.chain_range and distance < min_distance:
                min_distance = distance
                next_target = zombie

        return next_target


    def create_lightning_effect(self, start_row, start_col, end_row, end_col):
        """创建闪电视觉效果"""
        effect = {
            'start_row': start_row,
            'start_col': start_col,
            'end_row': end_row,
            'end_col': end_col,
            'intensity': 255,
            'flicker_timer': 0,
            'segments': self.generate_lightning_segments(start_row, start_col, end_row, end_col)
        }
        self.lightning_effects.append(effect)

    def generate_lightning_segments(self, start_row, start_col, end_row, end_col):
        """生成闪电的锯齿形路径"""
        segments = []
        num_segments = max(3, int(abs(end_col - start_col) + abs(end_row - start_row)) * 2)

        for i in range(num_segments + 1):
            t = i / num_segments

            # 基础直线插值
            base_row = start_row + (end_row - start_row) * t
            base_col = start_col + (end_col - start_col) * t

            # 添加随机偏移创建锯齿效果
            if i > 0 and i < num_segments:
                offset_row = random.uniform(-0.3, 0.3)
                offset_col = random.uniform(-0.2, 0.2)
                base_row += offset_row
                base_col += offset_col

            segments.append((base_row, base_col))

        return segments

    def update_lightning_effects(self):
        """更新闪电视觉效果"""
        if not self.show_lightning:
            return

        self.lightning_timer += 1

        # 更新闪电效果
        for effect in self.lightning_effects:
            effect['flicker_timer'] += 1
            # 闪烁效果
            if effect['flicker_timer'] % 4 == 0:
                effect['intensity'] = random.randint(200, 255)

            # 逐渐消失
            fade_progress = self.lightning_timer / self.lightning_duration
            effect['intensity'] = int(255 * (1 - fade_progress))

        # 结束闪电效果
        if self.lightning_timer >= self.lightning_duration:
            self.show_lightning = False
            self.lightning_effects.clear()
            self.lightning_timer = 0

    def draw(self, surface):
        """绘制闪电花"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        # 闪电花可能有充电效果
        if self.show_lightning:
            # 绘制发光效果
            glow_surface = pygame.Surface((self.constants['GRID_SIZE'] + 20,
                                           self.constants['GRID_SIZE'] + 20), pygame.SRCALPHA)
            glow_color = (255, 255, 0, 100)  # 半透明黄色发光
            pygame.draw.circle(glow_surface, glow_color,
                               (glow_surface.get_width() // 2, glow_surface.get_height() // 2),
                               self.constants['GRID_SIZE'] // 2 + 10)
            surface.blit(glow_surface, (x - 10, y - 10))

        if self.images and self.images.get('lightning_flower_img'):
            surface.blit(self.images['lightning_flower_img'], (x, y))
        else:
            # 默认黄色圆形
            pygame.draw.circle(surface, (255, 255, 0),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

        # 绘制闪电效果
        self.draw_lightning_effects(surface)

        # 绘制血条
        self._draw_health_bar(surface, x, y)

    def draw_lightning_effects(self, surface):
        """绘制闪电效果"""
        if not self.show_lightning or not self.constants:
            return

        for effect in self.lightning_effects:
            alpha = max(0, effect['intensity'])
            if alpha < 10:
                continue

            # 绘制闪电路径
            segments = effect['segments']
            if len(segments) < 2:
                continue

            # 转换为屏幕坐标
            screen_points = []
            for row, col in segments:
                screen_x = (self.constants['BATTLEFIELD_LEFT'] +
                            col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                            self.constants['GRID_SIZE'] // 2)
                screen_y = (self.constants['BATTLEFIELD_TOP'] +
                            row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                            self.constants['GRID_SIZE'] // 2)
                screen_points.append((int(screen_x), int(screen_y)))

            # 绘制主闪电（黄色）
            if len(screen_points) >= 2:
                pygame.draw.lines(surface, (255, 255, 0, alpha), False, screen_points, 3)
                # 内部高光（白色）
                pygame.draw.lines(surface, (255, 255, 255, alpha // 2), False, screen_points, 1)