"""
冰道管理系统 - 处理冰车僵尸留下的冰道效果
"""
import math
import random

import pygame
import time


class IceTrail:
    """雪道段 - 静态版本"""

    def __init__(self, row, col, constants=None, images=None):
        self.row = row
        self.col = col
        self.constants = constants
        self.images = images

        # 雪道持续时间
        self.duration = 1200
        self.remaining_time = self.duration
        self.creation_time = time.time()

        # 视觉效果
        self.alpha = 200  # 透明度
        self.fade_start_time = self.duration * 0.8  # 80%时间后开始淡出

        # 生成固定的静态反光点（基于位置种子，确保每次相同）
        self.sparkles = []
        self._generate_static_sparkles()

        # 闪烁计时器
        self.sparkle_timer = 0

    def _generate_static_sparkles(self):
        """生成固定的静态反光点"""
        if not self.constants:
            return

        # 使用行列坐标作为随机种子，确保相同位置总是生成相同的反光点
        seed = self.row * 1000 + self.col
        random.seed(seed)

        grid_size = self.constants.get('GRID_SIZE', 80)
        # 每个雪道格子生成4-6个静态反光点
        num_sparkles = 5  # 固定数量

        sparkle_positions = [
            (grid_size * 0.2, grid_size * 0.3),
            (grid_size * 0.7, grid_size * 0.2),
            (grid_size * 0.4, grid_size * 0.6),
            (grid_size * 0.8, grid_size * 0.7),
            (grid_size * 0.3, grid_size * 0.8),
        ]

        for i in range(num_sparkles):
            base_x, base_y = sparkle_positions[i]
            # 添加少量随机偏移，但保持位置相对固定
            offset_range = 8
            sparkle = {
                'x': int(base_x + random.randint(-offset_range, offset_range)),
                'y': int(base_y + random.randint(-offset_range, offset_range)),
                'size': 3,  # 固定大小
                'brightness': 0.8 + random.random() * 0.2,  # 0.8-1.0之间
                'phase': random.uniform(0, 2 * math.pi),  # 初始相位
                'speed': 0.05 + random.random() * 0.03  # 很慢的闪烁速度 0.05-0.08
            }
            self.sparkles.append(sparkle)

        # 重置随机种子
        random.seed()

    def update(self):
        """更新雪道状态"""
        self.remaining_time -= 1
        self.sparkle_timer += 1

        # 淡出效果
        if self.remaining_time < self.fade_start_time:
            fade_progress = 1.0 - (self.remaining_time / self.fade_start_time)
            self.alpha = int(200 * (1.0 - fade_progress))

        # 更新缓慢的闪烁效果
        for sparkle in self.sparkles:
            sparkle['phase'] += sparkle['speed']
            if sparkle['phase'] > 2 * math.pi:
                sparkle['phase'] -= 2 * math.pi

        return self.remaining_time > 0

    def refresh(self):
        """刷新雪道持续时间（当新的冰车经过时）"""
        self.remaining_time = self.duration
        self.alpha = 200
        # 不重新生成闪烁点，保持静态

    def draw(self, surface):
        """绘制静态雪道"""
        if not self.constants:
            return

        # 计算绘制位置
        x = (self.constants['BATTLEFIELD_LEFT'] +
             self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))
        y = (self.constants['BATTLEFIELD_TOP'] +
             self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))

        grid_size = self.constants['GRID_SIZE']

        # 创建雪道表面
        snow_surface = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)

        # 绘制雪道基础层 - 纯白色
        base_snow_color = (255, 255, 255, int(self.alpha * 0.85))
        snow_surface.fill(base_snow_color)

        # 添加固定的雪道纹理图案
        self._draw_static_texture(snow_surface, grid_size)

        # 绘制缓慢闪烁的反光点
        for sparkle in self.sparkles:
            # 计算当前亮度（缓慢的正弦波闪烁）
            brightness_multiplier = (math.sin(sparkle['phase']) * 0.3 + 0.7)  # 0.4到1.0之间变化
            current_brightness = sparkle['brightness'] * brightness_multiplier

            sparkle_alpha = int(self.alpha * current_brightness * 0.6)
            if sparkle_alpha > 0:
                self._draw_sparkle(snow_surface, sparkle, sparkle_alpha)

        # 添加微妙的边框
        self._draw_border(snow_surface, grid_size)

        # 最终绘制到屏幕
        surface.blit(snow_surface, (x, y))

    def _draw_static_texture(self, snow_surface, grid_size):
        """绘制固定的雪道纹理"""
        # 使用行列坐标作为种子生成固定纹理
        seed = self.row * 1000 + self.col
        random.seed(seed)

        # 绘制固定位置的雪花点
        texture_points = []
        for i in range(12):  # 固定12个纹理点
            x_pos = random.randint(5, grid_size - 5)
            y_pos = random.randint(5, grid_size - 5)
            texture_points.append((x_pos, y_pos))

        for x_pos, y_pos in texture_points:
            # 绘制2x2的小雪花
            texture_alpha = int(self.alpha * random.uniform(0.2, 0.4))
            texture_color = (255, 255, 255, texture_alpha)

            texture_surface = pygame.Surface((2, 2), pygame.SRCALPHA)
            texture_surface.fill(texture_color)
            snow_surface.blit(texture_surface, (x_pos, y_pos))

        # 重置随机种子
        random.seed()

    def _draw_sparkle(self, snow_surface, sparkle, sparkle_alpha):
        """绘制单个反光点"""
        center_x = sparkle['x']
        center_y = sparkle['y']
        size = sparkle['size']

        # 绘制小十字形反光点（更优雅）
        # 横线
        for i in range(-size // 2, size // 2 + 1):
            px = center_x + i
            if 0 <= px < snow_surface.get_width():
                pixel_alpha = sparkle_alpha if i == 0 else sparkle_alpha // 2
                pixel_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
                pixel_surface.fill((255, 255, 255, pixel_alpha))
                snow_surface.blit(pixel_surface, (px, center_y))

        # 竖线
        for i in range(-size // 2, size // 2 + 1):
            py = center_y + i
            if 0 <= py < snow_surface.get_height():
                pixel_alpha = sparkle_alpha if i == 0 else sparkle_alpha // 2
                pixel_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
                pixel_surface.fill((255, 255, 255, pixel_alpha))
                snow_surface.blit(pixel_surface, (center_x, py))

    def _draw_border(self, snow_surface, grid_size):
        """绘制微妙的边框"""
        border_alpha = int(self.alpha * 0.3)
        border_color = (200, 200, 200, border_alpha)

        # 只绘制角落的小点作为边框装饰
        corner_size = 3
        corners = [
            (0, 0),  # 左上
            (grid_size - corner_size, 0),  # 右上
            (0, grid_size - corner_size),  # 左下
            (grid_size - corner_size, grid_size - corner_size),  # 右下
        ]

        for corner_x, corner_y in corners:
            corner_surface = pygame.Surface((corner_size, corner_size), pygame.SRCALPHA)
            corner_surface.fill(border_color)
            snow_surface.blit(corner_surface, (corner_x, corner_y))


class IceTrailManager:
    """冰道管理器"""

    def __init__(self, constants=None, images=None):
        self.constants = constants
        self.images = images
        self.ice_trails = {}  # {(row, col): IceTrail}

    def add_ice_trail(self, row, col):
        """在指定位置添加冰道"""
        trail_key = (row, col)

        if trail_key in self.ice_trails:
            # 刷新已存在的冰道
            self.ice_trails[trail_key].refresh()
        else:
            # 创建新的冰道
            self.ice_trails[trail_key] = IceTrail(row, col, self.constants, self.images)

    def update(self):
        """更新所有冰道"""
        trails_to_remove = []

        for trail_key, trail in self.ice_trails.items():
            if not trail.update():
                trails_to_remove.append(trail_key)

        # 移除过期的冰道
        for trail_key in trails_to_remove:
            del self.ice_trails[trail_key]

    def draw(self, surface):
        """绘制所有冰道"""
        for trail in self.ice_trails.values():
            trail.draw(surface)

    def has_ice_trail_at(self, row, col):
        """检查指定位置是否有冰道"""
        return (row, col) in self.ice_trails

    def get_speed_boost_for_zombie(self, zombie):
        """获取僵尸在当前位置的速度加成"""
        zombie_row = zombie.row
        zombie_col = int(round(zombie.col))

        # 检查僵尸脚下是否有冰道
        if self.has_ice_trail_at(zombie_row, zombie_col):
            return 1.5

        return 1.0  # 无加成

    def apply_speed_boost_to_zombies(self, zombies):
        """为在冰道上的僵尸应用速度加成 - 更健壮的版本"""
        for zombie in zombies:
            # 跳过冰车僵尸本身和正在死亡的僵尸
            if (hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car") or zombie.is_dying:
                continue

            speed_boost = self.get_speed_boost_for_zombie(zombie)

            # 应用速度加成
            if speed_boost > 1.0:
                # 检查是否已经在冰道上
                already_boosted = (hasattr(zombie, '_ice_trail_boosted') and
                                   zombie._ice_trail_boosted and
                                   hasattr(zombie, '_original_speed_before_ice'))

                if not already_boosted:
                    # 第一次踏上冰道或状态异常，重新保存当前速度
                    zombie._original_speed_before_ice = zombie.speed
                    zombie._ice_trail_boosted = True

                # 基于保存的原始速度应用加成
                zombie.speed = zombie._original_speed_before_ice * speed_boost

            else:
                # 离开冰道，恢复原始速度
                if hasattr(zombie, '_ice_trail_boosted') and zombie._ice_trail_boosted:
                    if hasattr(zombie, '_original_speed_before_ice'):
                        zombie.speed = zombie._original_speed_before_ice
                        del zombie._original_speed_before_ice
                    zombie._ice_trail_boosted = False

    def clear_all_trails(self):
        """清除所有冰道"""
        self.ice_trails.clear()


# 全局冰道管理器实例
_ice_trail_manager = None


def get_ice_trail_manager(constants=None, images=None):
    """获取全局冰道管理器实例"""
    global _ice_trail_manager
    if _ice_trail_manager is None:
        _ice_trail_manager = IceTrailManager(constants, images)
    return _ice_trail_manager


def add_ice_trail(game_state, row, col):
    """添加冰道到游戏状态"""
    if "ice_trail_manager" not in game_state:
        from core.constants import get_constants
        game_state["ice_trail_manager"] = IceTrailManager(
            constants=get_constants(),
            images=game_state.get("images")
        )

    game_state["ice_trail_manager"].add_ice_trail(row, col)


def update_ice_trails(game_state):
    """更新游戏中的所有冰道"""
    if "ice_trail_manager" in game_state and game_state["ice_trail_manager"]:
        ice_trail_manager = game_state["ice_trail_manager"]
        ice_trail_manager.update()

        # 为僵尸应用冰道速度加成
        if "zombies" in game_state:
            ice_trail_manager.apply_speed_boost_to_zombies(game_state["zombies"])


def draw_ice_trails(surface, game_state):
    """绘制游戏中的所有冰道"""
    if "ice_trail_manager" in game_state and game_state["ice_trail_manager"]:
        game_state["ice_trail_manager"].draw(surface)


def clear_all_ice_trails(game_state):
    """清除游戏中的所有冰道"""
    if "ice_trail_manager" in game_state and game_state["ice_trail_manager"]:
        game_state["ice_trail_manager"].clear_all_trails()