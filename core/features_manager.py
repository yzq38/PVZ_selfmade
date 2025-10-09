"""
特性管理器模块 - 统一管理所有关卡特性
"""
from enum import Enum
from typing import Dict, List, Optional, Union


class FeatureCategory(Enum):
    """特性分类枚举"""
    BULLET = "bullet"  # 子弹相关
    PLANT = "plant"  # 植物相关
    ZOMBIE = "zombie"  # 僵尸相关
    ECONOMY = "economy"  # 经济相关
    UNLOCK = "unlock"  # 解锁相关
    GAMEPLAY = "gameplay"  # 游戏玩法
    ENVIRONMENT = "environment"  # 环境相关


class FeatureInfo:
    """特性信息类"""

    def __init__(self,
                 feature_id: str,
                 name: str,
                 description: str,
                 category: FeatureCategory = FeatureCategory.GAMEPLAY,
                 min_level: int = 1,
                 conflicts_with: List[str] = None,
                 requires: List[str] = None,
                 default_value=None):
        """
        初始化特性信息

        Args:
            feature_id: 特性ID
            name: 特性名称
            description: 特性描述
            category: 特性分类
            min_level: 最低关卡要求
            conflicts_with: 冲突的特性列表
            requires: 依赖的特性列表
            default_value: 默认值（如果特性有参数）
        """
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.category = category
        self.min_level = min_level
        self.conflicts_with = conflicts_with or []
        self.requires = requires or []
        self.default_value = default_value


class FeaturesManager:
    """特性管理器"""

    def __init__(self):
        self._features = self._initialize_features()

    def _initialize_features(self) -> Dict[str, FeatureInfo]:
        """初始化所有特性"""
        return {
            # 子弹相关特性
            "bullet_penetration": FeatureInfo(
                "bullet_penetration",
                "子弹穿透",
                "豌豆子弹可以穿透僵尸",
                FeatureCategory.BULLET,
                min_level=2
            ),

            "random_penetration": FeatureInfo(
                "random_penetration",
                "随机穿透",
                "子弹有随机概率穿透僵尸",
                FeatureCategory.BULLET,
                min_level=4,
                conflicts_with=["bullet_penetration"],
                default_value=0.15
            ),

            # 植物相关特性
            "sunflower_limit": FeatureInfo(
                "sunflower_limit",
                "向日葵限制",
                "限制向日葵种植数量",
                FeatureCategory.PLANT,
                min_level=2,
                conflicts_with=["no_sunflower"],
                default_value=3
            ),

            # 第四关专用的向日葵限制特性
            "sunflower_limit_1": FeatureInfo(
                "sunflower_limit_1",
                "向日葵限制(1棵)",
                "只能种植1棵向日葵",
                FeatureCategory.PLANT,
                min_level=4,
                conflicts_with=["no_sunflower", "sunflower_limit"],
                default_value=1
            ),

            "no_sunflower": FeatureInfo(
                "no_sunflower",
                "禁用向日葵",
                "完全禁止种植向日葵",
                FeatureCategory.PLANT,
                min_level=4,
                conflicts_with=["sunflower_limit", "sunflower_limit_1"]
            ),

            "plant_speed_boost": FeatureInfo(
                "plant_speed_boost",
                "植物加速",
                "植物攻击和生产速度提升",
                FeatureCategory.PLANT,
                min_level=7,
                default_value=1.5
            ),

            "card_cooldown": FeatureInfo(
                "card_cooldown",
                "卡片冷却",
                "植物卡片需要冷却时间",
                FeatureCategory.PLANT,
                min_level=8,
                default_value=180
            ),

            # 解锁相关特性
            "melon_pult_available": FeatureInfo(
                "melon_pult_available",
                "解锁西瓜投手",
                "西瓜投手可以使用",
                FeatureCategory.UNLOCK,
                min_level=5
            ),

            "cattail_available": FeatureInfo(
                "cattail_available",
                "解锁猫尾草",
                "猫尾草可以使用",
                FeatureCategory.UNLOCK,
                min_level=10
            ),
            "cherry_bomb_available": FeatureInfo(
                "cherry_bomb_available",
                "解锁樱桃炸弹",
                "樱桃炸弹可以使用",
                FeatureCategory.UNLOCK,
                min_level=12
            ),
            "wall_nut_available": FeatureInfo(
                "wall_nut_available",
                "解锁坚果墙",
                "坚果墙可以使用",
                FeatureCategory.UNLOCK,
                min_level=11
            ),

            # 黄瓜解锁特性
            "cucumber_available": FeatureInfo(
                "cucumber_available",
                "解锁黄瓜",
                "黄瓜可以使用",
                FeatureCategory.UNLOCK,
                min_level=14
            ),
            # 解锁特性
            "dandelion_available": FeatureInfo(
                "dandelion_available",
                "解锁蒲公英",
                "蒲公英可以使用",
                FeatureCategory.UNLOCK,
                min_level=15
            ),
            "lightning_flower_available": FeatureInfo(
                "lightning_flower_available",
                "解锁闪电花",
                "闪电花可以使用",
                FeatureCategory.UNLOCK,
                min_level=16
            ),
            "ice_cactus_available": FeatureInfo(
                "ice_cactus_available",
                "解锁寒冰仙人掌",
                "寒冰仙人掌",
                FeatureCategory.UNLOCK,
                min_level=17
            ),
            "moon_flower_available": FeatureInfo(
                "moon_flower_available",
                "解锁月亮花",
                "月亮花可以使用",
                FeatureCategory.UNLOCK,
                min_level=23
            ),
            "luker_available": FeatureInfo(
                "luker_available",
                "解锁地刺",
                "地刺可以使用",
                FeatureCategory.UNLOCK,
                min_level=24
            ),
            "psychedelic_pitcher_available": FeatureInfo(
                "psychedelic_pitcher_available",
                "解锁迷幻投手",
                "迷幻投手可以使用",
                FeatureCategory.UNLOCK,
                min_level=25
            ),
            "sunflower_no_produce": FeatureInfo(
                "sunflower_no_produce",
                "向日葵停产",
                "向日葵不再生产阳光",
                FeatureCategory.PLANT,
                min_level=22
            ),
            "sun_shroom_available": FeatureInfo(
                "sun_shroom_available",
                "解锁阳光蘑",
                "阳光蘑可以使用",
                FeatureCategory.UNLOCK,
                min_level=22
            ),

            # 僵尸相关特性
            "high_armor_rate": FeatureInfo(
                "high_armor_rate",
                "高铁门率",
                "提高铁门僵尸出现概率",
                FeatureCategory.ZOMBIE,
                min_level=3,
                default_value=0.7
            ),
            "giant_zombie_spawn": FeatureInfo(
                "giant_zombie_spawn",
                "巨人僵尸出现",
                "第13关及以后会出现巨人僵尸",
                FeatureCategory.ZOMBIE,
                min_level=13,
            ),
            "exploding_zombie_spawn": FeatureInfo(
                "exploding_zombie_spawn",
                "爆炸僵尸出现",
                "第19关及以后会出现爆炸僵尸，死亡时3x3爆炸",
                FeatureCategory.ZOMBIE,
                min_level=19,
                default_value=0.15  # 15%生成概率
            ),

            # 新增：冰车僵尸特性
            "ice_car_zombie_spawn": FeatureInfo(
                "ice_car_zombie_spawn",
                "冰车僵尸出现",
                "第24关会出现冰车僵尸，免疫寒冰，碾压植物，留下冰道加速其他僵尸",
                FeatureCategory.ZOMBIE,
                min_level=24,
                default_value=0.12  # 12%生成概率
            ),

            "all_fast_zombies": FeatureInfo(
                "all_fast_zombies",
                "全员快速",
                "所有僵尸都是快速僵尸",
                FeatureCategory.ZOMBIE,
                min_level=7
            ),

            "zombie_immunity": FeatureInfo(
                "zombie_immunity",
                "僵尸免疫",
                "僵尸有概率免疫一次伤害",
                FeatureCategory.ZOMBIE,
                min_level=6,
                default_value=0.05
            ),

            "zombie_health_reduce": FeatureInfo(
                "zombie_health_reduce",
                "僵尸血量减少",
                "僵尸血量减少20%",
                FeatureCategory.ZOMBIE,
                min_level=3,
                default_value=0.8
            ),
            "high_spawn_rate_wave": FeatureInfo(
                "high_spawn_rate_wave",
                "波次高生成率",
                "波次模式下巨人和爆炸僵尸生成率提升",
                FeatureCategory.ZOMBIE,
                min_level=20,
                default_value={
                    "giant_spawn_rate": 0.35,
                    "exploding_spawn_rate": 0.40
                }
            ),
            "conveyor_belt": FeatureInfo(
                "conveyor_belt",
                "传送带系统",
                "植物卡牌在传送带上从右往左移动，取代传统卡槽系统",
                FeatureCategory.GAMEPLAY,
                min_level=21,
                default_value={
                    "belt_speed": 0.5,  # 传送带速度（像素/帧）
                    "card_spawn_interval": 240,  # 新卡牌生成间隔（帧）
                    "max_cards_on_belt": 11,  # 传送带上最多卡牌数
                    "card_types": None,  # 可出现的植物类型，None表示所有可用植物
                    "random_spawn": True  # 是否随机生成卡牌
                }
            ),
            "seed_rain": FeatureInfo(
                "seed_rain",
                "种子雨",
                "从天而降的植物卡牌，每4秒出现一张，点击可选中使用",
                FeatureCategory.GAMEPLAY,
                min_level=27,
                default_value={
                    "spawn_interval": 240,  # 4秒
                    "wait_duration": 480,  # 8秒
                    "fall_speed": 1.0,  # 下降速度
                    "card_types": None  # 可掉落的植物类型，None表示所有可用植物
                }
            ),
            # 经济相关特性
            "no_sun_drop": FeatureInfo(
                "no_sun_drop",
                "无阳光掉落",
                "波次模式下不掉落阳光",
                FeatureCategory.ECONOMY,
                min_level=4,
                conflicts_with=["random_sun_drop"]
            ),

            "random_sun_drop": FeatureInfo(
                "random_sun_drop",
                "随机阳光",
                "僵尸只随机掉落5或10阳光",
                FeatureCategory.ECONOMY,
                min_level=1,
                conflicts_with=["no_sun_drop"]
            ),

            "increased_initial_sun": FeatureInfo(
                "increased_initial_sun",
                "初始阳光增加",
                "关卡开始时有更多阳光",
                FeatureCategory.ECONOMY,
                min_level=1,
                default_value=200
            ),
            "zombie_sun_reduce": FeatureInfo(
                "zombie_sun_reduce",
                "僵尸阳光减半",
                "僵尸掉落的阳光减少50%",
                FeatureCategory.ECONOMY,
                min_level=22,
                default_value=0.5  # 50%倍率
            ),

            "no_natural_sun": FeatureInfo(
                "no_natural_sun",
                "无自然阳光",
                "不会自然掉落阳光",
                FeatureCategory.ECONOMY,
                min_level=22
            ),
            "night": FeatureInfo(
                "night",
                "暗夜模式",
                "关卡在黑暗中进行，阳光受限",
                FeatureCategory.ENVIRONMENT,
                min_level=22
            ),
            # 环境相关特性 - 新增传送门特性
            "portal_system": FeatureInfo(
                "portal_system",
                "传送门系统",
                "在草坪右侧生成2个传送门，每20秒随机切换位置，僵尸可以通过传送门传送",
                FeatureCategory.ENVIRONMENT,
                min_level=18,
                default_value={
                    "portal_count": 2,
                    "switch_interval": 20,  # 秒
                    "spawn_columns": [5, 6, 7, 8, 9],  # 右侧5列
                    "teleport_chance": 0.3  # 僵尸经过传送门时的传送概率
                }
            ),
        }

    def get_feature(self, feature_id: str) -> Optional[FeatureInfo]:
        """获取特性信息"""
        return self._features.get(feature_id)

    def get_all_features(self) -> Dict[str, FeatureInfo]:
        """获取所有特性"""
        return self._features.copy()

    def get_features_by_category(self, category: FeatureCategory) -> Dict[str, FeatureInfo]:
        """按分类获取特性"""
        return {
            feature_id: feature for feature_id, feature in self._features.items()
            if feature.category == category
        }

    def get_available_features_for_level(self, level: int) -> Dict[str, FeatureInfo]:
        """获取指定关卡可用的特性"""
        return {
            feature_id: feature for feature_id, feature in self._features.items()
            if feature.min_level <= level
        }

    def validate_feature_combination(self, features: List[str]) -> tuple[bool, List[str]]:
        """
        验证特性组合是否有效

        Returns:
            tuple: (是否有效, 冲突信息列表)
        """
        conflicts = []

        # 检查特性是否存在
        for feature_id in features:
            if feature_id not in self._features:
                conflicts.append(f"未知特性: {feature_id}")

        # 检查冲突
        for feature_id in features:
            if feature_id in self._features:
                feature = self._features[feature_id]
                for conflict in feature.conflicts_with:
                    if conflict in features:
                        conflicts.append(f"{feature.name} 与 {self._features[conflict].name} 冲突")

        # 检查依赖
        for feature_id in features:
            if feature_id in self._features:
                feature = self._features[feature_id]
                for requirement in feature.requires:
                    if requirement not in features:
                        conflicts.append(f"{feature.name} 需要 {self._features[requirement].name}")

        return len(conflicts) == 0, conflicts

    def get_recommended_features_for_level(self, level: int) -> List[str]:
        """获取关卡推荐特性组合"""
        recommendations = {
            1: [],
            2: ["bullet_penetration", "sunflower_limit"],
            3: ["high_armor_rate", "zombie_health_reduce"],
            4: ["no_sun_drop", "random_penetration", "sunflower_limit_1"],
            5: ["melon_pult_available", "high_armor_rate"],
            6: ["melon_pult_available", "zombie_immunity"],
            7: ["melon_pult_available", "all_fast_zombies", "plant_speed_boost"],
            8: ["melon_pult_available", "card_cooldown"],
            9: ["melon_pult_available", "card_cooldown"],
            10: ["melon_pult_available", "cattail_available", "card_cooldown"],
            11: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available"],
            12: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available"],
            13: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn"],
            14: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "cucumber_available"],
            15: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "cucumber_available", "dandelion_available"],
            16: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "cucumber_available", "dandelion_available",
                 "lightning_flower_available"],
            17: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "cucumber_available", "dandelion_available",
                 "lightning_flower_available", "ice_cactus_available"],
            18: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "cucumber_available", "dandelion_available",
                 "lightning_flower_available", "ice_cactus_available", "portal_system"],
            19: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "exploding_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available"],
            20: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "exploding_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "high_spawn_rate_wave"],
            21: ["melon_pult_available", "cattail_available",  "wall_nut_available",
                 "cherry_bomb_available", "giant_zombie_spawn", "exploding_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "conveyor_belt", "no_sunflower"],
            22: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "exploding_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "random_sun_drop", "no_natural_sun",
                 "sunflower_no_produce", "sun_shroom_available", "night"],
            23: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "moon_flower_available", "giant_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "random_sun_drop", "no_natural_sun",
                 "sunflower_no_produce", "sun_shroom_available", "night"],
            24: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "moon_flower_available", "ice_car_zombie_spawn",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "luker_available", "random_sun_drop", "no_natural_sun",
                 "sunflower_no_produce", "sun_shroom_available", "night"],
            25: ["melon_pult_available", "cattail_available", "card_cooldown", "wall_nut_available",
                 "cherry_bomb_available", "moon_flower_available",
                 "cucumber_available", "dandelion_available", "lightning_flower_available",
                 "ice_cactus_available", "luker_available", "psychedelic_pitcher_available",
                  "sun_shroom_available", "night","random_sun_drop", "no_natural_sun","sunflower_no_produce"],
            26: [  "wall_nut_available","no_sunflower"
                 "cherry_bomb_available", "moon_flower_available",
                   "lightning_flower_available",
                 "ice_cactus_available", "luker_available", "psychedelic_pitcher_available",
                  "night", "random_sun_drop", "no_natural_sun", "sunflower_no_produce","conveyor_belt","ice_car_zombie_spawn","giant_zombie_spawn"],
            27: [ "wall_nut_available","melon_pult_available",
                 "cherry_bomb_available", "moon_flower_available","dandelion_available",
                 "lightning_flower_available","cattail_available","cucumber_available",
                 "ice_cactus_available", "luker_available", "psychedelic_pitcher_available",
                  "random_sun_drop", "seed_rain", "no_sunflower"
                 "ice_car_zombie_spawn", "giant_zombie_spawn"],
            28: [ "melon_pult_available",
                 "cherry_bomb_available", "moon_flower_available", "dandelion_available",
                 "lightning_flower_available", "cattail_available", "cucumber_available",
                 "ice_cactus_available", "luker_available", "night","conveyor_belt",
                 "random_sun_drop", "exploding_zombie_spawn","high_spawn_rate_wave",
                 "ice_car_zombie_spawn", "giant_zombie_spawn", "no_sunflower"],
        }

        # 对于超过最大定义关卡的，使用最高关卡的配置
        max_defined_level = max(recommendations.keys())
        if level > max_defined_level:
            return recommendations[max_defined_level]
        return recommendations.get(level, [])

    def add_custom_feature(self, feature: FeatureInfo) -> bool:
        """添加自定义特性"""
        if feature.feature_id in self._features:
            return False

        self._features[feature.feature_id] = feature
        return True

    def get_feature_description_text(self, feature_id: str) -> str:
        """获取特性的详细描述文本特性:"""
        feature = self.get_feature(feature_id)
        if not feature:
            return f"未知特性: {feature_id}"

        description = f"{feature.name}: {feature.description}"

        if feature.default_value is not None:
            if isinstance(feature.default_value, dict):
                # 对于复杂的配置（如传送门系统），显示主要参数
                if feature_id == "portal_system":
                    config = feature.default_value
                    description += f" (传送门数量: {config['portal_count']}, 切换间隔: {config['switch_interval']}秒)"
            elif isinstance(feature.default_value, float):
                if feature_id.endswith("_rate") or feature_id.endswith("_prob"):
                    description += f" ({feature.default_value:.0%})"
                elif feature_id.endswith("_multiplier"):
                    description += f" ({feature.default_value:.1f}x)"
                else:
                    description += f" ({feature.default_value})"
            else:
                description += f" ({feature.default_value})"

        return description


# 全局特性管理器实例
features_manager = FeaturesManager()


def get_level_features(level: int) -> List[str]:
    """获取指定关卡的推荐特性（兼容函数）"""
    return features_manager.get_recommended_features_for_level(level)


def validate_level_features(level: int, features: List[str]) -> bool:
    """验证关卡特性是否有效（兼容函数）"""
    # 检查特性是否适用于该关卡
    available_features = features_manager.get_available_features_for_level(level)
    for feature_id in features:
        if feature_id not in available_features:
            return False

    # 检查特性组合是否有效
    is_valid, _ = features_manager.validate_feature_combination(features)
    return is_valid


def get_feature_description(feature_id: str) -> str:
    """获取特性描述（兼容函数）"""
    return features_manager.get_feature_description_text(feature_id)