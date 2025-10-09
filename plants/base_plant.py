"""
基础植物类 - 包含自描述功能
"""
import random
import pygame


class BasePlant:
    """基础植物类，包含所有植物共享的属性和方法"""

    # 类级别的植物信息
    PLANT_INFO = {
        'icon_key': None,  # 图标键名
        'display_name': 'Unknown',  # 显示名称
        'category': 'other',  # 植物分类
        'preview_alpha': 128,  # 预览透明度
    }

    def __init__(self, row, col, plant_type=None, constants=None, images=None, level_manager=None):
        self.row = row
        self.col = col
        self.plant_type = plant_type

        # 根据植物类型设置血量和最大血量
        if plant_type == "wall_nut":
            self.health = 1500
            self.max_health = 1500  # 坚果墙最大血量
        else:
            self.health = 100
            self.max_health = 100  # 其他植物最大血量

        # 存储常量和图片引用
        self.constants = constants
        self.images = images
        self.level_manager = level_manager

        # 初始化爆炸相关属性为False
        self.has_exploded = False
        self.should_be_removed = False
        self.explosion_sound_played = False

    @classmethod
    def get_icon_key(cls):
        """获取植物图标键名"""
        return cls.PLANT_INFO.get('icon_key') or f"{cls.get_plant_type()}_60"

    @classmethod
    def get_display_name(cls):
        """获取植物显示名称"""
        return cls.PLANT_INFO.get('display_name', cls.get_plant_type())

    @classmethod
    def get_category(cls):
        """获取植物分类"""
        return cls.PLANT_INFO.get('category', 'other')

    @classmethod
    def get_plant_type(cls):
        """获取植物类型标识"""
        # 默认使用类名的小写形式，去掉Plant后缀
        class_name = cls.__name__.lower()
        if class_name.endswith('plant'):
            class_name = class_name[:-5]
        # 特殊处理一些类名
        type_mapping = {
            'sunflower': 'sunflower',
            'shooter': 'shooter',
            'wallnut': 'wall_nut',
            'cherrybomb': 'cherry_bomb',
            'cucumber': 'cucumber',
            'melonpult': 'melon_pult',
            'cattail': 'cattail',
            'dandelion': 'dandelion',
            'icecactus': 'ice_cactus',
            'lightningflower': 'lightning_flower',
            'sunshroom':'sun_shroom',
            'moonflower':'moon_flower',
            'psychedelicpitcher':'psychedelic_pitcher',
        }
        return type_mapping.get(class_name, class_name)

    @classmethod
    def get_preview_alpha(cls):
        """获取预览透明度"""
        return cls.PLANT_INFO.get('preview_alpha', 128)

    def take_damage(self, damage):
        """植物受到伤害"""
        if self.health <= 0:
            return

        self.health -= damage
        self.health = max(0, self.health)

    def is_alive(self):
        """检查植物是否存活"""
        return self.health > 0

    def update(self):
        """更新植物状态 - 基类默认返回0"""
        return 0

    def draw(self, surface):
        """绘制植物和血条 - 基础绘制方法"""
        if not self.constants:
            return

        x = self.constants['BATTLEFIELD_LEFT'] + self.col * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])
        y = self.constants['BATTLEFIELD_TOP'] + self.row * (self.constants['GRID_SIZE'] + self.constants['GRID_GAP'])

        # 默认圆形绘制
        color = self.constants.get('WHITE', (255, 255, 255))
        pygame.draw.circle(surface, color,
                           (x + self.constants['GRID_SIZE'] // 2,
                            y + self.constants['GRID_SIZE'] // 2),
                           self.constants['GRID_SIZE'] // 3)

        # 绘制血条
        self._draw_health_bar(surface, x, y)

    def can_shoot(self):
        """检查是否可以射击 - 基类默认返回False"""
        return False

    def reset_shoot_timer(self):
        """重置射击计时器 - 基类默认实现"""
        pass

    def check_for_new_wave(self, has_target_now):
        """检测新僵尸波次 - 基类默认实现"""
        pass

    def find_nearest_zombie(self, zombies):
        """寻找最近的僵尸 - 基类默认返回None"""
        return None

    def _draw_health_bar(self, surface, x, y):
        """绘制植物血条"""
        should_show_health_bar = (self.health < self.max_health and
                                  self.plant_type not in ["cherry_bomb", "cucumber"])

        if should_show_health_bar:
            health_bar_width = self.constants['GRID_SIZE']
            health_bar_height = 6
            health_bar_x = x
            health_bar_y = y + self.constants['GRID_SIZE'] + 2

            # 血条背景（红色）
            pygame.draw.rect(surface, self.constants['RED'],
                             (health_bar_x, health_bar_y, health_bar_width, health_bar_height))

            # 当前血量条
            health_percentage = self.health / self.max_health
            current_health_width = int(health_percentage * health_bar_width)

            # 根据血量百分比选择颜色
            if health_percentage > 0.6:
                health_color = self.constants['GREEN']
            elif health_percentage > 0.3:
                health_color = (255, 255, 0)  # 黄色
            else:
                health_color = (255, 165, 0)  # 橙色

            if current_health_width > 0:
                pygame.draw.rect(surface, health_color,
                                 (health_bar_x, health_bar_y, current_health_width, health_bar_height))

            # 血条边框
            pygame.draw.rect(surface, (0, 0, 0),
                             (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 1)