"""
地刺植物类 - 第24关新增植物
"""
import pygame
from .shooter_base import ShooterPlant


class Luker(ShooterPlant):
    """地刺：地面防守植物，无视僵尸防具，可秒杀车子类僵尸"""

    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'luker_60',
        'display_name': '地刺',
        'category': 'shooter',
        'preview_alpha': 130,
    }

    def __init__(self, row, col, constants, images, level_manager):
        # 攻速为豌豆的0.75，豌豆基础延迟约60帧，地刺为80帧
        super().__init__(row, col, "luker", constants, images, level_manager, base_shoot_delay=80)

        # 地刺特殊属性
        self.damage = 20  # 基础伤害
        self.can_ignore_armor = True  # 无视防具
        self.can_instant_kill_vehicles = True  # 可秒杀车子类僵尸

        # 地刺血量较低，但有特殊能力
        self.health = 150
        self.max_health = 150

    def can_shoot(self):
        """地刺只在有僵尸踩在自己身上时才攻击"""
        # 修复：使用基类的射击计时器检查方法
        return self.shoot_timer >= self.current_shoot_delay

    def is_zombie_on_luker(self, zombie):
        """检查僵尸是否踩在地刺上"""
        if zombie.row != self.row:
            return False

        # 检查僵尸的位置是否与地刺重叠
        zombie_left = zombie.col
        zombie_right = zombie.col + getattr(zombie, 'size_multiplier', 1.0)
        luker_left = self.col
        luker_right = self.col + 1

        # 检查重叠
        return not (zombie_right <= luker_left or zombie_left >= luker_right)

    def can_instant_kill_zombie(self, zombie):
        """检查是否可以秒杀僵尸（车子类）"""
        if not self.can_instant_kill_vehicles:
            return False

        # 检查是否为车子类僵尸（需要根据实际僵尸类型判断）
        vehicle_types = ['ice_car', 'truck_zombie', 'vehicle']  # 可根据实际情况调整
        return hasattr(zombie, 'zombie_type') and zombie.zombie_type in vehicle_types

    def is_visible_to_zombie(self, zombie):
        """
        检查地刺是否对指定僵尸可见
        地刺的隐形逻辑：
        - 对普通僵尸、爆炸僵尸等完全隐形
        - 对巨人僵尸和车类僵尸可见（可以被攻击）
        """
        # 检查僵尸类型
        zombie_type = getattr(zombie, 'zombie_type', 'normal')

        # 巨人僵尸可以看见并攻击地刺
        if zombie_type == 'giant':
            return True

        # 车类僵尸可以看见并攻击地刺
        vehicle_types = ['ice_car', 'truck_zombie', 'vehicle']
        if zombie_type in vehicle_types:
            return True

        # 其他僵尸类型（普通僵尸、爆炸僵尸等）看不见地刺
        return False

    def attack_zombie_on_position(self, zombies, sounds=None):
        """
        攻击踩在地刺上的僵尸
        特殊规则：如果是冰车僵尸，秒杀所有在该位置的冰车僵尸，地刺也消失
        """
        if not self.can_shoot():
            return False

        # 收集所有在该位置的僵尸
        zombies_on_position = []
        ice_cars_on_position = []
        has_ice_car = False

        for zombie in zombies:
            # 跳过魅惑僵尸
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

            # 检查僵尸是否踩在地刺上
            if self.is_zombie_on_luker(zombie):
                zombies_on_position.append(zombie)

                # 检查是否为冰车僵尸
                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car":
                    ice_cars_on_position.append(zombie)
                    has_ice_car = True

        # 如果有冰车僵尸，执行特殊交互
        if has_ice_car:
            # 秒杀所有在该位置的冰车僵尸
            for ice_car in ice_cars_on_position:
                if not ice_car.is_dying:
                    # 立即将冰车血量归零
                    ice_car.health = 0
                    ice_car.start_death_animation()

                    # 播放爆炸音效
                    if sounds and sounds.get("cherry_explosion"):
                        sounds["cherry_explosion"].play()
                        break  # 只播放一次音效

            # 地刺自身也被破坏
            self.health = 0

            # 重置射击计时器（虽然马上要被移除）
            self.reset_shoot_timer()

            print(f"地刺与{len(ice_cars_on_position)}辆冰车同归于尽！")
            return True

        # 如果没有冰车僵尸，执行普通攻击
        attacked = False
        for zombie in zombies_on_position:
            # 检查是否可以秒杀（其他车子类僵尸）
            if self.can_instant_kill_zombie(zombie):
                # 秒杀车子类僵尸
                zombie.health = 0
                if not zombie.is_dying:
                    # 添加爆炸僵尸的特殊处理
                    if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                        if not hasattr(zombie, 'death_by_explosion'):
                            zombie.death_by_explosion = False
                        if not zombie.death_by_explosion:
                            zombie.explosion_triggered = True
                            zombie.explosion_timer = zombie.explosion_delay
                    zombie.start_death_animation()
                attacked = True
            else:
                # 普通攻击
                if self.can_ignore_armor:
                    # 无视防具，直接扣血
                    zombie.health -= self.damage
                else:
                    # 正常攻击（虽然地刺设定是无视防具）
                    if zombie.has_armor and zombie.armor_health > 0:
                        armor_damage = min(self.damage, zombie.armor_health)
                        zombie.armor_health -= armor_damage
                        remaining_damage = self.damage - armor_damage
                        if remaining_damage > 0:
                            zombie.health -= remaining_damage
                    else:
                        zombie.health -= self.damage

                # 检查僵尸是否死亡
                if zombie.health <= 0 and not zombie.is_dying:
                    # 添加爆炸僵尸的特殊处理
                    if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                        if not hasattr(zombie, 'death_by_explosion'):
                            zombie.death_by_explosion = False
                        if not zombie.death_by_explosion:
                            zombie.explosion_triggered = True
                            zombie.explosion_timer = zombie.explosion_delay
                    zombie.start_death_animation()

                attacked = True

            # 播放攻击音效
            if sounds and attacked:
                if sounds.get("zombie_hit"):
                    sounds["zombie_hit"].play()
                    break  # 只播放一次音效

        if attacked:
            self.reset_shoot_timer()

        return attacked

    def draw(self, surface):
        """绘制地刺 - 仅占格子底部三分之一"""
        if not self.constants:
            return

        grid_size = self.constants['GRID_SIZE']
        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (grid_size + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (grid_size + self.constants['GRID_GAP'])

        if self.images and self.images.get('luker_img'):
            # 将地刺图片绘制在格子底部三分之一的位置
            # 计算绘制位置：y坐标向下偏移到底部三分之一处
            luker_y_offset = y + (grid_size * 2 // 3)  # 底部三分之一的起始位置

            # 获取原始图片
            original_img = self.images['luker_img']

            # 缩放图片以适应底部三分之一的高度
            target_height = grid_size // 3
            target_width = grid_size  # 宽度保持与格子相同

            # 如果需要缩放图片
            if original_img.get_height() != target_height or original_img.get_width() != target_width:
                scaled_img = pygame.transform.scale(original_img, (target_width, target_height))
                surface.blit(scaled_img, (x, luker_y_offset))
            else:
                surface.blit(original_img, (x, luker_y_offset))
        else:
            # 默认深灰色尖刺形状 - 绘制在底部三分之一
            spike_color = (64, 64, 64)  # 深灰色

            # 调整中心点到格子底部三分之一的中心
            center_x = x + grid_size // 2
            center_y = y + grid_size - (grid_size // 6)  # 底部三分之一的中心

            # 缩小尖刺大小以适应底部三分之一
            spike_size = grid_size // 6  # 更小的尖刺

            # 水平尖刺
            pygame.draw.polygon(surface, spike_color, [
                (center_x - spike_size, center_y - 2),
                (center_x + spike_size, center_y - 2),
                (center_x + spike_size, center_y + 2),
                (center_x - spike_size, center_y + 2)
            ])

            # 垂直尖刺
            pygame.draw.polygon(surface, spike_color, [
                (center_x - 2, center_y - spike_size),
                (center_x + 2, center_y - spike_size),
                (center_x + 2, center_y + spike_size),
                (center_x - 2, center_y + spike_size)
            ])

            # 中心圆点
            pygame.draw.circle(surface, spike_color, (center_x, center_y), 3)

        # 绘制血条 - 保持在原位置（格子顶部）
        self._draw_health_bar(surface, x, y)