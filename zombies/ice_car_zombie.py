"""
冰车僵尸类 - 免疫寒冰减速，碾压植物，留下冰道，支持魅惑状态图片翻转
"""
import random
import math
from .base_zombie import BaseZombie
import pygame


class IceCarZombie(BaseZombie):
    """冰车僵尸 - 免疫寒冰减速效果，碾压植物，留下冰道，支持魅惑状态图片翻转"""

    def __init__(self, row, has_armor_prob=0.0, is_fast=False, wave_mode=False,
                 fast_multiplier=2.5, constants=None, sounds=None, images=None,
                 level_settings=None, zombie_type="ice_car"):

        # 冰车僵尸基础属性
        self.base_speed = 0.0035  # 基础速度，和普通僵尸相近
        self.health = 1000  # 血量适中
        self.max_health = 1000
        self.size_multiplier = 1.1  # 稍大一些
        self.crushed_plants = set()  # 使用set记录已碾压植物的id
        # 冰车僵尸不会有护甲
        has_armor_prob = 0.0

        # 调用父类构造函数
        super().__init__(row, has_armor_prob, is_fast, wave_mode,
                         fast_multiplier, constants, sounds, images,
                         level_settings, zombie_type)

        # 冰车特有属性
        self.is_ice_immune = True  # 免疫寒冰减速效果
        self.crush_plants = True  # 可以碾压植物
        self.explodes_on_spike = True  # 遇到地刺会爆炸

        # 冰道相关属性
        self.ice_trail_timer = 0  # 冰道生成计时器
        self.ice_trail_interval = 15  # 每15帧检查一次冰道生成
        self.last_trail_col = None  # 上次生成冰道的列位置
        self._game_state = None  # 游戏状态引用
        # 冰车特有属性
        self.continuous_damage = 10  # 每帧对敌对僵尸造成10伤害
        self.damage_timer = 0  # 伤害计时器
        self.damage_interval = 1  # 每帧造成伤害

        # 重新计算速度（1.15-1.2倍普通僵尸速度）
        speed_multiplier = random.uniform(1.15, 1.2)
        if wave_mode and is_fast:
            self.speed = self.base_speed * speed_multiplier * fast_multiplier
        else:
            self.speed = self.base_speed * speed_multiplier

        # 保存原始速度，防止被其他效果修改
        self.original_speed = self.speed

    def set_game_state(self, game_state):
        """设置游戏状态引用，用于冰道管理"""
        self._game_state = game_state

    def update(self, plants):
        """更新冰车僵尸状态 - 添加对敌对僵尸的持续伤害"""
        if self.is_dying:
            self.death_animation_timer -= 1
            return

        # 处理对敌对僵尸的持续伤害
        if self._game_state and "zombies" in self._game_state:
            self._apply_continuous_damage_to_enemies()

        # 原有的更新逻辑
        if hasattr(self, 'is_charmed') and self.is_charmed:
            if not self._check_stun_status():
                self.col += abs(self.speed) * 0.8
            self._update_ice_trail()
            return

        self._update_attack_logic(plants)
        self._update_ice_trail()

        if not self._check_stun_status():
            if self.speed > 0:
                self.speed = -abs(self.speed)
            self.col -= abs(self.speed)

    def _apply_continuous_damage_to_enemies(self):
        """对附近的敌对僵尸造成持续伤害"""
        self.damage_timer += 1

        if self.damage_timer >= self.damage_interval:
            current_team = getattr(self, 'team', 'zombie')

            for zombie in self._game_state["zombies"]:
                if zombie == self:  # 跳过自己
                    continue

                zombie_team = getattr(zombie, 'team', 'zombie')

                # 只攻击不同阵营的僵尸
                if zombie_team != current_team:
                    # 检查是否在攻击范围内（同行且距离很近）
                    if (zombie.row == self.row and
                            abs(zombie.col - self.col) < 1.0):  # 1格范围内

                        # 造成持续伤害
                        zombie.health -= self.continuous_damage

                        # 检查是否死亡
                        if zombie.health <= 0 and not zombie.is_dying:
                            # 标记为爆炸性死亡（如果是爆炸僵尸）
                            if hasattr(zombie, 'take_damage_from_explosion'):
                                zombie.take_damage_from_explosion()
                            zombie.start_death_animation()

            self.damage_timer = 0

    def _update_attack_logic(self, plants):
        """冰车僵尸的攻击逻辑 - 碾压植物或遇到地刺爆炸 - 修复版本"""
        if self.is_dying:
            return

        # 修复：使用更宽泛的检查范围，确保能及时检测到植物
        current_col = int(round(self.col))
        check_range = 0.8  # 增加检查范围到0.8

        plants_in_range = []
        for plant in plants:
            if plant.row == self.row:
                # 修复：使用更精确的距离计算
                plant_center = plant.col + 0.5  # 植物中心位置
                zombie_center = self.col + 0.5  # 僵尸中心位置
                distance = abs(plant_center - zombie_center)

                if distance <= check_range:
                    plants_in_range.append(plant)

        if plants_in_range:
            for plant in plants_in_range:
                plant_id = id(plant)  # 获取植物的唯一标识

                # 修复：检查是否已经碾压过这颗植物
                if plant_id in self.crushed_plants:
                    continue

                if plant.plant_type == "luker":  # 地刺类植物
                    # 遇到地刺，爆炸死亡（无伤害）
                    self._explode_on_spike()
                    return
                else:
                    # 修复：立即碾压其他植物，播放啃咬音效
                    self._crush_plant_immediately(plant, plants)
                    # 标记这颗植物已被碾压
                    self.crushed_plants.add(plant_id)

    def _crush_plant_immediately(self, plant, plants):
        """立即碾压植物 - 修复版本"""
        if plant in plants:
            plants.remove(plant)

            # 如果是向日葵，需要更新计数
            if plant.plant_type == "sunflower" and self._game_state:
                level_manager = self._game_state.get("level_manager")
                if level_manager:
                    level_manager.remove_sunflower()

            # 修复：播放啃咬音效现在只会播放一次）
            if self.sounds and self.sounds.get("bite"):
                self.sounds["bite"].play()

    def _explode_on_spike(self):
        """遇到地刺爆炸 - 改进版：同归于尽"""
        if not self.is_dying:
            # 开始死亡动画
            self.start_death_animation()

            # 播放爆炸音效（如果有）
            if self.sounds and self.sounds.get("cherry_explosion"):
                self.sounds["cherry_explosion"].play()

            # 如果可以访问游戏状态，也摧毁地刺
            if self._game_state and "plants" in self._game_state:
                for plant in self._game_state["plants"][:]:  # 使用切片副本避免迭代时修改
                    if (plant.plant_type == "luker" and
                            plant.row == self.row and
                            self.is_zombie_on_position(plant)):
                        # 摧毁地刺
                        plant.health = 0
                        break

    def is_zombie_on_position(ice_car_zombie, plant):
        """检查冰车僵尸是否在指定植物位置上"""
        if ice_car_zombie.row != plant.row:
            return False

        # 检查冰车僵尸的位置是否与植物重叠
        zombie_left = ice_car_zombie.col
        zombie_right = ice_car_zombie.col + ice_car_zombie.size_multiplier
        plant_left = plant.col
        plant_right = plant.col + 1

        # 检查重叠
        return not (zombie_right <= plant_left or zombie_left >= plant_right)

    def _update_ice_trail(self):
        """更新冰道生成"""
        if self.is_dying:
            return

        self.ice_trail_timer += 1

        # 每隔一定帧数检查冰道生成
        if self.ice_trail_timer >= self.ice_trail_interval:
            current_trail_col = int(round(self.col))

            # 只在移动到新位置时生成冰道
            if self.last_trail_col != current_trail_col and current_trail_col >= 0:
                self._create_ice_trail(current_trail_col)
                self.last_trail_col = current_trail_col

            self.ice_trail_timer = 0

    def _create_ice_trail(self, col):
        """在指定位置创建冰道"""
        if not self._game_state or col < 0:
            return

        # 确保冰道管理器存在
        if "ice_trail_manager" not in self._game_state:
            self._initialize_ice_trail_manager()

        # 添加冰道
        if self._game_state["ice_trail_manager"]:
            self._game_state["ice_trail_manager"].add_ice_trail(self.row, col)

    def _initialize_ice_trail_manager(self):
        """初始化冰道管理器"""
        try:
            from .ice_trail_manager import IceTrailManager
            from core.constants import get_constants

            self._game_state["ice_trail_manager"] = IceTrailManager(
                constants=get_constants(),
                images=self._game_state.get("images")
            )
        except ImportError:
            # 如果导入失败，创建一个空的管理器
            self._game_state["ice_trail_manager"] = None

    def apply_freeze_effect(self):
        """应用冰冻效果 - 冰车僵尸免疫减速但仍受伤害"""
        # 冰车僵尸免疫冰冻减速效果，不修改速度
        pass

    def take_damage(self, damage, damage_type=None):
        """受到伤害 - 重写以处理免疫效果"""
        # 冰车僵尸免疫寒冰减速效果，但仍会受到寒冰伤害
        if damage_type == 'ice':
            # 受到寒冰伤害，但不会被减速
            self.health -= damage
        else:
            # 正常受到其他类型伤害
            self.health -= damage

        if self.health <= 0:
            self.health = 0

    def _check_stun_status(self):
        """检查眩晕状态 - 冰车僵尸可能受到黄瓜等效果影响"""
        if not self._game_state:
            return False

        # 检查是否受到眩晕效果（如黄瓜）
        stun_timers = self._game_state.get("zombie_stun_timers", {})
        zombie_id = id(self)

        return zombie_id in stun_timers and stun_timers[zombie_id] > 0

    def _draw_zombie_body(self, surface, x, y, base_x, base_y, actual_size):
        """绘制冰车僵尸本体 - 支持魅惑状态图片翻转"""
        zombie_img = self._get_zombie_image('ice_car_zombie_img')

        if zombie_img:
            # 使用冰车僵尸图片
            if self.size_multiplier != 1.0:
                scaled_image = pygame.transform.scale(zombie_img, (actual_size, actual_size))
                surface.blit(scaled_image, (x, y))
            else:
                surface.blit(zombie_img, (x, y))
        else:
            # 备用绘制：深蓝色矩形表示冰车
            ice_car_color = (70, 130, 180)  # 钢蓝色
            pygame.draw.rect(surface, ice_car_color, (x, y, actual_size, actual_size))

            # 添加一些装饰线条表示是车辆
            line_color = (200, 230, 255)  # 浅蓝色
            pygame.draw.line(surface, line_color,
                             (x + 5, y + actual_size // 3),
                             (x + actual_size - 5, y + actual_size // 3), 2)
            pygame.draw.line(surface, line_color,
                             (x + 5, y + 2 * actual_size // 3),
                             (x + actual_size - 5, y + 2 * actual_size // 3), 2)

    def _draw_zombie_to_surface(self, surface, x, y, actual_size):
        """将冰车僵尸绘制到指定surface（用于死亡动画）- 支持魅惑状态图片翻转"""
        zombie_img = self._get_zombie_image('ice_car_zombie_img')

        if zombie_img:
            if self.size_multiplier != 1.0:
                scaled_image = pygame.transform.scale(zombie_img, (actual_size, actual_size))
                surface.blit(scaled_image, (x, y))
            else:
                surface.blit(zombie_img, (x, y))
        else:
            # 备用绘制
            ice_car_color = (70, 130, 180)
            pygame.draw.rect(surface, ice_car_color, (x, y, actual_size, actual_size))