"""
植物注册系统 - 与 CardsManager 集成
"""
import pygame


class PlantRegistry:
    """植物注册表 - 自动收集所有植物类的信息，并与 CardsManager 集成"""

    def __init__(self):
        self._plants = {}  # plant_type -> plant_class
        self._cards_manager = None  # 引用 CardsManager
        self._level_manager = None  # 引用 LevelManager
        self._initialized = False

    def set_managers(self, cards_manager, level_manager=None):
        """设置管理器引用"""
        self._cards_manager = cards_manager
        self._level_manager = level_manager
        self._initialized = True

    def register(self, plant_class):
        """注册植物类"""
        plant_type = plant_class.get_plant_type()
        self._plants[plant_type] = plant_class
        return plant_class  # 返回类本身，可以用作装饰器

    def get_plant_class(self, plant_type):
        """获取植物类"""
        return self._plants.get(plant_type)

    def get_plant_price(self, plant_type):
        """获取植物价格 - 从 CardsManager 获取"""
        if self._cards_manager:
            return self._cards_manager.get_card_cost(plant_type, self._level_manager)
        return 0

    def get_plant_cooldown(self, plant_type):
        """获取植物冷却时间 - 从 CardsManager 获取"""
        if self._cards_manager:
            return self._cards_manager.get_card_cooldown_time(plant_type, self._level_manager)
        return 0

    def get_plant_name(self, plant_type):
        """获取植物名称 - 从 CardsManager 获取"""
        if self._cards_manager:
            return self._cards_manager.get_card_name(plant_type)
        return plant_type

    def get_plant_color(self, plant_type):
        """获取植物颜色 - 从 CardsManager 获取"""
        if self._cards_manager:
            return self._cards_manager.get_card_color(plant_type)
        return (255, 255, 255)

    def is_plant_unlocked(self, plant_type, current_level=None):
        """检查植物是否解锁 - 从 CardsManager 获取"""
        if not self._cards_manager:
            return False

        level = current_level if current_level is not None else (
            self._level_manager.current_level if self._level_manager else 1
        )
        return self._cards_manager.is_card_unlocked(plant_type, level, self._level_manager)

    def get_plant_icon_key(self, plant_type):
        """获取植物图标键名"""
        plant_class = self._plants.get(plant_type)
        if plant_class:
            return plant_class.get_icon_key()
        # 如果找不到，使用命名约定
        return f"{plant_type}_60"

    def get_plant_display_name(self, plant_type):
        """获取植物显示名称 - 优先使用 CardsManager"""
        if self._cards_manager:
            return self._cards_manager.get_card_name(plant_type)

        plant_class = self._plants.get(plant_type)
        return plant_class.get_display_name() if plant_class else plant_type

    def get_plant_category(self, plant_type):
        """获取植物分类"""
        plant_class = self._plants.get(plant_type)
        return plant_class.get_category() if plant_class else 'other'

    def get_preview_alpha(self, plant_type):
        """获取预览透明度"""
        plant_class = self._plants.get(plant_type)
        return plant_class.get_preview_alpha() if plant_class else 128

    def get_all_plants_by_category(self, category):
        """按分类获取植物"""
        return [plant_type for plant_type, plant_class in self._plants.items()
                if plant_class.get_category() == category]

    def get_all_plants(self):
        """获取所有已注册的植物类型"""
        return list(self._plants.keys())

    def get_available_plants(self, current_level=None):
        """获取当前可用的植物列表"""
        if not self._cards_manager:
            return []

        level = current_level if current_level is not None else (
            self._level_manager.current_level if self._level_manager else 1
        )

        available_cards = self._cards_manager.get_available_cards(level, self._level_manager)
        return [card['type'] for card in available_cards]

    def is_registered(self, plant_type):
        """检查植物是否已注册"""
        return plant_type in self._plants

    def get_plant_info(self, plant_type):
        """获取植物的完整信息"""
        return {
            'type': plant_type,
            'display_name': self.get_plant_display_name(plant_type),
            'price': self.get_plant_price(plant_type),
            'cooldown': self.get_plant_cooldown(plant_type),
            'category': self.get_plant_category(plant_type),
            'icon_key': self.get_plant_icon_key(plant_type),
            'preview_alpha': self.get_preview_alpha(plant_type),
            'color': self.get_plant_color(plant_type),
            'unlocked': self.is_plant_unlocked(plant_type)
        }

    def get_plant_select_grid_data(self, current_level=None):
        """获取植物选择网格数据 - 直接从 CardsManager 获取"""
        if not self._cards_manager:
            return []

        level = current_level if current_level is not None else (
            self._level_manager.current_level if self._level_manager else 1
        )

        return self._cards_manager.get_plant_select_grid_data(level, self._level_manager)


# 全局植物注册表单例
plant_registry = PlantRegistry()