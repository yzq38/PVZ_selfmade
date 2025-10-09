"""
巨人僵尸类 - 支持魅惑状态图片翻转
"""
import pygame
from .base_zombie import BaseZombie


class GiantZombie(BaseZombie):
    """巨人僵尸实现"""

    def __init__(self, row, has_armor_prob=0.3, is_fast=False, wave_mode=False,
                 fast_multiplier=2.5, constants=None, sounds=None, images=None,
                 level_settings=None):
        # 设置巨人僵尸的基础属性
        self.health = 1700
        self.max_health = 1700
        self.base_speed = 0.003  # 移动更慢
        self.attack_dmg = 750  # 砸击伤害更高
        self.size_multiplier = 1.35  # 体积更大

        # 调用父类构造函数
        super().__init__(row, has_armor_prob, is_fast, wave_mode, fast_multiplier,
                         constants, sounds, images, level_settings, "giant")

        # 设置防具血量
        self.armor_health = 300 if (self.has_armor and wave_mode and is_fast) else (200 if self.has_armor else 0)
        self.max_armor_health = self.armor_health

        # 巨人僵尸特有的砸击攻击属性
        self.smash_attack_delay = 60  # 1秒延迟（60帧）
        self.smash_attack_interval = 100
        self.smash_timer = 0  # 砸击计时器
        self.has_attacked_once = False  # 是否已经进行过首次攻击
        self.attack_target = None  # 攻击目标植物

    def _update_attack_logic(self, plants):
        """巨人僵尸的砸击攻击逻辑 - 修复：处理魅惑状态"""
        # 如果被魅惑，不攻击植物
        if hasattr(self, 'is_charmed') and self.is_charmed:
            # 魅惑僵尸向右移动，不攻击植物
            if not self.is_attacking:  # 如果没在和其他僵尸战斗
                self.col += abs(self.speed)
            return

        # 检测是否碰撞植物（更精确的碰撞检测）
        collision_plant = None
        for plant in plants:
            if plant.row == self.row:
                # 计算实际的碰撞检测范围
                zombie_actual_size = self.constants['GRID_SIZE'] * self.size_multiplier
                plant_size = self.constants['GRID_SIZE']

                # 僵尸位置（考虑大小）
                zombie_left = self.col
                zombie_right = self.col + (zombie_actual_size / self.constants['GRID_SIZE'])

                # 植物位置
                plant_left = plant.col
                plant_right = plant.col + 1

                # 检测重叠
                if zombie_left < plant_right and zombie_right > plant_left:
                    collision_plant = plant
                    break

        if collision_plant:
            # 发现碰撞，开始攻击状态
            self.is_attacking = True
            self.attack_target = collision_plant

            # 停止移动，开始计时
            if not self.has_attacked_once:
                # 首次攻击：等待1秒
                self.smash_timer += 1
                if self.smash_timer >= self.smash_attack_delay:
                    self._perform_smash_attack()
                    self.has_attacked_once = True
                    self.smash_timer = 0  # 重置计时器用于后续攻击
            else:
                # 后续攻击：每2秒一次
                self.smash_timer += 1
                if self.smash_timer >= self.smash_attack_interval:
                    self._perform_smash_attack()
                    self.smash_timer = 0
        else:
            # 没有碰撞，继续移动
            self.is_attacking = False
            self.attack_target = None
            self.has_attacked_once = False
            self.smash_timer = 0

            # 确保速度方向正确
            if self.speed > 0:
                self.speed = -abs(self.speed)
            self.col -= abs(self.speed)

    def _perform_smash_attack(self):
        """执行砸击攻击"""
        if self.attack_target and self.attack_target.is_alive():
            # 对目标植物造成伤害
            self.attack_target.take_damage(self.attack_dmg)

            # 播放砸击音效（如果有的话）
            if self.sounds and self.sounds.get("giant_smash"):
                self.sounds["giant_smash"].play()
            elif self.sounds and self.sounds.get("bite"):
                # 如果没有专门的砸击音效，使用咬击音效
                self.sounds["bite"].play()

    def _draw_zombie_body(self, surface, x, y, base_x, base_y, actual_size):
        """绘制巨人僵尸本体 - 支持魅惑状态图片翻转"""
        # 巨人僵尸砸击动画效果
        if self.is_attacking and not self.is_stunned:
            if self.smash_timer > self.smash_attack_delay - 10:
                y += 3

        # 获取巨人僵尸图片，优先使用专用图片，否则使用普通僵尸图片
        giant_img_key = 'giant_zombie_img' if self.images and self.images.get('giant_zombie_img') else 'zombie_img'
        zombie_img = self._get_zombie_image(giant_img_key)

        if zombie_img:
            scaled_img = pygame.transform.scale(zombie_img, (actual_size, actual_size))

            # 修复：改进冰冻效果 - 使用海蓝色覆盖层
            if hasattr(self, 'is_frozen') and self.is_frozen:
                # 先绘制原图，再绘制覆盖层
                surface.blit(scaled_img, (x, y))

                # 创建海蓝色覆盖层（更强烈的效果）
                ice_overlay = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
                ice_overlay.fill((70, 130, 180, 120))  # 海蓝色，半透明
                surface.blit(ice_overlay, (x, y))

                # 绘制冰晶装饰效果
                self._draw_ice_crystals(surface, x, y, actual_size)

            elif self.is_stunned:
                stun_surface = scaled_img.copy()
                stun_surface.fill((255, 255, 0, 100), special_flags=pygame.BLEND_ADD)
                surface.blit(stun_surface, (x, y))
            else:
                surface.blit(scaled_img, (x, y))
        else:
            # 没有图片时使用矩形
            color = self.constants.get('GIANT_COLOR', self.constants['GRAY'])

            # 根据状态改变颜色
            if hasattr(self, 'is_frozen') and self.is_frozen:
                color = (70, 130, 180)  # 海蓝色表示冰冻
            elif self.is_stunned:
                color = (255, 255, 0)  # 黄色表示眩晕

            pygame.draw.rect(surface, color, (x, y, actual_size, actual_size))

    def _draw_zombie_to_surface(self, surface, x, y, actual_size):
        """将巨人僵尸绘制到指定surface（用于死亡动画）- 支持魅惑状态图片翻转"""
        giant_img_key = 'giant_zombie_img' if self.images and self.images.get('giant_zombie_img') else 'zombie_img'
        zombie_img = self._get_zombie_image(giant_img_key)

        if zombie_img:
            scaled_img = pygame.transform.scale(zombie_img, (actual_size, actual_size))
            surface.blit(scaled_img, (x, y))
        else:
            color = self.constants.get('GIANT_COLOR', self.constants.get('GRAY', (128, 128, 128)))
            pygame.draw.rect(surface, color, (x, y, actual_size, actual_size))

    def draw(self, surface):
        """重写绘制方法以添加巨人僵尸特有的攻击状态指示器"""
        # 调用父类的绘制方法
        super().draw(surface)

        # 巨人僵尸攻击状态指示器
        if self.zombie_type == "giant" and self.is_attacking and not self.is_stunned:
            if not self.has_attacked_once:
                remaining_time = (self.smash_attack_delay - self.smash_timer) // 20
                if remaining_time > 0:
                    pass  # 可以在这里添加倒计时文字显示