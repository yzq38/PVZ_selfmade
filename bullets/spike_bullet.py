"""
尖刺子弹类 - 具有追踪能力的智能子弹
"""
import pygame
import math
from .base_bullet import BaseBullet


class SpikeBullet(BaseBullet):
    """尖刺子弹类 - 能够追踪目标的智能子弹"""

    def __init__(self, row, col, target_zombie=None, constants=None, images=None, **kwargs):
        super().__init__(row, col, bullet_type="spike", constants=constants, images=images, **kwargs)

        # 尖刺子弹属性
        self.dmg = 40
        self.splash_dmg = 0
        self.target_zombie = target_zombie

        # 追踪子弹特有属性
        self.tracking_speed = 0.05  # 追踪子弹速度稍快
        self.direction_x = 1.0  # X方向
        self.direction_y = 0.0  # Y方向
        self.actual_x = float(col)  # 实际X坐标（浮点数）
        self.actual_y = float(row)  # 实际Y坐标（浮点数）

        # 重新锁定相关属性
        self.retargeting_cooldown = 0  # 重新锁定冷却时间，防止频繁切换目标
        self.max_retargeting_cooldown = 10  # 最大冷却时间（帧数）

        # 平滑转弯机制
        self.base_turn_rate = 0.05  # 基础转弯速率（弧度/帧）
        self.max_turn_rate = 0.4  # 最大转弯速率
        self.target_direction_x = self.direction_x  # 目标方向X
        self.target_direction_y = self.direction_y  # 目标方向Y

    def update(self, zombies_list=None):
        """更新追踪尖刺子弹，支持重新锁定，修复原地打转问题"""
        if not self.constants:
            return True

        # 更新重新锁定冷却时间
        if self.retargeting_cooldown > 0:
            self.retargeting_cooldown -= 1

        # 检查当前目标是否还有效（新增：检查魅惑状态）
        target_is_valid = (self.target_zombie and
                           self.target_zombie.health > 0 and
                           self.target_zombie in zombies_list and  # 确保目标还在僵尸列表中
                           self._is_zombie_attackable(self.target_zombie))  # 新增：检查是否可攻击

        # 如果目标无效且冷却时间已过，尝试重新锁定
        if not target_is_valid and self.retargeting_cooldown <= 0 and zombies_list:
            new_target = self._find_nearest_zombie(zombies_list)
            if new_target:
                self.target_zombie = new_target
                self.retargeting_cooldown = self.max_retargeting_cooldown
                target_is_valid = True

        # 如果有有效目标，计算目标方向
        if target_is_valid:
            # 计算到目标的方向
            target_x = self.target_zombie.col
            target_y = self.target_zombie.row

            dx = target_x - self.actual_x
            dy = target_y - self.actual_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0.1:  # 还没到达目标
                # 标准化方向向量
                self.target_direction_x = dx / distance
                self.target_direction_y = dy / distance
            else:
                # 已经很接近目标，保持当前目标方向
                pass
        else:
            # 没有有效目标的处理逻辑
            if not zombies_list or len(zombies_list) == 0:
                # 如果地图上没有僵尸了，子弹向右前进直到消失
                self.target_direction_x = 1.0
                self.target_direction_y = 0.0
            else:
                # 如果还有僵尸但暂时锁定不到，继续按当前方向前进
                # 这可以避免原地打转，让子弹有机会接近其他僵尸
                pass

        # 平滑转向目标方向
        self._smooth_turn_to_target()

        # 按当前方向移动
        self.actual_x += self.direction_x * self.tracking_speed
        self.actual_y += self.direction_y * self.tracking_speed

        # 更新网格坐标
        self.col = self.actual_x
        self.row = self.actual_y

        # 检查是否超出边界
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        grid_height = self.constants['GRID_HEIGHT'] if self.constants else 5

        # 增加边界检查的宽容度，避免子弹过早消失
        return (self.col > grid_width + 2 or self.col < -2 or
                self.row > grid_height + 2 or self.row < -2)

    def _is_zombie_attackable(self, zombie):
        """检查僵尸是否可以被攻击（排除被魅惑的僵尸）"""
        # 检查僵尸是否被魅惑
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return False
        if hasattr(zombie, 'team') and zombie.team == "plant":
            return False
        return True

    def _smooth_turn_to_target(self):
        """平滑转向目标方向，动态调整转弯速率"""
        # 计算当前方向与目标方向之间的角度差
        current_angle = math.atan2(self.direction_y, self.direction_x)
        target_angle = math.atan2(self.target_direction_y, self.target_direction_x)

        # 计算角度差（考虑圆周环绕）
        angle_diff = target_angle - current_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # 动态调整转弯速率
        abs_angle_diff = abs(angle_diff)

        # 基于角度差异的转弯速率
        if abs_angle_diff > math.pi * 2 / 3:  # 大于120度 - 急转弯
            angle_turn_rate = 0.35
        elif abs_angle_diff > math.pi / 2:  # 大于90度 - 大转弯
            angle_turn_rate = 0.25
        elif abs_angle_diff > math.pi / 3:  # 大于60度 - 中等转弯
            angle_turn_rate = 0.15
        elif abs_angle_diff > math.pi / 6:  # 大于30度 - 小转弯
            angle_turn_rate = 0.08
        else:  # 小于30度 - 微调
            angle_turn_rate = 0.03

        # 基于到目标距离的转弯速率调整
        distance_turn_rate = 1.0
        if self.target_zombie:
            distance = math.sqrt((self.target_zombie.col - self.actual_x) ** 2 +
                                 (self.target_zombie.row - self.actual_y) ** 2)

            # 距离越近，转弯越急
            if distance < 1.0:
                distance_turn_rate = 2.0  # 非常近时急转弯
            elif distance < 2.0:
                distance_turn_rate = 1.5  # 较近时加强转弯
            elif distance < 4.0:
                distance_turn_rate = 1.2  # 中等距离轻微加强
            else:
                distance_turn_rate = 1.0  # 远距离正常转弯

        # 综合转弯速率
        dynamic_turn_rate = angle_turn_rate * distance_turn_rate

        # 限制在最大转弯速率以内
        dynamic_turn_rate = min(self.max_turn_rate, dynamic_turn_rate)

        # 应用转弯限制
        if angle_diff > dynamic_turn_rate:
            angle_diff = dynamic_turn_rate
        elif angle_diff < -dynamic_turn_rate:
            angle_diff = -dynamic_turn_rate

        # 计算新的方向角度
        new_angle = current_angle + angle_diff

        # 更新方向向量
        self.direction_x = math.cos(new_angle)
        self.direction_y = math.sin(new_angle)

    def _find_nearest_zombie(self, zombies_list):
        """找到离子弹最近的有效僵尸，改进版本（排除被魅惑的僵尸）"""
        if not zombies_list:
            return None

        nearest_zombie = None
        min_distance = float('inf')

        for zombie in zombies_list:
            # 只考虑还活着的僵尸
            if zombie.health <= 0:
                continue

            # 检查僵尸是否可以被攻击（排除被魅惑的僵尸）
            if not self._is_zombie_attackable(zombie):
                continue

            # 额外检查：确保僵尸没有被标记为即将死亡（黄瓜效果）
            if hasattr(zombie, 'cucumber_marked_for_death') and zombie.cucumber_marked_for_death:
                continue

            # 计算距离
            dx = zombie.col - self.actual_x
            dy = zombie.row - self.actual_y
            distance = math.sqrt(dx * dx + dy * dy)

            # 优先选择距离较近的僵尸
            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

        return nearest_zombie

    def can_hit_zombie(self, zombie):
        """尖刺子弹的碰撞检测"""
        if zombie.is_dying:
            return False

        horizontal_distance = abs(zombie.col - self.col)
        vertical_distance = abs(zombie.row - self.row)
        return horizontal_distance < 0.6 and vertical_distance < 0.6

    def _draw_bullet(self, surface, x, y):
        """绘制尖刺子弹"""
        spike_img = self.images.get('spike_img') if self.images else None
        if spike_img:
            # 根据飞行方向旋转尖刺图片
            angle = math.degrees(math.atan2(self.direction_y, self.direction_x))
            rotated_img = pygame.transform.rotate(spike_img, -angle)
            rect = rotated_img.get_rect(center=(x, y))
            surface.blit(rotated_img, rect)
        else:
            # 没有图片时绘制简单的三角形尖刺
            size = 8
            angle_rad = math.atan2(self.direction_y, self.direction_x)
            front_x = x + math.cos(angle_rad) * size
            front_y = y + math.sin(angle_rad) * size
            left_x = x + math.cos(angle_rad + 2.5) * size * 0.7
            left_y = y + math.sin(angle_rad + 2.5) * size * 0.7
            right_x = x + math.cos(angle_rad - 2.5) * size * 0.7
            right_y = y + math.sin(angle_rad - 2.5) * size * 0.7

            points = [(front_x, front_y), (left_x, left_y), (right_x, right_y)]
            pygame.draw.polygon(surface, (128, 0, 128), points)