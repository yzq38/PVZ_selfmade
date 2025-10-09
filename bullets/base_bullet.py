"""
修改后的子弹基类 - 支持传送门穿越

"""
import pygame
import math
import random


class BaseBullet:
    """所有子弹的基础类 - 支持传送门穿越"""

    def __init__(self, row, col, bullet_type="base", constants=None, images=None, **kwargs):
        self.row = row
        self.col = col
        self.bullet_type = bullet_type
        self.speed = 0.09
        self.dmg = 25
        self.splash_dmg = 0

        # 状态标记
        self.can_penetrate = kwargs.get('can_penetrate', False)
        self.hit_zombies = set()  # 已击中的僵尸集合（防止重复伤害）
        self.splash_hit_zombies = set()  # 已溅射击中的僵尸集合

        # 传送门相关属性
        self.supports_portal_travel = kwargs.get('supports_portal_travel', False)
        self.source_plant_row = kwargs.get('source_plant_row', row)
        self.source_plant_col = kwargs.get('source_plant_col', col)
        self.has_traveled_through_portal = False
        self.portal_manager = kwargs.get('portal_manager', None)

        # 原始行信息（用于传送门逻辑）
        self.original_row = row

        # 存储引用
        self.constants = constants
        self.images = images

    def update(self, zombies_list=None):
        """更新子弹位置，返回是否应该移除"""
        # 检查传送门穿越（仅对支持传送门的子弹）
        if self.supports_portal_travel and not self.has_traveled_through_portal:
            if self._check_portal_travel():
                # 穿越传送门后不移除子弹，继续移动
                pass

        # 正常移动
        self.col += self.speed

        # 检查边界
        grid_width = self.constants['GRID_WIDTH'] if self.constants else 9
        return self.col > grid_width

    def _check_portal_travel(self):
        """检查并处理传送门穿越"""
        if not self.portal_manager:
            return False

        # 获取当前行的传送门
        current_row_portals = self._get_portals_in_row(self.row)

        for portal in current_row_portals:
            # 检查子弹是否接近传送门位置
            if (portal.is_active and
                    abs(self.col - portal.col) < 0.3 and  # 传送门检测范围
                    portal.col > self.source_plant_col):  # 确保是植物右侧的传送门

                # 执行传送门穿越
                exit_portal = self._find_exit_portal(portal)
                if exit_portal:
                    # 传送到出口传送门
                    self.row = exit_portal.row
                    self.col = exit_portal.col + 0.5  # 在传送门右侧稍微偏移
                    self.has_traveled_through_portal = True


                    return True

        return False

    def _get_portals_in_row(self, row):
        """获取指定行的活跃传送门"""
        if not self.portal_manager or not hasattr(self.portal_manager, 'portals'):
            return []

        return [portal for portal in self.portal_manager.portals
                if portal.row == row and portal.is_active]

    def _find_exit_portal(self, entrance_portal):
        """寻找传送门出口"""
        if not self.portal_manager or not hasattr(self.portal_manager, 'portals'):
            return None

        # 获取其他活跃的传送门作为可能的出口
        exit_candidates = [portal for portal in self.portal_manager.portals
                           if (portal.is_active and portal != entrance_portal)]

        if not exit_candidates:
            return None

        # 选择最优出口（这里可以实现不同的选择策略）
        # 目前选择第一个可用的出口
        return exit_candidates[0]

    def can_hit_zombie(self, zombie):
        """检测是否可以击中僵尸 - 基类实现"""
        # 不攻击被魅惑的僵尸（友军）
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return False
        if hasattr(zombie, 'team') and zombie.team == "plant":
            return False

        # 僵尸必须存活
        if zombie.is_dying:
            return False

        # 检查行和列
        if zombie.row != self.row:
            return False

        # 使用宽松的碰撞检测
        if abs(zombie.col - self.col) > 0.5:
            return False

        return True

    def can_splash_hit_zombie(self, zombie):
        """检查僵尸是否在溅射范围内（基类默认不支持溅射）"""
        return False

    def attack_zombie(self, zombie, level_settings):
        """攻击僵尸，返回是否击中 (0=未击中, 1=击中, 2=免疫)"""
        # 不攻击被魅惑的僵尸（友军）
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            return 0  # 不造成伤害
        if hasattr(zombie, 'team') and zombie.team == "plant":
            return 0  # 不攻击植物阵营的单位
        if zombie.is_dying:
            return 0

        # 首先检查是否可以击中僵尸（距离和行判断）
        if not self.can_hit_zombie(zombie):
            return 0

        # 对于穿透子弹，检查是否已经击中过这个僵尸
        zombie_id = id(zombie)
        if self.can_penetrate and zombie_id in self.hit_zombies:
            return 0

        # 检查僵尸是否触发免疫
        if (hasattr(zombie, 'immunity_chance') and
                random.random() < zombie.immunity_chance):
            self.hit_zombies.add(zombie_id)
            return 2  # 免疫

        # 记录已击中的僵尸
        self.hit_zombies.add(zombie_id)

        # 造成伤害
        self._apply_damage(zombie)
        return 1

    def _apply_damage(self, zombie):
        """对僵尸造成伤害的基础方法"""
        if zombie.has_armor and zombie.armor_health > 0:
            zombie.armor_health -= self.dmg
            if zombie.armor_health < 0:
                zombie.health += zombie.armor_health  # 剩余伤害转到生命值
                zombie.armor_health = 0
        else:
            zombie.health -= self.dmg

    def apply_splash_damage(self, zombies):
        """对范围内的僵尸应用溅射伤害（基类默认不支持）"""
        return 0

    def get_display_position(self):
        """获取用于显示的位置"""
        return self.col, self.row, 0

    def draw(self, surface):
        """绘制子弹"""
        if not self.constants:
            return

        # 获取显示位置
        display_col, display_row, vertical_offset = self.get_display_position()

        x = self.constants['BATTLEFIELD_LEFT'] + int(
            display_col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']))
        y = (self.constants['BATTLEFIELD_TOP'] +
             display_row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
             self.constants['GRID_SIZE'] // 2)

        # 应用垂直偏移（抛物线效果）
        y -= int(vertical_offset * self.constants['GRID_SIZE'])

        # 如果子弹穿越了传送门，添加特殊视觉效果
        if self.has_traveled_through_portal:
            self._draw_portal_effect(surface, x, y)

        # 子类应该重写这个方法来绘制特定的子弹外观
        self._draw_bullet(surface, x, y)

    def _draw_portal_effect(self, surface, x, y):
        """绘制传送门穿越效果"""
        # 添加青色光晕效果表示子弹穿越了传送门
        for radius in range(3, 8):
            alpha = max(50, 150 - radius * 20)
            # 创建带透明度的surface
            glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (0, 255, 255, alpha), (radius, radius), radius)
            surface.blit(glow_surface, (x - radius, y - radius))

    def _draw_bullet(self, surface, x, y):
        """绘制具体的子弹外观（子类重写）"""
        # 默认绘制一个白色圆圈
        white = self.constants.get('WHITE', (255, 255, 255)) if self.constants else (255, 255, 255)
        color = (100, 150, 255) if self.can_penetrate else white

        # 如果穿越了传送门，使用特殊颜色
        if self.has_traveled_through_portal:
            color = (0, 255, 255)  # 青色

        pygame.draw.circle(surface, color, (x, y), 5)