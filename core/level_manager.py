import json
import os
import random
from datetime import datetime
from animation import Trophy
from .features_manager import features_manager


class LevelConfigManager:
    """关卡配置管理器，负责加载和管理配置文件"""

    def __init__(self, config_path="database/levels.json"):
        self.config_path = config_path
        self.config_data = None
        self.last_modified = None
        self.load_config()

    def load_config(self):
        """从JSON文件加载配置"""
        try:
            if os.path.exists(self.config_path):
                self.last_modified = os.path.getmtime(self.config_path)
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)

            else:
                print(f"配置文件不存在: {self.config_path}，使用默认配置")
                self.create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置"""
        self.config_data = {
            "metadata": {
                "version": "2.0",
                "last_modified": datetime.now().isoformat(),
                "description": "植物大战僵尸简易版关卡配置"
            },
            "default_config": {
                "max_waves": 5,
                "initial_sun": 100,
                "zombie_armor_prob": 0.3,
                "fast_zombie_multiplier": 2.5
            },
            "levels": {
                "1": {
                    "name": "1.小试牛刀",
                    "max_waves": 3,
                    "initial_sun": 200,
                    "zombie_armor_prob": 0.1
                }
            }
        }

    def check_for_updates(self):
        """检查配置文件是否被修改"""
        if not os.path.exists(self.config_path):
            return False

        current_modified = os.path.getmtime(self.config_path)
        if self.last_modified != current_modified:
            return True
        return False

    def reload_if_changed(self):
        """如果文件被修改则重新加载"""
        if self.check_for_updates():
            print("检测到配置文件更新，重新加载...")
            self.load_config()
            return True
        return False

    def get_level_config(self, level_num):
        """获取指定关卡的配置"""
        if not self.config_data:
            return None

        level_key = str(level_num)
        levels = self.config_data.get("levels", {})
        default_config = self.config_data.get("default_config", {})

        if level_key in levels:
            config = default_config.copy()
            config.update(levels[level_key])
            return config
        else:
            config = default_config.copy()
            config["name"] = f"第{level_num}关：未知挑战"
            return config

    def get_all_levels(self):
        """获取所有关卡列表"""
        if not self.config_data:
            return {}
        return self.config_data.get("levels", {})

    def get_max_level(self):
        """获取最大关卡数"""
        levels = self.get_all_levels()
        if levels:
            return max(int(k) for k in levels.keys())
        return 1


class LevelManager:
    def __init__(self, config_path="database/levels.json", game_db=None):
        self.current_level = 1
        self.max_waves = 5
        self.current_wave = 0
        self.waves_completed = 0
        self.zombies_in_wave = 0
        self.zombies_defeated = 0
        self.wave_spawned = False
        self.all_waves_completed = False
        self.trophy = None
        self.wave_mode = False

        # 关卡特性和配置
        self.level_config = {}
        self.level_features = []  # 当前关卡可用的特性列表
        self.sunflower_count = 0

        # 配置管理器
        self.config_manager = LevelConfigManager(config_path)

        # 热重载设置
        self.hot_reload_enabled = True
        self.last_reload_check = 0
        self.reload_check_interval = 60

        # 新增：游戏数据库引用，用于获取全局设置
        self.game_db = game_db

    def enable_hot_reload(self, enabled=True):
        """启用或禁用热重载"""
        self.hot_reload_enabled = enabled
        if enabled:
            print("关卡配置热重载已启用")
        else:
            pass

    def check_hot_reload(self):
        """检查并执行热重载"""
        if not self.hot_reload_enabled:
            return False

        self.last_reload_check += 1
        if self.last_reload_check >= self.reload_check_interval:
            self.last_reload_check = 0
            if self.config_manager.reload_if_changed():
                self.load_level_config(self.current_level)
                return True
        return False

    def start_level(self, level):
        """开始指定关卡"""
        self.current_level = level
        self.current_wave = 0
        self.waves_completed = 0
        self.zombies_in_wave = 0
        self.zombies_defeated = 0
        self.wave_spawned = False
        self.all_waves_completed = False
        self.trophy = None
        self.wave_mode = False
        self.sunflower_count = 0

        self.load_level_config(level)

    def load_level_config(self, level):
        """从配置加载关卡设置"""
        config = self.config_manager.get_level_config(level)
        if config:
            self.level_config = config.copy()
            self.max_waves = self.level_config.get('max_waves', 5)
        else:
            # 使用默认配置
            self.level_config = {
                'name': f'第{level}关：未知挑战',
                'max_waves': 5,
                'initial_sun': 100,
                'zombie_armor_prob': 0.3,
                'fast_zombie_multiplier': 2.5
            }
            self.max_waves = 5

        # 关卡特性完全由特性管理器决定，忽略配置文件中的 features 字段
        self.level_features = features_manager.get_recommended_features_for_level(level)

        # 输出当前关卡使用的特性（可选的调试信息）
        if self.level_features:
            pass

    def start_wave_mode(self):
        """进入波次模式"""
        self.wave_mode = True
        self.current_wave = 0
        self.waves_completed = 0
        self.wave_spawned = False
        self.all_waves_completed = False

    def start_wave(self, zombie_count):
        """开始新的波次"""
        self.current_wave += 1
        self.zombies_in_wave = zombie_count
        self.zombies_defeated = 0
        self.wave_spawned = True
        print(f"波次 {self.current_wave} 开始：共 {zombie_count} 个僵尸")

    def zombie_defeated(self):
        """僵尸被击败时调用"""
        self.zombies_defeated += 1
        if self.zombies_defeated >= self.zombies_in_wave:
            self.wave_completed()

    def wave_completed(self):
        """当前波次完成"""
        self.waves_completed += 1
        self.wave_spawned = False
        if self.waves_completed >= self.max_waves:
            self.all_waves_completed = True

    def should_spawn_wave(self):
        """检查是否应该生成新波次"""
        return (self.wave_mode and
                not self.wave_spawned and
                self.current_wave < self.max_waves)

    def is_level_complete(self):
        """检查关卡是否完成"""
        return (self.all_waves_completed and
                self.current_wave >= self.max_waves and
                self.waves_completed >= self.max_waves)

    def create_trophy(self, x, y, image=None):
        """创建奖杯"""
        self.trophy = Trophy(x, y, image)

    # 全局设置检查方法
    def _get_global_setting(self, setting_key, default=False):
        """获取全局设置值"""
        if self.game_db:
            return self.game_db.is_global_setting_enabled(setting_key)
        return default

    def _is_hardcore_mode(self):
        """检查是否启用硬核模式"""
        return self._get_global_setting("hardcore_mode")

    def _is_speedrun_mode(self):
        """检查是否启用竞速模式"""
        return self._get_global_setting("speedrun_mode")

    # 配置访问方法 - 现在整合全局设置
    def get_level_name(self):
        """获取当前关卡名称"""
        name = self.level_config.get('name', f'第{self.current_level}关')

        # 根据全局模式添加前缀
        if self._is_hardcore_mode():
            name = f"[硬核] {name}"
        elif self._is_speedrun_mode():
            name = f"[竞速] {name}"

        return name

    def get_level_description(self):
        """获取当前关卡描述"""
        return self.level_config.get('description', '')

    def has_special_feature(self, feature_id: str) -> bool:
        """检查是否有特定特性（使用特性管理器）"""
        return feature_id in self.level_features

    def get_feature_value(self, feature_id: str, default_value=None):
        """获取特性的值（如果特性有参数）"""
        if not self.has_special_feature(feature_id):
            return default_value

        feature_info = features_manager.get_feature(feature_id)
        if feature_info and feature_info.default_value is not None:
            return feature_info.default_value

        return default_value

    def get_sunflower_limit(self):
        """获取向日葵种植限制 - 更新：支持第四关特殊限制"""
        # 全局植物限制：只允许基础植物
        if self._get_global_setting("global_plant_limit"):
            return 10  # 基础植物模式下允许更多向日葵

        # 检查是否完全禁止向日葵
        if self.has_special_feature("no_sunflower"):
            return 0

        # 检查是否限制为1棵（第四关专用特性）
        if self.has_special_feature("sunflower_limit_1"):
            return 1

        # 检查是否有普通向日葵限制
        if self.has_special_feature("sunflower_limit"):
            return self.get_feature_value("sunflower_limit", 3)

        # 没有任何限制
        return None

    def can_plant_sunflower(self):
        """检查是否可以种植向日葵 - 更新：支持不同限制数量"""
        limit = self.get_sunflower_limit()
        if limit is None:
            return True  # 无限制
        if limit == 0:
            return False  # 完全禁止
        return self.sunflower_count < limit  # 检查是否超过限制

    def plant_sunflower(self):
        """种植向日葵时调用"""
        if self.can_plant_sunflower():
            self.sunflower_count += 1
            return True
        return False

    def remove_sunflower(self):
        """移除向日葵时调用"""
        if self.sunflower_count > 0:
            self.sunflower_count -= 1

    def get_sunflower_status_text(self):
        """获取向日葵状态文本 - 更新：支持不同限制显示"""
        limit = self.get_sunflower_limit()
        if limit is None:
            return ""  # 无限制时不显示
        elif limit == 0:
            return ""
        else:
            return f"向日葵: {self.sunflower_count}/{limit}"



    # 子弹相关方法（整合全局设置）
    def has_bullet_penetration(self):
        """当前关卡是否有子弹穿透特性"""
        # 全局子弹穿透设置
        if self._get_global_setting("global_bullet_penetration"):
            return True
        return self.has_special_feature("bullet_penetration")

    def get_random_penetration_prob(self):
        """获取随机穿透概率"""
        # 全局设置优先
        if self._get_global_setting("global_bullet_penetration"):
            return 1.0  # 全局穿透时100%概率
        return self.get_feature_value("random_penetration", 0.0)

    # 僵尸相关方法（整合全局设置）
    def get_zombie_armor_prob(self):
        """获取僵尸铁甲概率"""
        # 全局高铁门率设置
        if self._get_global_setting("global_high_armor_rate"):
            return 0.7
        if self.has_special_feature("high_armor_rate"):
            return self.get_feature_value("high_armor_rate", 0.7)
        return self.level_config.get('zombie_armor_prob', 0.3)

    def get_fast_zombie_multiplier(self):
        """获取快速僵尸速度倍率"""
        return self.level_config.get('fast_zombie_multiplier', 2.5)

    def has_all_fast_zombies(self):
        """检查是否所有僵尸都是快速僵尸"""
        # 全局快速僵尸设置
        if self._get_global_setting("global_fast_zombies"):
            return True
        return self.has_special_feature('all_fast_zombies')

    # 植物相关方法（整合全局设置）
    def get_plant_speed_multiplier(self):
        """获取植物速度倍率"""
        # 全局植物加速设置
        if self._get_global_setting("global_plant_speed_boost"):
            return 1.5
        if self.has_special_feature("plant_speed_boost"):
            return self.get_feature_value("plant_speed_boost", 1.5)
        return 1.0

    def has_plant_speed_boost(self):
        """检查是否有植物速度提升特性"""
        return (self._get_global_setting("global_plant_speed_boost") or
                self.has_special_feature('plant_speed_boost'))

    def has_card_cooldown(self):
        """检查是否有卡牌冷却特性"""
        # 全局无冷却设置
        if self._get_global_setting("global_no_cooldown"):
            return False
        # 全局卡牌冷却设置
        if self._get_global_setting("all_card_cooldown"):
            return True
        return self.has_special_feature('card_cooldown')

    def get_card_cooldown_time(self):
        """获取卡牌冷却时间（帧数）"""
        if self._get_global_setting("global_no_cooldown"):
            return 0
        return self.get_feature_value("card_cooldown", 180)

    # 经济相关方法（整合全局设置）
    def get_initial_sun(self):
        """获取关卡初始阳光数量"""
        base_sun = self.level_config.get('initial_sun', 100)

        # 全局初始阳光翻倍
        if self._get_global_setting("global_increased_sun"):
            base_sun *= 2
        # 关卡特性：初始阳光增加
        elif self.has_special_feature("increased_initial_sun"):
            base_sun = self.get_feature_value("increased_initial_sun", 200)

        return base_sun

    def no_sun_drop_in_wave_mode(self):
        """波次模式下是否不掉落阳光"""
        # 全局无阳光掉落设置
        if self._get_global_setting("global_no_sun_drop"):
            return True
        return self.has_special_feature("no_sun_drop")

    # 新增：植物可用性检查（支持全局植物限制）
    def is_plant_available(self, plant_type):
        """检查植物是否可用（考虑全局限制）"""
        # 全局植物限制：只允许基础植物
        if self._get_global_setting("global_plant_limit"):
            basic_plants = ["sunflower", "shooter"]
            return plant_type in basic_plants

        # 正常的植物解锁检查
        return True

    # 配置管理方法
    def get_all_level_configs(self):
        """获取所有关卡配置"""
        return self.config_manager.get_all_levels()

    def get_max_available_level(self):
        """获取最大可用关卡数"""
        return self.config_manager.get_max_level()

    def reload_config(self):
        """手动重新加载配置print"""
        self.config_manager.load_config()
        self.load_level_config(self.current_level)
        print(f"已重新加载关卡配置，当前关卡：{self.get_level_name()}")

    def get_config_info(self):
        """获取配置文件信息"""
        if self.config_manager.config_data:
            metadata = self.config_manager.config_data.get("metadata", {})

            # 获取当前激活的全局设置
            active_global_settings = []
            if self.game_db:
                settings = self.game_db.get_level_settings()
                for key, value in settings.items():
                    if value and key.startswith(('global_', 'hardcore_', 'speedrun_', 'all_')):
                        active_global_settings.append(key)

            return {
                "config_path": self.config_manager.config_path,
                "version": metadata.get("version", "未知"),
                "last_modified": metadata.get("last_modified", "未知"),
                "total_levels": len(self.config_manager.get_all_levels()),
                "hot_reload": self.hot_reload_enabled,
                "current_features": self.level_features,
                "active_global_settings": active_global_settings  # 新增
            }
        return None

    def get_level_features_description(self):
        """获取当前关卡特性的描述"""
        descriptions = []

        # 添加关卡特性描述
        for feature_id in self.level_features:
            desc = features_manager.get_feature_description_text(feature_id)
            descriptions.append(f"关卡特性: {desc}")

        # 添加激活的全局设置描述
        if self.game_db:
            settings = self.game_db.get_level_settings()
            for key, value in settings.items():
                if value and key.startswith(('global_', 'hardcore_', 'speedrun_', 'all_')):
                    setting_names = {
                        "global_high_armor_rate": "全局高铁门率",
                        "global_fast_zombies": "全局快速僵尸",
                        "global_no_sun_drop": "全局无阳光掉落",
                        "global_plant_limit": "全局植物限制",
                        "global_bullet_penetration": "全局子弹穿透",
                        "global_plant_speed_boost": "全局植物加速",
                        "global_increased_sun": "全局初始阳光翻倍",
                        "global_no_cooldown": "全局无冷却",
                        "all_card_cooldown": "全局卡牌冷却",
                        "hardcore_mode": "硬核模式",
                        "speedrun_mode": "竞速模式"
                    }
                    name = setting_names.get(key, key)
                    descriptions.append(f"全局设置: {name}")

        return descriptions

    # 僵尸特性检查方法
    def has_giant_zombies(self):
        """检查当前关卡是否有巨人僵尸特性"""
        # 全局巨人僵尸设置
        if self._get_global_setting("global_giant_zombies"):
            return True
        return self.has_special_feature("giant_zombie_spawn")

    def has_exploding_zombies(self):
        """检查当前关卡是否有爆炸僵尸特性"""
        # 全局爆炸僵尸设置（如果有的话）
        if self._get_global_setting("global_exploding_zombies"):
            return True
        return self.has_special_feature("exploding_zombie_spawn")

    def get_zombie_spawn_probabilities(self):
        """获取各种僵尸的生成概率"""
        probabilities = {
            "normal": 1.0,  # 默认100%普通僵尸
            "giant": 0.0,
            "exploding": 0.0
        }

        # 检查是否是第20关的波次模式特殊生成率
        if (self.current_level == 20 and self.wave_mode and
                self.has_special_feature("high_spawn_rate_wave")):
            # 获取特殊生成率配置
            spawn_config = self.get_feature_value("high_spawn_rate_wave", {})
            if spawn_config:
                # 第20关波次模式下的特殊生成率
                probabilities["giant"] = spawn_config.get("giant_spawn_rate", 0.35)
                probabilities["exploding"] = spawn_config.get("exploding_spawn_rate", 0.35)
                # 剩余50%为普通僵尸
                probabilities["normal"] = 1.0 - probabilities["giant"] - probabilities["exploding"]



            return probabilities

        # 正常的生成概率逻辑
        if self.has_exploding_zombies():
            probabilities["exploding"] = 0.15  # 15%爆炸僵尸
            probabilities["normal"] -= 0.15

        if self.has_giant_zombies():
            probabilities["giant"] = 0.10  # 10%巨人僵尸
            probabilities["normal"] -= 0.10

        return probabilities

    def get_random_zombie_type(self):
        """根据当前关卡特性随机返回一个僵尸类型"""
        probabilities = self.get_zombie_spawn_probabilities()

        rand = random.random()
        cumulative = 0

        for zombie_type, prob in probabilities.items():
            cumulative += prob
            if rand < cumulative:
                return zombie_type

        return "normal"  # 默认返回普通僵尸

    def get_zombie_features_description(self):
        """获取当前关卡的僵尸特性描述"""
        descriptions = []

        if self.has_giant_zombies():
            descriptions.append("巨人僵尸（10%概率）")

        if self.has_exploding_zombies():
            descriptions.append("爆炸僵尸（15%概率）")

        if self.has_all_fast_zombies():
            descriptions.append("全员快速")

        if self.has_special_feature("zombie_immunity"):
            immunity_chance = self.get_feature_value("zombie_immunity", 0.05)
            descriptions.append(f"僵尸免疫（{immunity_chance:.0%}概率）")

        if self.has_special_feature("zombie_health_reduce"):
            descriptions.append("僵尸血量减少20%")

        armor_prob = self.get_zombie_armor_prob()
        if armor_prob != 0.3:  # 如果不是默认值
            descriptions.append(f"铁门概率: {armor_prob:.0%}")

        return descriptions if descriptions else ["标准僵尸配置"]