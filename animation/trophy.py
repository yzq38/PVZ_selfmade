"""
奖杯动画模块 - 处理奖杯的动画效果和交互
"""
import pygame
import random
import math


class Trophy:
    """奖杯类 - 包含完整的动画效果和粒子系统"""

    def __init__(self, x, y, image=None):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 80
        self.collected = False
        self.particles = []
        self.explosion_started = False
        self.explosion_complete = False
        self.fade_timer = 0
        self.fade_duration = 110
        self.image = image

        # 增强闪烁效果相关属性
        self.blink_timer = 0
        self.blink_speed = 0.12  # 增加闪烁速度
        self.min_alpha = 180  # 提高最小透明度，确保始终可见
        self.max_alpha = 255  # 最大透明度

        # 浮动效果
        self.float_timer = 0
        self.float_speed = 0.05
        self.float_amplitude = 8  # 上下浮动幅度
        self.original_y = y

        # 旋转效果
        self.rotation_angle = 0
        self.rotation_speed = 1.5

        # 脉冲发光效果
        self.pulse_timer = 0
        self.pulse_speed = 0.08
        self.glow_particles = []

        # 环形光晕效果
        self.halo_timer = 0
        self.halo_speed = 0.06

    def create_glow_particles(self):
        """创建环绕奖杯的发光粒子"""
        if random.random() < 0.3:  # 30%概率生成新粒子
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(35, 60)  # 距离奖杯中心的距离
            self.glow_particles.append({
                'angle': angle,
                'distance': distance,
                'life': random.randint(60, 120),
                'max_life': random.randint(60, 120),
                'size': random.randint(2, 5),
                'color': random.choice([
                    (255, 255, 100),  # 金黄色
                    (255, 200, 50),  # 橙黄色
                    (255, 255, 255),  # 白色
                    (255, 150, 0)  # 橙色
                ])
            })

    def update_glow_particles(self):
        """更新发光粒子"""
        for particle in self.glow_particles[:]:
            particle['angle'] += 0.03  # 粒子绕奖杯旋转
            particle['life'] -= 1

            if particle['life'] <= 0:
                self.glow_particles.remove(particle)

    def draw_enhanced_glow(self, surface):
        """绘制增强的发光效果"""
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # 1. 绘制多层外发光
        self.pulse_timer += self.pulse_speed
        pulse_intensity = (math.sin(self.pulse_timer) + 1) / 2

        for i in range(6):  # 增加发光层数
            glow_radius = 40 + i * 15 + int(pulse_intensity * 20)
            glow_alpha = max(5, int((80 - i * 12) * pulse_intensity))

            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (255, min(255, 215 + int(pulse_intensity * 40)), 0)

            # 创建临时表面来绘制圆形，然后设置透明度
            temp_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            temp_surface.set_alpha(glow_alpha)
            glow_surface.blit(temp_surface, (0, 0))

            surface.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius))

        # 2. 绘制环形光晕
        self.halo_timer += self.halo_speed
        for i in range(3):
            halo_angle = self.halo_timer + i * (math.pi * 2 / 3)
            halo_radius = 50 + math.sin(halo_angle) * 15
            halo_x = center_x + math.cos(halo_angle) * 10
            halo_y = center_y + math.sin(halo_angle) * 5

            halo_alpha = int(100 + math.sin(halo_angle * 2) * 50)
            halo_surface = pygame.Surface((int(halo_radius * 2), int(halo_radius * 2)), pygame.SRCALPHA)

            # 创建临时表面来绘制环形，然后设置透明度
            temp_halo = pygame.Surface((int(halo_radius * 2), int(halo_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_halo, (255, 255, 200),
                               (int(halo_radius), int(halo_radius)), int(halo_radius), 3)
            temp_halo.set_alpha(halo_alpha)
            halo_surface.blit(temp_halo, (0, 0))

            surface.blit(halo_surface, (halo_x - halo_radius, halo_y - halo_radius))

        # 3. 绘制发光粒子
        for particle in self.glow_particles:
            particle_x = center_x + math.cos(particle['angle']) * particle['distance']
            particle_y = center_y + math.sin(particle['angle']) * particle['distance']

            alpha = int(255 * (particle['life'] / particle['max_life']))

            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            # 分别绘制颜色和透明度
            color_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(color_surface, particle['color'],
                               (particle['size'], particle['size']), particle['size'])
            color_surface.set_alpha(alpha)
            particle_surface.blit(color_surface, (0, 0))

            surface.blit(particle_surface,
                         (particle_x - particle['size'], particle_y - particle['size']))

    def draw(self, surface):
        """绘制奖杯主体"""
        if not self.collected and not self.explosion_started:
            # 更新浮动位置
            self.float_timer += self.float_speed
            float_offset = math.sin(self.float_timer) * self.float_amplitude
            current_y = self.original_y + float_offset

            # 更新旋转角度
            self.rotation_angle += self.rotation_speed
            if self.rotation_angle >= 360:
                self.rotation_angle -= 360

            # 生成和更新发光粒子
            self.create_glow_particles()
            self.update_glow_particles()

            # 绘制增强发光效果
            self.draw_enhanced_glow(surface)

            # 计算增强的闪烁效果
            self.blink_timer += self.blink_speed
            alpha_base = (math.sin(self.blink_timer) + 1) / 2
            # 添加快速闪烁叠加效果
            quick_flash = (math.sin(self.blink_timer * 5) + 1) / 2 * 0.3
            alpha_ratio = alpha_base + quick_flash
            alpha_ratio = min(1.0, alpha_ratio)

            current_alpha = int(self.min_alpha + (self.max_alpha - self.min_alpha) * alpha_ratio)

            # 绘制奖杯主体
            if self.image:
                # 创建旋转后的图像
                trophy_surface = self.image.copy()
                if self.rotation_angle != 0:
                    trophy_surface = pygame.transform.rotate(trophy_surface, self.rotation_angle)
                    # 重新计算绘制位置以保持居中
                    new_rect = trophy_surface.get_rect()
                    draw_x = self.x + self.width // 2 - new_rect.width // 2
                    draw_y = current_y + self.height // 2 - new_rect.height // 2
                else:
                    draw_x = self.x
                    draw_y = current_y

                trophy_surface.set_alpha(current_alpha)
                surface.blit(trophy_surface, (draw_x, draw_y))
            else:
                # 后备绘制方法 - 增强版
                trophy_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

                # 绘制渐变奖杯主体
                for i in range(self.height):
                    color_ratio = i / self.height
                    r = int(255 * (1 - color_ratio * 0.3))
                    g = int(215 + color_ratio * 40)
                    b = int(color_ratio * 50)

                    line_color = (r, g, b)
                    pygame.draw.line(trophy_surface, line_color,
                                     (0, i), (self.width, i))

                # 绘制高光
                highlight_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                highlight_rect = (self.width // 4, self.height // 6,
                                  self.width // 2, self.height // 3)
                pygame.draw.ellipse(highlight_surface, (255, 255, 255), highlight_rect)
                highlight_surface.set_alpha(120)
                trophy_surface.blit(highlight_surface, (0, 0))

                # 绘制装饰边框
                pygame.draw.rect(trophy_surface, (218, 165, 32),
                                 (0, 0, self.width, self.height), 4)

                # 应用旋转
                if self.rotation_angle != 0:
                    trophy_surface = pygame.transform.rotate(trophy_surface, self.rotation_angle)
                    new_rect = trophy_surface.get_rect()
                    draw_x = self.x + self.width // 2 - new_rect.width // 2
                    draw_y = current_y + self.height // 2 - new_rect.height // 2
                else:
                    draw_x = self.x
                    draw_y = current_y

                trophy_surface.set_alpha(current_alpha)
                surface.blit(trophy_surface, (draw_x, draw_y))

            # 绘制闪电效果
            if random.random() < 0.15:  # 15%概率出现闪电
                self.draw_lightning_effect(surface, self.x + self.width // 2, current_y + self.height // 2)

            # 绘制星光效果
            if current_alpha > 230:  # 在高亮时显示星光
                self.draw_star_sparkles(surface, self.x + self.width // 2, current_y + self.height // 2)

    def draw_lightning_effect(self, surface, center_x, center_y):
        """绘制闪电效果"""
        lightning_surface = pygame.Surface((100, 100), pygame.SRCALPHA)

        # 创建闪电颜色的临时表面
        lightning_color = (255, 255, 255)

        # 绘制十字闪光
        temp_surface1 = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.line(temp_surface1, lightning_color, (50, 20), (50, 80), 3)
        pygame.draw.line(temp_surface1, lightning_color, (20, 50), (80, 50), 3)
        temp_surface1.set_alpha(200)
        lightning_surface.blit(temp_surface1, (0, 0))

        # 绘制对角线闪光
        temp_surface2 = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.line(temp_surface2, lightning_color, (30, 30), (70, 70), 2)
        pygame.draw.line(temp_surface2, lightning_color, (70, 30), (30, 70), 2)
        temp_surface2.set_alpha(100)
        lightning_surface.blit(temp_surface2, (0, 0))

        surface.blit(lightning_surface, (center_x - 50, center_y - 50))

    def draw_star_sparkles(self, surface, center_x, center_y):
        """绘制星光闪烁效果"""
        for i in range(6):  # 绘制6个小星星
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(40, 70)
            star_x = center_x + math.cos(angle) * distance
            star_y = center_y + math.sin(angle) * distance

            star_size = random.randint(2, 4)
            star_color = (255, 255, random.randint(200, 255))
            star_alpha = random.randint(150, 255)

            # 绘制四角星
            points = []
            for j in range(8):
                star_angle = j * math.pi / 4
                radius = star_size if j % 2 == 0 else star_size // 2
                px = star_x + math.cos(star_angle) * radius
                py = star_y + math.sin(star_angle) * radius
                points.append((px, py))

            if len(points) >= 3:
                star_surface = pygame.Surface((star_size * 4, star_size * 4), pygame.SRCALPHA)
                adjusted_points = [(p[0] - star_x + star_size * 2, p[1] - star_y + star_size * 2) for p in points]
                pygame.draw.polygon(star_surface, star_color, adjusted_points)
                star_surface.set_alpha(star_alpha)
                surface.blit(star_surface, (star_x - star_size * 2, star_y - star_size * 2))

    def check_click(self, pos):
        """检查鼠标点击"""
        if self.collected or self.explosion_started:
            return False

        x, y = pos
        # 考虑浮动位置的点击检测
        current_y = self.original_y + math.sin(self.float_timer) * self.float_amplitude

        if (self.x <= x <= self.x + self.width and
                current_y <= y <= current_y + self.height):
            self.collected = True
            self.explosion_started = True
            self.create_explosion_particles()
            return True
        return False

    def create_explosion_particles(self):
        """创建更壮观的爆炸粒子"""
        for _ in range(150):  # 增加粒子数量
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 12)  # 增加速度范围
            size = random.randint(2, 8)  # 增加大小范围
            life = random.randint(40, 120)  # 增加生命周期

            # 更丰富的颜色选择
            color_choice = random.choice([
                (255, 215, 0),  # 金色
                (255, 255, 0),  # 黄色
                (255, 165, 0),  # 橙色
                (255, 255, 255),  # 白色
                (255, 100, 100),  # 粉红色
                (100, 255, 100),  # 绿色
            ])

            self.particles.append({
                'x': self.x + self.width // 2,
                'y': self.y + self.height // 2,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': size,
                'color': color_choice,
                'life': life,
                'max_life': life
            })

    def update(self):
        """更新奖杯状态"""
        if self.explosion_started:
            # 更新粒子
            for particle in self.particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] += 0.15  # 稍微增加重力
                particle['life'] -= 1

                if particle['life'] <= 0:
                    self.particles.remove(particle)

            # 检查爆炸是否完成
            if not self.particles:
                self.explosion_complete = True

            # 更新淡出计时器
            if self.explosion_complete:
                self.fade_timer += 1

    def draw_particles(self, surface):
        """绘制爆炸粒子"""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))

            # 绘制带尾迹的粒子
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)

            # 主粒子 - 使用分离的颜色和透明度处理
            main_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(main_surface, particle['color'],
                               (particle['size'], particle['size']), particle['size'])
            main_surface.set_alpha(alpha)
            particle_surface.blit(main_surface, (0, 0))

            # 尾迹效果
            if particle['size'] > 3:
                tail_surface = pygame.Surface((particle['size'] * 2 + 4, particle['size'] * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(tail_surface, particle['color'],
                                   (particle['size'] + 2, particle['size'] + 2), particle['size'] + 2, 2)
                tail_surface.set_alpha(alpha // 3)
                surface.blit(tail_surface, (particle['x'] - particle['size'] - 2, particle['y'] - particle['size'] - 2))

            surface.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))

    def is_fade_complete(self):
        """检查淡出是否完成"""
        return self.fade_timer >= self.fade_duration

    def get_fade_alpha(self):
        """获取淡出透明度"""
        return min(255, int(255 * (self.fade_timer / self.fade_duration)))

    def set_blink_speed(self, speed):
        """设置闪烁速度"""
        self.blink_speed = speed

    def set_blink_alpha_range(self, min_alpha, max_alpha):
        """设置闪烁的透明度范围"""
        self.min_alpha = max(0, min(255, min_alpha))
        self.max_alpha = max(0, min(255, max_alpha))

    def set_float_amplitude(self, amplitude):
        """设置浮动幅度"""
        self.float_amplitude = amplitude

    def set_rotation_speed(self, speed):
        """设置旋转速度"""
        self.rotation_speed = speed