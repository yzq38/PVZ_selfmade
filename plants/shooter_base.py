"""
射击型植物基类
"""
import random
from .base_plant import BasePlant


class ShooterPlant(BasePlant):
    """射击型植物的基类"""

    def __init__(self, row, col, plant_type, constants, images, level_manager, base_shoot_delay=60):
        super().__init__(row, col, plant_type, constants, images, level_manager)

        # 射击参数
        self.base_shoot_delay = base_shoot_delay

        # 当前实际使用的射击间隔（带随机波动和关卡加成）
        self.current_shoot_delay = self._calculate_random_delay()

        # 设置随机初始值，避免所有植物同时攻击
        self.shoot_timer = random.randint(0, self.current_shoot_delay)

        # 用于检测新僵尸波次的变量
        self.had_target_last_frame = False

    def _calculate_random_delay(self):
        """计算带有随机波动和关卡加成的射击间隔"""
        if self.plant_type not in ["shooter", "melon_pult", "cattail", "dandelion", "lightning_flower", "ice_cactus","moon_flower","psychedelic_pitcher"]:
            return self.base_shoot_delay

        # 获取关卡射速倍率
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 应用射速倍率（倍率越高，间隔越短）
        adjusted_delay = int(self.base_shoot_delay / speed_multiplier)

        # 根据植物类型设置不同的波动范围
        variation_percent = self._get_variation_percent()
        variation = int(adjusted_delay * variation_percent)

        return adjusted_delay + random.randint(-variation, variation)

    def _get_variation_percent(self):
        """获取射击间隔的波动百分比"""
        if self.plant_type in ["cattail","moon_flower"]:
            return 0.05  # ±5%
        elif self.plant_type in ["melon_pult", "dandelion", "lightning_flower", "ice_cactus","psychedelic_pitcher"]:
            return 0.08  # ±8%
        else:  # shooter
            return 0.1  # ±10%

    def update(self):
        """更新射击计时器"""
        # 速度倍率支持
        speed_multiplier = 1.0
        if self.level_manager and self.level_manager.has_plant_speed_boost():
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()

        # 速度倍率越高，计时器增加越快
        self.shoot_timer += speed_multiplier
        return 0

    def check_for_new_wave(self, has_target_now):
        """检测是否有新僵尸波次出现，并添加随机延时"""
        # 如果之前没有目标，现在有了目标，说明新一波僵尸出现
        if not self.had_target_last_frame and has_target_now:
            current_base_delay = self._get_current_base_delay()

            # 添加0-15%的随机延时
            max_delay = int(current_base_delay * 0.15)
            extra_delay = random.randint(0, max_delay)

            if self.shoot_timer >= self.current_shoot_delay:
                self.shoot_timer = self.current_shoot_delay - extra_delay

        self.had_target_last_frame = has_target_now

    def _get_current_base_delay(self):
        """获取当前的基础射击间隔（考虑关卡加成）"""
        if self.level_manager and self.level_manager.has_special_feature('plant_speed_boost'):
            speed_multiplier = self.level_manager.get_plant_speed_multiplier()
            return int(self.base_shoot_delay / speed_multiplier)
        return self.base_shoot_delay

    def can_shoot(self):
        """检查是否可以射击"""
        return self.shoot_timer >= self.current_shoot_delay

    def reset_shoot_timer(self):
        """重置射击计时器并重新计算随机射击间隔"""
        self.shoot_timer = 0
        self.current_shoot_delay = self._calculate_random_delay()


def has_zombie_in_row_ahead_with_portal(plant, zombies, portal_manager):
    """
    检测植物前方是否有僵尸，考虑传送门穿越逻辑

    Args:
        plant: 植物对象
        zombies: 僵尸列表
        portal_manager: 传送门管理器

    Returns:
        bool: 是否有可攻击的僵尸
    """
    if not portal_manager:
        # 没有传送门管理器，使用普通逻辑
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    # 检查植物所在行是否有传送门
    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        # 植物所在行没有传送门，使用普通逻辑
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    # 找到植物右侧最近的传送门
    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        # 植物右侧没有传送门，使用普通逻辑
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    # 检查传送门左侧是否有僵尸（传送门左侧的僵尸可以正常攻击）
    has_zombie_before_portal = _has_zombie_between_positions(
        zombies, plant.row, plant.col, nearest_portal.col
    )

    if has_zombie_before_portal:
        return True

    # 检查其他传送门出口是否有僵尸
    return _has_zombie_at_portal_exits(zombies, portal_manager, nearest_portal)


def find_nearest_zombie_with_portal(plant, zombies, portal_manager):
    """
    寻找最近的僵尸，考虑传送门穿越逻辑

    Args:
        plant: 植物对象
        zombies: 僵尸列表
        portal_manager: 传送门管理器

    Returns:
        zombie or None: 最近的僵尸对象
    """
    if not portal_manager:
        return _find_nearest_zombie_normal(plant, zombies)

    # 检查植物所在行是否有传送门
    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        return _find_nearest_zombie_normal(plant, zombies)

    # 找到植物右侧最近的传送门
    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        return _find_nearest_zombie_normal(plant, zombies)

    # 首先检查传送门左侧的僵尸（优先攻击，因为不需要穿越传送门）
    nearest_before_portal = _find_nearest_zombie_between_positions(
        zombies, plant.row, plant.col, nearest_portal.col
    )

    if nearest_before_portal:
        return nearest_before_portal

    # 如果传送门左侧没有僵尸，寻找其他传送门出口的僵尸
    return _find_nearest_zombie_at_portal_exits(zombies, portal_manager, nearest_portal)


def get_bullet_target_col_with_portal(plant, zombies, portal_manager):
    """
    获取子弹目标列位置，考虑传送门穿越

    Args:
        plant: 植物对象
        zombies: 僵尸列表
        portal_manager: 传送门管理器

    Returns:
        float: 目标列位置
    """
    target_zombie = find_nearest_zombie_with_portal(plant, zombies, portal_manager)

    if target_zombie:
        # 检查目标僵尸是否在传送门出口
        if _is_zombie_at_portal_exit(target_zombie, plant, portal_manager):
            # 如果目标在传送门出口，子弹应该射向植物所在行的传送门
            plant_row_portals = _get_portals_in_row(portal_manager, plant.row)
            nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)
            if nearest_portal:
                return float(nearest_portal.col)

        return target_zombie.col

    # 默认目标位置
    return 9.0  # GRID_WIDTH


# ==================== 辅助函数 ====================

def _get_portals_in_row(portal_manager, row):
    """获取指定行的所有活跃传送门"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return []

    return [portal for portal in portal_manager.portals
            if portal.row == row and portal.is_active]


def _find_nearest_portal_to_right(plant, portals):
    """找到植物右侧最近的传送门"""
    nearest_portal = None
    min_distance = float('inf')

    for portal in portals:
        if portal.col > plant.col:  # 传送门在植物右侧
            distance = portal.col - plant.col
            if distance < min_distance:
                min_distance = distance
                nearest_portal = portal

    return nearest_portal


def _has_zombie_in_row_ahead_normal(plant, zombies):
    """普通的前方僵尸检测逻辑"""
    for zombie in zombies:
        if zombie.row == plant.row and zombie.col > plant.col:
            return True
    return False


def _find_nearest_zombie_normal(plant, zombies):
    """普通的最近僵尸寻找逻辑"""
    nearest_zombie = None
    min_distance = float('inf')

    for zombie in zombies:
        if zombie.row == plant.row and zombie.col > plant.col:
            distance = zombie.col - plant.col
            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

    return nearest_zombie


def _has_zombie_between_positions(zombies, row, start_col, end_col):
    """检查指定位置范围内是否有僵尸"""
    for zombie in zombies:
        if (zombie.row == row and
                start_col < zombie.col < end_col):
            return True
    return False


def _find_nearest_zombie_between_positions(zombies, row, start_col, end_col):
    """寻找指定位置范围内最近的僵尸"""
    nearest_zombie = None
    min_distance = float('inf')

    for zombie in zombies:
        if (zombie.row == row and
                start_col < zombie.col < end_col):
            distance = zombie.col - start_col
            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

    return nearest_zombie


def _has_zombie_at_portal_exits(zombies, portal_manager, source_portal):
    """检查其他传送门出口是否有僵尸"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return False

    # 获取所有其他活跃的传送门作为可能的出口
    exit_portals = [portal for portal in portal_manager.portals
                    if (portal.is_active and
                        portal != source_portal)]

    for exit_portal in exit_portals:
        # 检查每个出口传送门所在行的右侧是否有僵尸
        for zombie in zombies:
            if (zombie.row == exit_portal.row and
                    zombie.col > exit_portal.col):
                return True

    return False


def _find_nearest_zombie_at_portal_exits(zombies, portal_manager, source_portal):
    """寻找其他传送门出口最近的僵尸"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return None

    # 获取所有其他活跃的传送门作为可能的出口
    exit_portals = [portal for portal in portal_manager.portals
                    if (portal.is_active and
                        portal != source_portal)]

    nearest_zombie = None
    min_total_distance = float('inf')

    for exit_portal in exit_portals:
        # 在每个出口传送门所在行寻找最近的僵尸
        for zombie in zombies:
            if (zombie.row == exit_portal.row and
                    zombie.col > exit_portal.col):

                # 计算总距离（传送门距离可以忽略，主要考虑僵尸距传送门的距离）
                distance_from_exit = zombie.col - exit_portal.col

                if distance_from_exit < min_total_distance:
                    min_total_distance = distance_from_exit
                    nearest_zombie = zombie

    return nearest_zombie


def _is_zombie_at_portal_exit(zombie, plant, portal_manager):
    """检查僵尸是否位于传送门出口（相对于植物的传送门系统）"""
    if not portal_manager:
        return False

    # 获取植物所在行的传送门
    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        return False

    # 找到植物右侧的传送门
    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        return False

    # 检查僵尸是否在其他传送门的出口行
    exit_portals = [portal for portal in portal_manager.portals
                    if (portal.is_active and
                        portal != nearest_portal)]

    for exit_portal in exit_portals:
        if zombie.row == exit_portal.row:
            return True

    return False