"""
黄瓜植物类
"""
import pygame
import random
import math
from .base_plant import BasePlant
from .particles import CucumberExplosionParticle, CucumberSprayParticle


class Cucumber(BasePlant):
    """黄瓜：全屏眩晕+喷射效果"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'cucumber_60',
        'display_name': '黄瓜炸弹',
        'category': 'explosive',
        'preview_alpha': 128,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "cucumber", constants, images, level_manager)

        # 爆炸参数
        self.explode_timer = 0
        self.explode_delay = 60
        self.explosion_damage = 1200
        self.has_exploded = False
        self.should_be_removed = False

        # 音效播放控制
        self.explosion_sound_played = False
        self.sound_trigger_frame = self.explode_delay - 10

        # 动画相关属性
        self.init_cucumber_animation()

    def init_cucumber_animation(self):
        """初始化黄瓜动画特有属性"""
        # 基础动画（类似樱桃炸弹）
        self.scale = 1.0
        self.max_scale = 1.3  # 黄瓜缩放稍小一些
        self.scale_timer = 0
        self.scale_interval = 40  # 稍快一些
        self.scale_step = 0.1

        # 爆炸相关
        self.explosion_started = False
        self.explosion_particles = []
        self.particles_created = False

        # 黄瓜特殊属性
        self.explosion_range = "fullscreen"  # 全屏范围
        self.stun_duration = 300  # 5秒眩晕（60fps * 5）
        self.spray_duration = 120  # 2秒喷射（60fps * 2）
        self.death_probability = 0.5  # 50%死亡概率

        # 喷射粒子
        self.spray_particles = []
        self.spray_created = False

        # 视觉效果
        self.pulse_timer = 0
        self.glow_intensity = 0

        # 全屏爆炸状态
        self.fullscreen_explosion_data = None

    def update(self):
        """更新黄瓜状态"""
        # 更新脉冲效果
        self.pulse_timer += 1

        # 更新缩放动画
        if not self.explosion_started:
            self.scale_timer += 1
            if self.scale_timer >= self.scale_interval and self.scale < self.max_scale:
                self.scale = min(self.scale + self.scale_step, self.max_scale)
                self.scale_timer = 0

            # 黄瓜发光效果逐渐增强
            progress = self.explode_timer / self.explode_delay
            self.glow_intensity = int(progress * 150)

        # 黄瓜：累加爆炸计时器
        if not self.has_exploded:
            self.explode_timer += 1

            # 检查是否需要播放音效（爆炸前10帧）
            if (self.explode_timer >= self.sound_trigger_frame and
                    not self.explosion_sound_played):
                return "play_cucumber_sound"

            # 检查爆炸触发条件
            should_explode = False

            # 条件1：正常倒计时结束
            if self.explode_timer >= self.explode_delay:
                should_explode = True

            # 条件2：被攻击死亡（血量归零或小于0）
            if self.health <= 0:
                should_explode = True

            # 触发爆炸
            if should_explode:
                self.explode_cucumber()

        # 更新爆炸粒子
        if self.explosion_particles:
            self.explosion_particles = [p for p in self.explosion_particles if p.update()]

        # 更新喷射粒子
        if self.spray_particles:
            self.spray_particles = [p for p in self.spray_particles if p.update()]

        # 如果所有粒子都消失，标记为可移除
        if (self.explosion_started and
                not self.explosion_particles and
                not self.spray_particles):
            self.should_be_removed = True

        return 0

    def explode_cucumber(self):
        """黄瓜爆炸 - 全屏效果"""
        if not self.has_exploded:
            self.has_exploded = True
            self.explosion_started = True

            # 创建全屏爆炸数据，供外部系统使用
            self.fullscreen_explosion_data = {
                'type': 'cucumber_explosion',
                'stun_duration': self.stun_duration,
                'spray_duration': self.spray_duration,
                'death_probability': self.death_probability,
                'plant_row': self.row,
                'plant_col': self.col
            }

            # 创建视觉效果粒子
            self.create_cucumber_explosion_particles()

            # 确保音效播放状态正确
            if not self.explosion_sound_played:
                self.explosion_sound_played = True

            return True
        return False

    def create_cucumber_explosion_particles(self):
        """创建黄瓜爆炸粒子（绿色系）"""
        if self.particles_created:
            return

        # 计算黄瓜的像素位置
        center_x = (self.constants['BATTLEFIELD_LEFT'] +
                    self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                    self.constants['GRID_SIZE'] // 2)
        center_y = (self.constants['BATTLEFIELD_TOP'] +
                    self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                    self.constants['GRID_SIZE'] // 2)

        # 创建绿色爆炸粒子
        particle_count = random.randint(40, 60)
        for _ in range(particle_count):
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)
            particle = CucumberExplosionParticle(center_x + offset_x, center_y + offset_y)
            self.explosion_particles.append(particle)

        self.particles_created = True

    def create_spray_particles_at_position(self, x, y, direction=1):
        """在指定位置创建喷射粒子（供外部调用）"""
        particle_count = random.randint(1, 2)
        for _ in range(particle_count):
            # 在位置周围稍微分散
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-10, 10)
            particle = CucumberSprayParticle(x + offset_x, y + offset_y, direction)
            self.spray_particles.append(particle)

    def get_fullscreen_explosion_data(self):
        """获取全屏爆炸数据（供外部系统使用）"""
        data = self.fullscreen_explosion_data
        self.fullscreen_explosion_data = None  # 清除数据，避免重复处理
        return data

    def get_explosion_area(self):
        """获取爆炸范围"""
        return "fullscreen"

    def should_play_explosion_sound(self):
        """检查是否应该播放爆炸音效"""
        return (self.explode_timer >= self.sound_trigger_frame and
                not self.explosion_sound_played)

    def mark_sound_played(self):
        """标记爆炸音效已播放"""
        self.explosion_sound_played = True

    def get_countdown_remaining(self):
        """获取剩余倒计时帧数"""
        return max(0, self.explode_delay - self.explode_timer)

    def take_damage(self, damage):
        """植物受到伤害"""
        super().take_damage(damage)

        # 如果血量归零，立即标记需要检查爆炸
        if self.health <= 0:
            self._needs_explosion_check = True

    def can_shoot(self):
        """黄瓜不能射击"""
        return False

    def reset_shoot_timer(self):
        """黄瓜没有射击计时器"""
        pass

    def check_for_new_wave(self, has_target_now):
        """黄瓜不需要检测新波次"""
        pass

    def find_nearest_zombie(self, zombies):
        """黄瓜不需要寻找僵尸"""
        return None

    def is_alive(self):
        """检查植物是否存活"""
        # 爆炸植物即使血量为0，在爆炸动画未完成前仍算"存活"
        return not self.should_be_removed

    def get_explosion_status(self):
        """获取爆炸植物的状态信息"""
        return {
            'plant_type': self.plant_type,
            'has_exploded': self.has_exploded,
            'explosion_started': self.explosion_started,
            'should_be_removed': self.should_be_removed,
            'health': self.health,
            'explode_timer': self.explode_timer,
            'explode_delay': self.explode_delay,
            'explosion_particle_count': len(self.explosion_particles) if self.explosion_particles else 0,
            'spray_particle_count': len(self.spray_particles) if self.spray_particles else 0
        }

    def draw(self, surface):
        """绘制黄瓜"""
        if not self.constants:
            return

        # 如果已开始爆炸，只绘制粒子
        if self.explosion_started:
            self.draw_explosion_particles(surface)
            self.draw_spray_particles(surface)
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('cucumber_img'):
            self.draw_cucumber(surface, self.images['cucumber_img'], x, y)
        else:
            # 默认淡绿色圆形
            pygame.draw.circle(surface, (144, 238, 144),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

    def draw_cucumber(self, surface, img, x, y):
        """绘制黄瓜（带缩放和绿色发光效果）"""
        # 计算当前缩放
        current_scale = self.scale

        # 添加脉冲效果（快爆炸时更明显）
        if self.explode_timer > 60:  # 最后1秒
            pulse_frequency = 0.25  # 稍慢的脉冲频率
            pulse_intensity = 0.08 * ((self.explode_timer - 60) / 60)
            pulse_effect = math.sin(self.pulse_timer * pulse_frequency) * pulse_intensity
            current_scale += pulse_effect

        # 确保缩放比例在合理范围内
        current_scale = max(0.8, min(current_scale, 1.8))

        # 计算缩放后的尺寸
        scaled_width = int(img.get_width() * current_scale)
        scaled_height = int(img.get_height() * current_scale)

        # 缩放图片
        if abs(current_scale - 1.0) > 0.01:
            scaled_img = pygame.transform.scale(img, (scaled_width, scaled_height))
        else:
            scaled_img = img

        # 计算居中绘制位置
        center_x = x + self.constants['GRID_SIZE'] // 2
        center_y = y + self.constants['GRID_SIZE'] // 2
        draw_x = center_x - scaled_img.get_width() // 2
        draw_y = center_y - scaled_img.get_height() // 2

        # 添加绿色发光效果（逐渐增强）
        if self.glow_intensity > 0:
            glow_surface = pygame.Surface((scaled_width + 30, scaled_height + 30), pygame.SRCALPHA)
            glow_color = (144, 238, 144, min(self.glow_intensity, 120))  # 淡绿色发光
            pygame.draw.circle(glow_surface, glow_color,
                               (glow_surface.get_width() // 2, glow_surface.get_height() // 2),
                               max(scaled_width, scaled_height) // 2 + 15)
            surface.blit(glow_surface, (draw_x - 15, draw_y - 15))

        # 绘制黄瓜
        surface.blit(scaled_img, (draw_x, draw_y))

    def draw_explosion_particles(self, surface):
        """绘制爆炸粒子"""
        for particle in self.explosion_particles:
            particle.draw(surface)

    def draw_spray_particles(self, surface):
        """绘制喷射粒子"""
        for particle in self.spray_particles:
            particle.draw(surface)