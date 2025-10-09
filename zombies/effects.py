"""
僵尸相关的视觉效果
"""
import pygame
import random
import math


class CucumberSprayParticle:
    """黄瓜喷射粒子 - 乳白色，向前喷射"""

    def __init__(self, x, y, direction=1):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 8)
        self.max_radius = self.radius

        # 向前喷射（方向由僵尸朝向决定）
        self.direction = direction  # 1向右，-1向左

        # 主要向前，稍微有些散射
        forward_speed = random.uniform(1, 3)
        vertical_spread = random.uniform(-0.5, 0.5)

        self.vx = forward_speed * self.direction
        self.vy = vertical_spread

        # 重力和空气阻力
        self.gravity = 0.1
        self.friction = 0.98

        # 乳白色色调色板
        base_colors = [
            (255, 255, 240),  # 象牙白
            (250, 250, 210),  # 淡黄白
            (255, 250, 240),  # 花白
            (248, 248, 255),  # 幽灵白
            (240, 248, 255),  # 爱丽丝蓝白
        ]
        self.color = random.choice(base_colors)

        # 生命周期
        self.life = random.randint(60, 100)
        self.max_life = self.life
        self.alpha = 220

        # 旋转和脉冲效果
        self.rotation = 0
        self.rotation_speed = random.uniform(-5, 5)
        self.pulse_speed = random.uniform(0.1, 0.2)

    def update(self):
        # 应用重力和阻力
        self.vy += self.gravity
        self.vx *= self.friction
        self.vy *= self.friction

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 更新旋转
        self.rotation += self.rotation_speed

        # 减少生命值
        self.life -= 1
        life_ratio = self.life / self.max_life

        # 大小和透明度变化
        if life_ratio > 0.7:
            # 初期：稍微增大
            scale = 1.0 + (1 - life_ratio) * 0.5
            self.alpha = 220
        elif life_ratio > 0.3:
            # 中期：稳定大小，轻微脉冲
            pulse = 1.0 + math.sin(self.life * self.pulse_speed) * 0.15
            scale = 1.2 * pulse
            self.alpha = int(200 * life_ratio)
        else:
            # 后期：缩小并变透明
            scale = life_ratio * 1.2
            self.alpha = int(150 * life_ratio)

        self.radius = max(1, int(self.max_radius * scale))

        return self.life > 0

    def draw(self, surface):
        if self.radius > 0 and self.alpha > 0:
            particle_size = self.radius * 2
            particle_surface = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)

            # 绘制主体粒子
            color_with_alpha = (*self.color, self.alpha)
            pygame.draw.circle(particle_surface, color_with_alpha,
                               (self.radius, self.radius), self.radius)

            # 添加柔和的内部高光
            if self.radius > 3:
                highlight_radius = max(1, self.radius // 2)
                highlight_alpha = min(self.alpha // 2, 100)
                highlight_color = (255, 255, 255, highlight_alpha)
                pygame.draw.circle(particle_surface, highlight_color,
                                   (self.radius, self.radius), highlight_radius)

            # 应用旋转
            if abs(self.rotation) > 0.1:
                particle_surface = pygame.transform.rotate(particle_surface, self.rotation)

            # 计算绘制位置
            draw_x = self.x - particle_surface.get_width() // 2
            draw_y = self.y - particle_surface.get_height() // 2

            surface.blit(particle_surface, (draw_x, draw_y))


class CharmEffect:
    """魅惑效果 - 让僵尸暂时加入植物阵营"""

    def __init__(self, zombie, duration=300):  # 5秒 = 300帧


        self.zombie = zombie
        self.duration = duration
        self.remaining_time = duration

        # 检查僵尸是否有必要的属性
        if not hasattr(zombie, 'speed'):

            self.remaining_time = 0  # 立即失效
            return

        self.original_speed = zombie.speed
        self.original_team = "zombie"

        # 保存原始属性
        self.original_color_overlay = getattr(zombie, 'color_overlay', None)

        # 粉色覆盖层设置
        self.charm_pink = (255, 105, 180, 100)  # 深粉色，半透明
        self.pulse_intensity = 0
        self.pulse_direction = 1


        # 应用魅惑效果
        self.apply_charm()

    def apply_charm(self):
        """应用魅惑效果"""


        # 检查僵尸是否有speed属性
        if not hasattr(self.zombie, 'speed'):

            return

        # 反转速度（让僵尸向后走）
        old_speed = self.zombie.speed
        self.zombie.speed = -abs(self.original_speed)


        # 设置粉色覆盖层（增强版本）
        self.zombie.color_overlay = self.charm_pink

        # 添加魅惑效果标记，用于渲染时的额外处理
        self.zombie.charm_effect = self

        # 标记为魅惑状态
        self.zombie.is_charmed = True
        self.zombie.team = "plant"

        # 防止被植物攻击
        self.zombie.immune_to_plants = True



    def update(self):
        """更新魅惑效果，返回是否仍在生效"""


        # 检查僵尸是否还存在
        if not hasattr(self, 'zombie') or self.zombie is None:

            return False

        # 检查remaining_time是否合理
        if not hasattr(self, 'remaining_time') or self.remaining_time is None:

            return False

        self.remaining_time -= 1

        # 更新脉冲效果
        self.pulse_intensity += self.pulse_direction * 2
        if self.pulse_intensity >= 50:
            self.pulse_direction = -1
        elif self.pulse_intensity <= 0:
            self.pulse_direction = 1

        # 更新粉色覆盖层的透明度（脉冲效果）
        base_alpha = 100
        pulse_alpha = int(base_alpha + self.pulse_intensity * 0.6)  # 范围：100-130
        self.zombie.color_overlay = (255, 105, 180, pulse_alpha)



        if self.remaining_time <= 0:

            self.remove_charm()
            return False




        return True

    def draw_charm_overlay(self, surface, zombie_rect):
        """在僵尸图片上绘制额外的粉色覆盖层"""
        if not self.zombie or not hasattr(self.zombie, 'is_charmed'):
            return

        # 创建粉色覆盖层表面
        overlay_surface = pygame.Surface((zombie_rect.width, zombie_rect.height), pygame.SRCALPHA)

        # 基础粉色覆盖
        base_alpha = 80 + int(self.pulse_intensity * 0.8)  # 80-120 范围的脉冲透明度
        pink_color = (255,105,180, base_alpha)
        overlay_surface.fill(pink_color)

        # 添加边缘光晕效果
        glow_alpha = 40 + int(self.pulse_intensity * 0.4)
        for i in range(3):  # 绘制多层光晕
            glow_surface = pygame.Surface((zombie_rect.width + i*4, zombie_rect.height + i*4), pygame.SRCALPHA)
            glow_color = (255, 182, 193, max(0, glow_alpha - i*15))  # 浅粉色光晕
            glow_surface.fill(glow_color)

            glow_x = zombie_rect.x - i*2
            glow_y = zombie_rect.y - i*2
            surface.blit(glow_surface, (glow_x, glow_y), special_flags=pygame.BLEND_ALPHA_SDL2)

        # 绘制主覆盖层
        surface.blit(overlay_surface, zombie_rect.topleft, special_flags=pygame.BLEND_ALPHA_SDL2)

        # 添加闪烁的小心心效果
        if self.remaining_time % 15 == 0:  # 每0.25秒生成小心心
            self.draw_charm_hearts(surface, zombie_rect)

    def draw_charm_hearts(self, surface, zombie_rect):
        """绘制魅惑状态的小心心特效"""
        for _ in range(2):  # 生成2个小心心
            heart_x = zombie_rect.centerx + random.randint(-20, 20)
            heart_y = zombie_rect.centery + random.randint(-30, -10)

            # 绘制简单的心形（用两个圆和一个三角形组成）
            heart_size = random.randint(8, 12)
            heart_color = (255, 192, 203, 200)  # 粉色心形

            # 两个上半部分的圆
            pygame.draw.circle(surface, heart_color[:3],
                             (heart_x - heart_size//3, heart_y), heart_size//2)
            pygame.draw.circle(surface, heart_color[:3],
                             (heart_x + heart_size//3, heart_y), heart_size//2)

            # 下半部分的三角形
            points = [
                (heart_x - heart_size//2, heart_y),
                (heart_x + heart_size//2, heart_y),
                (heart_x, heart_y + heart_size)
            ]
            pygame.draw.polygon(surface, heart_color[:3], points)

    def remove_charm(self):
        """移除魅惑效果"""


        # 检查僵尸和original_speed
        if not hasattr(self, 'zombie') or not hasattr(self, 'original_speed'):

            return


        # 恢复原始速度
        self.zombie.speed = self.original_speed

        # 移除粉色覆盖
        self.zombie.color_overlay = self.original_color_overlay

        # 移除魅惑效果引用
        if hasattr(self.zombie, 'charm_effect'):
            delattr(self.zombie, 'charm_effect')

        # 恢复原始阵营
        self.zombie.is_charmed = False
        self.zombie.team = self.original_team
        self.zombie.immune_to_plants = False
