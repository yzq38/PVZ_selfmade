"""
樱桃炸弹植物类
"""
import pygame
import random
import math
from .base_plant import BasePlant
from .particles import ExplosionParticle


class CherryBomb(BasePlant):
    """樱桃炸弹：3x3范围爆炸伤害"""
    # 植物自描述信息
    PLANT_INFO = {
        'icon_key': 'cherry_bomb_60',
        'display_name': '樱桃炸弹',
        'category': 'explosive',
        'preview_alpha': 128,
    }
    def __init__(self, row, col, constants, images, level_manager):
        super().__init__(row, col, "cherry_bomb", constants, images, level_manager)

        # 爆炸参数
        self.explode_timer = 0
        self.explode_delay = 60
        self.explosion_damage = 1200
        self.has_exploded = False
        self.should_be_removed = False

        # 音效播放控制
        self.explosion_sound_played = False
        self.sound_trigger_frame = self.explode_delay - 10  # 在爆炸前10帧播放音效

        # 动画相关属性
        self.init_cherry_bomb_animation()

    def init_cherry_bomb_animation(self):
        """初始化樱桃炸弹动画特有属性"""
        # 缩放动画相关
        self.scale = 1.0
        self.max_scale = 1.5
        self.scale_timer = 0
        self.scale_interval = 45
        self.scale_step = 0.125

        # 爆炸相关
        self.explosion_started = False

        # 爆炸粒子
        self.explosion_particles = []
        self.particles_created = False

        # 爆炸属性
        self.explosion_range = 1  # 3x3范围

        # 视觉效果
        self.pulse_timer = 0

    def update(self):
        """更新樱桃炸弹状态"""
        # 更新脉冲效果
        self.pulse_timer += 1

        # 更新缩放动画
        if not self.explosion_started:
            self.scale_timer += 1
            if self.scale_timer >= self.scale_interval and self.scale < self.max_scale:
                self.scale = min(self.scale + self.scale_step, self.max_scale)
                self.scale_timer = 0

        # 累加爆炸计时器
        if not self.has_exploded:
            self.explode_timer += 1

            # 检查是否需要播放音效
            if (self.explode_timer >= self.sound_trigger_frame and
                    not self.explosion_sound_played):
                return "play_explosion_sound"

            # 检查爆炸触发条件
            should_explode = False

            # 条件1：正常倒计时结束
            if self.explode_timer >= self.explode_delay:
                should_explode = True

            # 条件2：被攻击死亡
            if self.health <= 0:
                should_explode = True

            # 触发爆炸
            if should_explode:
                self.explode()

        # 更新爆炸粒子
        if self.explosion_particles:
            self.explosion_particles = [p for p in self.explosion_particles if p.update()]

            # 如果粒子全部消失，标记为可移除
            if not self.explosion_particles and self.explosion_started:
                self.should_be_removed = True

        return 0

    def explode(self):
        """樱桃炸弹爆炸"""
        if not self.has_exploded:
            self.has_exploded = True
            self.explosion_started = True

            # 立即创建爆炸粒子
            self.create_explosion_particles()

            # 确保音效播放状态正确
            if not self.explosion_sound_played:
                self.explosion_sound_played = True

            return True
        return False

    def create_explosion_particles(self):
        """创建爆炸粒子"""
        if self.particles_created:
            return

        # 计算植物的像素位置
        center_x = (self.constants['BATTLEFIELD_LEFT'] +
                    self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                    self.constants['GRID_SIZE'] // 2)
        center_y = (self.constants['BATTLEFIELD_TOP'] +
                    self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP']) +
                    self.constants['GRID_SIZE'] // 2)

        # 创建红色粒子
        particle_count = random.randint(30, 50)
        for _ in range(particle_count):
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-20, 20)
            particle = ExplosionParticle(center_x + offset_x, center_y + offset_y)
            self.explosion_particles.append(particle)

        self.particles_created = True

    def get_explosion_area(self):
        """获取爆炸范围"""
        explosion_cells = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                explosion_cells.append((self.row + dr, self.col + dc))
        return explosion_cells

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
        """樱桃炸弹不能射击"""
        return False

    def reset_shoot_timer(self):
        """樱桃炸弹没有射击计时器"""
        pass

    def check_for_new_wave(self, has_target_now):
        """樱桃炸弹不需要检测新波次"""
        pass

    def find_nearest_zombie(self, zombies):
        """樱桃炸弹不需要寻找僵尸"""
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
            'explosion_particle_count': len(self.explosion_particles) if self.explosion_particles else 0
        }

    def draw(self, surface):
        """绘制樱桃炸弹"""
        if not self.constants:
            return

        # 如果已开始爆炸，只绘制粒子
        if self.explosion_started:
            self.draw_explosion_particles(surface)
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        if self.images and self.images.get('cherry_bomb_img'):
            self.draw_cherry_bomb(surface, self.images['cherry_bomb_img'], x, y)
        else:
            # 默认粉红色圆形
            pygame.draw.circle(surface, (255, 0, 100),
                               (x + self.constants['GRID_SIZE'] // 2,
                                y + self.constants['GRID_SIZE'] // 2),
                               self.constants['GRID_SIZE'] // 3)

    def draw_cherry_bomb(self, surface, img, x, y):
        """绘制樱桃炸弹（带缩放和脉冲效果）"""
        # 计算当前缩放
        current_scale = self.scale

        # 添加脉冲效果（快爆炸时更明显）
        if self.explode_timer > 60:  # 最后1秒
            pulse_frequency = 0.3
            pulse_intensity = 0.1 * ((self.explode_timer - 60) / 60)
            pulse_effect = math.sin(self.pulse_timer * pulse_frequency) * pulse_intensity
            current_scale += pulse_effect

        # 确保缩放比例在合理范围内
        current_scale = max(0.8, min(current_scale, 2.0))

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

        # 添加红色发光效果（快爆炸时）
        if self.explode_timer > 60:
            glow_intensity = int(100 * ((self.explode_timer - 60) / 60))
            glow_surface = pygame.Surface((scaled_width + 20, scaled_height + 20), pygame.SRCALPHA)
            glow_color = (255, 100, 100, glow_intensity)
            pygame.draw.circle(glow_surface, glow_color,
                               (glow_surface.get_width() // 2, glow_surface.get_height() // 2),
                               max(scaled_width, scaled_height) // 2 + 10)
            surface.blit(glow_surface, (draw_x - 10, draw_y - 10))

        # 绘制樱桃炸弹
        surface.blit(scaled_img, (draw_x, draw_y))

    def draw_explosion_particles(self, surface):
        """绘制爆炸粒子"""
        for particle in self.explosion_particles:
            particle.draw(surface)

    def get_explosion_targets(self, zombies):
        """获取爆炸目标 - 排除魅惑僵尸"""
        explosion_area = self.get_explosion_area()
        targets = []

        for zombie in zombies:
            # 跳过魅惑僵尸（它们属于植物阵营）
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

            zombie_row = zombie.row
            zombie_col = int(zombie.col)

            if (zombie_row, zombie_col) in explosion_area:
                targets.append(zombie)

        return targets

    def apply_explosion_damage(self, zombies):
        """对目标僵尸造成爆炸伤害"""
        targets = self.get_explosion_targets(zombies)

        for zombie in targets:
            # 标记被爆炸性伤害杀死（防止爆炸僵尸连锁爆炸）
            if hasattr(zombie, 'take_damage_from_explosion'):
                zombie.take_damage_from_explosion()

            # 造成爆炸伤害
            zombie.health -= self.explosion_damage

            # 检查是否死亡
            if zombie.health <= 0 and not zombie.is_dying:
                zombie.start_death_animation()

        return len(targets)  # 返回受影响的僵尸数量