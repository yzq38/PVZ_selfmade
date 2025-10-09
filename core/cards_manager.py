"""
卡牌管理器模块 - 统一管理植物卡牌的特性和可用性
"""
from enum import Enum
from typing import Dict, List, Optional, Union


class PlantType(Enum):
    """植物类型枚举"""
    LIGHTNING_FLOWER = "lightning_flower"
    SUNFLOWER = "sunflower"
    SHOOTER = "shooter"
    MELON_PULT = "melon_pult"
    CATTAIL = "cattail"
    WALL_NUT = "wall_nut"
    CHERRY_BOMB = "cherry_bomb"
    CUCUMBER = "cucumber"
    DANDELION = "dandelion"
    ICE_CACTUS = "ice_cactus"
    SUN_SHROOM = "sun_shroom"
    MOON_FLOWER = "moon_flower"
    LUKER = "luker"
    PSYCHEDELIC_PITCHER = "psychedelic_pitcher"



class CardInfo:
    """卡牌信息类"""

    def __init__(self,
                 plant_type: str,
                 name: str,
                 cost: int,
                 color: tuple,
                 cooldown_time: int = 0,
                 unlock_level: int = 1,
                 unlock_features: List[str] = None,
                 description: str = "",
                 image_key: str = None):
        """
        初始化卡牌信息

        Args:
            plant_type: 植物类型
            name: 植物名称
            cost: 阳光成本
            color: 卡牌颜色
            cooldown_time: 基础冷却时间（帧数）
            unlock_level: 解锁关卡
            unlock_features: 需要的特殊解锁特性
            description: 植物描述
            image_key: 图片资源键名
        """
        self.plant_type = plant_type
        self.name = name
        self.cost = cost
        self.color = color
        self.cooldown_time = cooldown_time
        self.unlock_level = unlock_level
        self.unlock_features = unlock_features or []
        self.description = description
        self.image_key = image_key or f"{plant_type}_img"

    def to_dict(self) -> Dict:
        """转换为字典格式，兼容现有代码"""
        return {
            "type": self.plant_type,
            "name": self.name,
            "cost": self.cost,
            "color": self.color
        }


class CardsManager:
    """卡牌管理器"""

    def __init__(self):
        self._cards_database = self._initialize_cards_database()

    def _initialize_cards_database(self) -> Dict[str, CardInfo]:
        """初始化卡牌数据库"""
        return {
            PlantType.SUNFLOWER.value: CardInfo(
                plant_type=PlantType.SUNFLOWER.value,
                name="向日葵",
                cost=50,
                color=(255, 204, 0),
                cooldown_time=120,  # 2秒
                unlock_level=1,
                description="产生阳光的基础植物"
            ),

            PlantType.SHOOTER.value: CardInfo(
                plant_type=PlantType.SHOOTER.value,
                name="豌豆射手",
                cost=75,
                color=(0, 255, 0),
                cooldown_time=120,  # 2秒
                unlock_level=1,
                description="发射豌豆攻击僵尸"
            ),

            PlantType.MELON_PULT.value: CardInfo(
                plant_type=PlantType.MELON_PULT.value,
                name="西瓜投手",
                cost=275,
                color=(255, 100, 100),
                cooldown_time=480,  # 8秒
                unlock_level=5,
                unlock_features=["melon_pult_available"],
                description="发射高伤害的西瓜，具有溅射效果"
            ),

            PlantType.CATTAIL.value: CardInfo(
                plant_type=PlantType.CATTAIL.value,
                name="猫尾草",
                cost=225,
                color=(128, 0, 128),
                cooldown_time=1200,  # 20秒
                unlock_level=10,
                unlock_features=["cattail_available"],
                description="发射追踪尖刺，可攻击任意位置的僵尸"
            ),


            PlantType.WALL_NUT.value: CardInfo(
                plant_type=PlantType.WALL_NUT.value,
                name="坚果墙",
                cost=50,
                color=(139, 69, 19),
                cooldown_time=1200,
                unlock_level=11,
                unlock_features=["wall_nut_available"],
                description="高血量防御植物"
            ),

            PlantType.CHERRY_BOMB.value: CardInfo(
                plant_type=PlantType.CHERRY_BOMB.value,
                name="樱桃炸弹",
                cost=150,
                color=(255, 0, 0),
                cooldown_time=1200,  # 20秒
                unlock_level=12,
                unlock_features=["cherry_bomb_available"],
                description="对大范围内的敌人造成巨大伤害"
            ),
            PlantType.CUCUMBER.value: CardInfo(
                plant_type=PlantType.CUCUMBER.value,
                name="黄瓜",
                cost=200,
                color=(255, 0, 0),
                cooldown_time=1200,  # 20秒
                unlock_level=14,
                unlock_features=["cucumber_available"],
                description="对大范围内的敌人造成眩晕并概率致其兴奋死亡"
            ),
            PlantType.DANDELION.value: CardInfo(
                plant_type=PlantType.DANDELION.value,
                name="蒲公英",
                cost=175,
                color=(255, 0, 0),
                cooldown_time=600,
                unlock_level=15,
                unlock_features=["dandelion_available"],
                description="随机发射5颗蒲公英种子锁定僵尸"
            ),
            PlantType.LIGHTNING_FLOWER.value: CardInfo(
                plant_type=PlantType.LIGHTNING_FLOWER.value,
                name="闪电花",
                cost=300,
                color=(255, 0, 0),
                cooldown_time=600,
                unlock_level=16,
                unlock_features=["lightning_flower_available"],
                description="向前发射一道闪电"
            ),
            PlantType.ICE_CACTUS.value: CardInfo(
                plant_type=PlantType.ICE_CACTUS.value,
                name="寒冰仙人掌",
                cost=200,
                color=(255, 0, 0),
                cooldown_time=600,
                unlock_level=17,
                unlock_features=["ice_cactus_available"],
                description="发射寒冰穿透子弹"
            ),
            PlantType.SUN_SHROOM.value: CardInfo(
                plant_type=PlantType.SUN_SHROOM.value,
                name="阳光菇",
                cost=25,  # 比向日葵便宜一半映射
                color=(200, 150, 255),  # 淡紫色
                cooldown_time=120,  # 2秒
                unlock_level=22,
                unlock_features=["sun_shroom_available"],
                description="产生阳光，但速率比向日葵慢20%"
            ),
            PlantType.MOON_FLOWER.value: CardInfo(
                plant_type=PlantType.MOON_FLOWER.value,
                name="月亮花",
                cost=125,
                color=(100, 100, 200),  # 深蓝紫色
                cooldown_time=480,  # 8秒
                unlock_level=23,
                unlock_features=["moon_flower_available"],
                description="发射月亮子弹，每个月亮花提供10%攻速加成(最高50%)"
            ),
            PlantType.LUKER.value: CardInfo(
                plant_type=PlantType.LUKER.value,
                name="地刺",
                cost=75,
                color=(64, 64, 64),  # 深灰色
                cooldown_time=480,  # 8秒
                unlock_level=24,
                unlock_features=["luker_available"],
                description="地面防守植物，无视僵尸防具，可秒杀车子类僵尸"
            ),
            PlantType.PSYCHEDELIC_PITCHER.value: CardInfo(
                plant_type=PlantType.PSYCHEDELIC_PITCHER.value,
                name="迷幻投手",
                cost=125,
                color=(64, 64, 64),  # 深灰色
                cooldown_time=480,  # 8秒
                unlock_level=25,
                unlock_features=["psychedelic_pitcher_available"],
                description="魅惑僵尸使其暂时为你作战"
            ),
        }

    def get_card_info(self, plant_type: str) -> Optional[CardInfo]:
        """获取指定植物的卡牌信息"""
        return self._cards_database.get(plant_type)

    def get_all_cards(self) -> Dict[str, CardInfo]:
        """获取所有卡牌信息"""
        return self._cards_database.copy()

    def is_card_unlocked(self, plant_type: str, current_level: int, level_manager=None) -> bool:
        """
        检查卡牌是否解锁 - 更新：完全使用特性管理系统

        Args:
            plant_type: 植物类型
            current_level: 当前关卡
            level_manager: 关卡管理器，用于检查特殊特性

        Returns:
            bool: 是否已解锁
        """
        card_info = self.get_card_info(plant_type)
        if not card_info:
            return False

        # 🔧 新增：检查是否禁用向日葵
        if plant_type in ["sunflower", "sun_shroom"] and level_manager:
            if level_manager.has_special_feature("no_sunflower"):
                return False  # 禁用向日葵相关卡牌

        # 检查关卡解锁条件
        if current_level < card_info.unlock_level:
            return False

        # 检查特殊特性解锁条件 - 修改：使用统一的特性管理器接口
        if card_info.unlock_features and level_manager:
            for feature in card_info.unlock_features:
                # 使用 level_manager 的统一接口，内部会调用特性管理器
                if not level_manager.has_special_feature(feature):
                    return False

        return True

    def get_available_cards(self, current_level: int, level_manager=None,
                            selected_plants: List[str] = None) -> List[Dict]:
        """
        获取当前关卡可用的卡牌列表 - 更新：使用特性管理系统

        Args:
            current_level: 当前关卡
            level_manager: 关卡管理器
            selected_plants: 已选择的植物列表（用于植物选择模式）

        Returns:
            List[Dict]: 可用卡牌列表，格式兼容现有代码
        """
        available_cards = []

        if selected_plants:
            # 植物选择模式：使用玩家选择的植物
            for plant_type in selected_plants:
                card_info = self.get_card_info(plant_type)
                if card_info and self.is_card_unlocked(plant_type, current_level, level_manager):
                    available_cards.append(card_info.to_dict())
        else:
            # 普通模式：根据关卡自动确定可用植物
            for plant_type, card_info in self._cards_database.items():
                if self.is_card_unlocked(plant_type, current_level, level_manager):
                    available_cards.append(card_info.to_dict())

        return available_cards

    def get_plant_select_grid_data(self, current_level: int, level_manager=None) -> List[List[Optional[Dict]]]:
        """
        获取植物选择网格数据（6×5） - 更新：使用特性管理系统

        Args:
            current_level: 当前关卡
            level_manager: 关卡管理器

        Returns:
            List[List[Optional[Dict]]]: 6×5网格数据
        """
        # 获取所有已解锁的植物 - 使用更新后的解锁检查
        unlocked_plants = []
        for plant_type, card_info in self._cards_database.items():
            if self.is_card_unlocked(plant_type, current_level, level_manager):
                unlocked_plants.append({
                    'type': card_info.plant_type,
                    'name': card_info.name,
                    'cost': card_info.cost,
                    'description': card_info.description
                })

        # 创建6×5网格
        grid = []
        plant_index = 0

        for row in range(5):
            grid_row = []
            for col in range(6):
                if plant_index < len(unlocked_plants):
                    grid_row.append(unlocked_plants[plant_index])
                    plant_index += 1
                else:
                    grid_row.append(None)  # 空槽位
            grid.append(grid_row)

        return grid

    def get_card_cooldown_time(self, plant_type: str, level_manager=None) -> int:
        """
        获取卡牌冷却时间 - 统一管理，支持第八关特殊处理

        Args:
            plant_type: 植物类型
            level_manager: 关卡管理器，用于获取关卡特定的冷却时间

        Returns:
            int: 冷却时间（帧数）
        """
        card_info = self.get_card_info(plant_type)
        if not card_info:
            return 0

        # 获取基础冷却时间（所有关卡都使用卡牌管理器中定义的时间）
        base_cooldown = card_info.cooldown_time

        # 第八关特殊处理：在基础冷却时间上增加1秒
        if level_manager and level_manager.current_level == 8:
            base_cooldown += 60  # 增加1秒（60帧）

        # 所有其他关卡都使用卡牌管理器中定义的基础冷却时间，忽略配置文件设置
        return base_cooldown

    def get_card_cost(self, plant_type: str, level_manager=None) -> int:
        """
        获取卡牌成本

        Args:
            plant_type: 植物类型
            level_manager: 关卡管理器，可用于未来的成本修改特性

        Returns:
            int: 阳光成本
        """
        card_info = self.get_card_info(plant_type)
        if not card_info:
            return 0

        # 这里可以添加关卡特性对成本的修改
        # 例如：if level_manager and level_manager.has_special_feature('plant_cost_reduction'):
        #          return int(card_info.cost * 0.8)

        return card_info.cost

    def get_card_color(self, plant_type: str) -> tuple:
        """获取卡牌颜色"""
        card_info = self.get_card_info(plant_type)
        return card_info.color if card_info else (255, 255, 255)

    def get_card_name(self, plant_type: str) -> str:
        """获取卡牌名称"""
        card_info = self.get_card_info(plant_type)
        return card_info.name if card_info else plant_type

    def get_cards_by_unlock_level(self, level: int) -> List[CardInfo]:
        """获取指定关卡解锁的卡牌"""
        return [card for card in self._cards_database.values()
                if card.unlock_level == level]

    def add_custom_card(self, card_info: CardInfo) -> bool:
        """
        添加自定义卡牌

        Args:
            card_info: 卡牌信息

        Returns:
            bool: 是否添加成功
        """
        if card_info.plant_type in self._cards_database:
            return False  # 卡牌已存在

        self._cards_database[card_info.plant_type] = card_info
        return True

    def update_card_property(self, plant_type: str, property_name: str, value) -> bool:
        """
        更新卡牌属性

        Args:
            plant_type: 植物类型
            property_name: 属性名
            value: 新值

        Returns:
            bool: 是否更新成功
        """
        card_info = self.get_card_info(plant_type)
        if not card_info or not hasattr(card_info, property_name):
            return False

        setattr(card_info, property_name, value)
        return True


# 全局卡牌管理器实例
cards_manager = CardsManager()


def get_available_cards_new(level_manager, level_settings=None, selected_plants=None):
    """
    新的获取可用卡牌函数，兼容现有代码
    这个函数可以替代 game_logic.py 中的 get_available_cards 函数
    更新：完全使用特性管理系统
    """
    current_level = level_manager.current_level if level_manager else 1
    return cards_manager.get_available_cards(current_level, level_manager, selected_plants)


def get_plant_select_grid_new(level_manager):
    """
    新的获取植物选择网格函数
    这个函数可以替代 main.py 中的 init_plant_select_grid 函数
    更新：完全使用特性管理系统
    """
    current_level = level_manager.current_level if level_manager else 1
    return cards_manager.get_plant_select_grid_data(current_level, level_manager)