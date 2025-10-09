"""
保存管理器 - 处理游戏进度的保存和恢复逻辑
"""
import pygame
import random
import sys
import os

# 获取当前文件所在的database目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（database的上级目录）
project_root = os.path.dirname(current_dir)
# 添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.constants import get_constants
from plants import Plant
from zombies import Zombie
# 统一使用 import bullets 方式
import bullets


def auto_save_game_progress(game_db, game_state, music_manager, game_manager=None, save_interval=100):
    """自动保存游戏进度"""
    current_time = pygame.time.get_ticks()
    last_save_time = game_state.get("last_save_time", 0)

    # 每save_interval帧（默认5秒）保存一次
    if current_time - last_save_time >= save_interval * 1000 / 60:  # 转换为毫秒
        if game_state.get("wave_mode") or len(game_state.get("plants", [])) > 0:
            # 只在有意义的游戏进度时保存
            # 修改：传入 game_manager 参数
            if game_db.save_game_progress(game_state, music_manager, game_manager):
                pass
            game_state["last_save_time"] = current_time


def restore_game_from_save(saved_data, level_manager, game_manager=None):
    """从保存的数据恢复游戏状态，增加地刺和魅惑系统支持"""
    try:
        # 创建基础游戏状态
        game = {
            "plants": [], "zombies": [], "bullets": [],
            "zombie_timer": saved_data.get("zombie_timer", 0),
            "sun": saved_data["sun"],
            "game_over": False,
            "selected": None,
            "wave_mode": saved_data["wave_mode"],
            "wave_timer": saved_data["wave_timer"],
            "zombies_spawned": saved_data["zombies_spawned"],
            "zombies_killed": saved_data["zombies_killed"],
            "first_wave_spawned": saved_data["first_wave_spawned"],
            "game_over_sound_played": False,
            "level_manager": level_manager,
            "fade_state": "none",
            "fade_alpha": 0,
            "fade_timer": 0,
            "fade_duration": 190,
            "card_cooldowns": saved_data.get("card_cooldowns", {}),
            "last_update_time": pygame.time.get_ticks(),
            "last_save_time": 0,
            "hammer_cooldown": saved_data.get("hammer_cooldown", 0),
            # 黄瓜效果状态
            "zombie_stun_timers": saved_data.get("cucumber_effects", {}).get("zombie_stun_timers", {}),
            "cucumber_spray_timers": saved_data.get("cucumber_effects", {}).get("cucumber_spray_timers", {}),
            "cucumber_plant_healing": saved_data.get("cucumber_effects", {}).get("cucumber_plant_healing", {}),
            # 新增：爆炸效果列表
            "explosion_effects": [],
            # 新增：魅惑效果字典
            "charm_effects": {}
        }

        # 恢复植物 - 新增地刺和迷幻投手支持
        for plant_data in saved_data.get("plants", []):
            plant = Plant(
                plant_data["row"],
                plant_data["col"],
                plant_data["plant_type"],
                get_constants(),
                None,
                level_manager
            )
            plant.health = plant_data["health"]
            if "max_health" in plant_data:
                plant.max_health = plant_data["max_health"]

            # 恢复攻击型植物的射击参数 - 添加地刺和迷幻投手支持
            if plant.plant_type in ["shooter", "melon_pult", "cattail", "dandelion", "lightning_flower", "ice_cactus",
                                    "moon_flower", "luker", "psychedelic_pitcher"]:
                plant.shoot_timer = plant_data.get("shoot_timer", 0)
                plant.current_shoot_delay = plant_data.get("current_shoot_delay", plant.base_shoot_delay)
                plant.had_target_last_frame = plant_data.get("had_target_last_frame", False)

            # 恢复闪电花特殊状态
            if plant.plant_type == "lightning_flower":
                plant.lightning_timer = plant_data.get("lightning_timer", 0)
                plant.show_lightning = plant_data.get("show_lightning", False)
                plant.lightning_effects = plant_data.get("lightning_effects", [])

            # 恢复向日葵状态
            if plant.plant_type == "sunflower":
                plant.sun_timer = plant_data.get("sun_timer", 0)

            # 恢复月亮花特殊状态
            if plant.plant_type == "moon_flower":
                plant.glow_effect_timer = plant_data.get("moon_flower_glow_timer", 0)
                plant.glow_alpha = plant_data.get("moon_flower_glow_alpha", 100)
                plant.glow_increasing = plant_data.get("moon_flower_glow_increasing", True)
                plant.moon_flower_count = plant_data.get("moon_flower_count", 0)

            # 新增：恢复地刺特殊状态
            if plant.plant_type == "luker":
                plant.damage = plant_data.get("luker_damage", 20)
                plant.can_ignore_armor = plant_data.get("luker_can_ignore_armor", True)
                plant.can_instant_kill_vehicles = plant_data.get("luker_can_instant_kill_vehicles", True)

                # 恢复地刺的正确射击延迟
                if "luker_base_shoot_delay" in plant_data:
                    plant.base_shoot_delay = plant_data["luker_base_shoot_delay"]
                    # 如果当前延迟是默认值，更新为地刺的正确值
                    if plant.current_shoot_delay == 300:
                        plant.current_shoot_delay = plant.base_shoot_delay

            # 新增：恢复迷幻投手特殊状态
            if plant.plant_type == "psychedelic_pitcher":
                plant.shoot_interval = plant_data.get("shoot_interval", 240)
                plant.animation_timer = plant_data.get("animation_timer", 0)
                plant.is_throwing = plant_data.get("is_throwing", False)
                plant.throw_animation_duration = plant_data.get("throw_animation_duration", 50)

            # 关键修复：恢复爆炸植物的特殊状态
            if "explosion_state" in plant_data:
                explosion_state = plant_data["explosion_state"]

                # 恢复爆炸状态属性
                for attr_name, attr_value in explosion_state.items():
                    setattr(plant, attr_name, attr_value)

                # 特殊处理：如果植物已经爆炸，不应该添加到植物列表中
                if explosion_state.get("has_exploded", False):
                    print(f"跳过已爆炸的植物: {plant.plant_type} at ({plant.row}, {plant.col})")
                    continue

                # 如果植物正在爆炸过程中，也不添加（让爆炸效果自然结束）
                if explosion_state.get("is_exploding", False):
                    print(f"跳过正在爆炸的植物: {plant.plant_type} at ({plant.row}, {plant.col})")
                    continue

            game["plants"].append(plant)

        # 恢复爆炸效果（如果有）
        if "explosion_effects" in saved_data:
            for effect_data in saved_data["explosion_effects"]:
                # 这里可以重新创建爆炸效果，或者简单跳过
                # 因为大多数情况下，玩家不会在意爆炸动画的恢复
                print(f"跳过爆炸效果恢复: {effect_data.get('effect_type', 'unknown')}")

        # 恢复僵尸 - 保持原有逻辑，添加魅惑状态
        current_time = pygame.time.get_ticks()
        for zombie_data in saved_data.get("zombies", []):
            zombie_type = zombie_data.get("zombie_type", "normal")

            # 根据僵尸类型导入正确的类
            if zombie_type == "ice_car":
                from zombies.ice_car_zombie import IceCarZombie
                zombie = IceCarZombie(
                    zombie_data["row"],
                    has_armor_prob=0.0,  # 冰车僵尸没有护甲
                    is_fast=zombie_data["is_fast"],
                    wave_mode=True,
                    fast_multiplier=level_manager.get_fast_zombie_multiplier(),
                    constants=get_constants(),
                    sounds=None,
                    images=None,
                    level_settings=None
                )

                # 恢复冰车僵尸特有状态
                zombie.ice_trail_timer = zombie_data.get("ice_trail_timer", 0)
                zombie.ice_trail_interval = zombie_data.get("ice_trail_interval", 15)
                zombie.last_trail_col = zombie_data.get("last_trail_col", None)

                # 恢复已碾压植物集合（从list转回set）
                crushed_plants_list = zombie_data.get("crushed_plants", [])
                zombie.crushed_plants = set(crushed_plants_list)

                # 设置游戏状态引用
                zombie.set_game_state(game)

            # 根据僵尸类型导入正确的类
            elif zombie_type == "exploding":
                from zombies.exploding_zombie import ExplodingZombie
                zombie = ExplodingZombie(
                    zombie_data["row"],
                    has_armor_prob=1.0 if zombie_data["has_armor"] else 0.0,
                    is_fast=zombie_data["is_fast"],
                    wave_mode=True,
                    fast_multiplier=level_manager.get_fast_zombie_multiplier(),
                    constants=get_constants(),
                    sounds=None,
                    images=None,
                    level_settings=None
                )

                # 恢复爆炸僵尸特有状态
                zombie.explosion_damage = zombie_data.get("explosion_damage", 1500)
                zombie.explosion_range = zombie_data.get("explosion_range", 3)
                zombie.has_exploded = zombie_data.get("has_exploded", False)
                zombie.explosion_triggered = zombie_data.get("explosion_triggered", False)
                zombie.explosion_timer = zombie_data.get("explosion_timer", 0)
                zombie.explosion_delay = zombie_data.get("explosion_delay", 30)
                zombie.death_by_explosion = zombie_data.get("death_by_explosion", False)

            elif zombie_type == "giant":
                from zombies.giant_zombie import GiantZombie
                zombie = GiantZombie(
                    zombie_data["row"],
                    has_armor_prob=1.0 if zombie_data["has_armor"] else 0.0,
                    is_fast=zombie_data["is_fast"],
                    wave_mode=True,
                    fast_multiplier=level_manager.get_fast_zombie_multiplier(),
                    constants=get_constants(),
                    sounds=None,
                    images=None,
                    level_settings=None
                )

                # 恢复巨人僵尸特有状态
                zombie.smash_timer = zombie_data.get("smash_timer", 0)
                zombie.has_attacked_once = zombie_data.get("has_attacked_once", False)

            else:
                # 普通僵尸
                zombie = Zombie(
                    zombie_data["row"],
                    has_armor_prob=1.0 if zombie_data["has_armor"] else 0.0,
                    is_fast=zombie_data["is_fast"],
                    wave_mode=True,
                    fast_multiplier=level_manager.get_fast_zombie_multiplier(),
                    constants=get_constants(),
                    sounds=None,
                    images=None,
                    zombie_type=zombie_type
                )

            # 恢复所有僵尸的通用状态
            zombie.col = zombie_data["col"]
            zombie.has_armor = zombie_data["has_armor"]
            zombie.is_attacking = zombie_data["is_attacking"]
            zombie.health = zombie_data["health"]
            zombie.armor_health = zombie_data["armor_health"]

            # 恢复死亡动画状态
            zombie.is_dying = zombie_data.get("is_dying", False)
            zombie.death_animation_timer = zombie_data.get("death_animation_timer", 0)
            zombie.current_alpha = zombie_data.get("current_alpha", 255)

            # 恢复冰冻状态
            if zombie_data.get("is_frozen", False):
                zombie.is_frozen = True
                zombie.freeze_start_time = zombie_data.get("freeze_start_time", current_time)
                zombie.original_speed = zombie_data.get("original_speed", zombie.base_speed)
                freeze_elapsed = current_time - zombie.freeze_start_time
                if freeze_elapsed < 5000:
                    zombie.speed = zombie.original_speed * 0.5
                else:
                    zombie.is_frozen = False
                    zombie.speed = zombie.original_speed

            # 恢复眩晕和喷射状态
            zombie.is_stunned = zombie_data.get("is_stunned", False)
            zombie.is_spraying = zombie_data.get("is_spraying", False)
            zombie.stun_visual_timer = zombie_data.get("stun_visual_timer", 0)

            # 新增：恢复魅惑状态
            zombie.is_charmed = zombie_data.get("is_charmed", False)
            zombie.team = zombie_data.get("team", "zombie")
            zombie.pending_charm = zombie_data.get("pending_charm", 0)

            game["zombies"].append(zombie)

        # 新增：恢复魅惑效果
        if "charm_effects" in saved_data and saved_data["charm_effects"]:
            charm_data = saved_data["charm_effects"]
            if "charm_effects_list" in charm_data:
                for charm_info in charm_data["charm_effects_list"]:
                    zombie_index = charm_info.get("zombie_index", -1)
                    if 0 <= zombie_index < len(game["zombies"]):
                        zombie = game["zombies"][zombie_index]
                        zombie_id = id(zombie)

                        # 恢复魅惑效果数据
                        game["charm_effects"][zombie_id] = {
                            'zombie': zombie,
                            'duration': charm_info.get('duration', 300),
                            'remaining': charm_info.get('remaining', 0),
                            'original_speed': charm_info.get('original_speed', -0.01)
                        }

                        # 确保僵尸处于魅惑状态
                        zombie.is_charmed = True
                        zombie.team = "plant"

        # 恢复子弹状态 - 新增月亮子弹和迷幻子弹支持
        for bullet_data in saved_data.get("bullets", []):
            bullet = bullets.create_bullet(
                bullet_type=bullet_data["bullet_type"],
                row=bullet_data["row"],
                col=bullet_data["col"],
                can_penetrate=bullet_data["can_penetrate"],
                target_col=bullet_data.get("target_col", None),
                constants=get_constants(),
                images=None
            )

            # 恢复子弹状态
            bullet.speed = bullet_data.get("speed", bullet.speed)

            if bullet.bullet_type == "ice":
                bullet.freeze_duration = bullet_data.get("freeze_power", 5000)
                bullet.freeze_applied_zombies = set()

            elif bullet.bullet_type == "melon":
                bullet.start_col = bullet_data.get("start_col", bullet.col)
                bullet.flight_progress = bullet_data.get("flight_progress", 0.0)
                bullet.has_landed = bullet_data.get("has_landed", False)
                bullet.splash_applied = bullet_data.get("splash_applied", False)
                bullet.has_hit_target = bullet_data.get("has_hit_target", False)
                bullet.explosion_triggered = bullet_data.get("explosion_triggered", False)
                bullet.show_explosion = bullet_data.get("show_explosion", False)

            elif bullet.bullet_type == "spike":
                bullet.actual_x = bullet_data.get("actual_x", bullet.col)
                bullet.actual_y = bullet_data.get("actual_y", bullet.row)
                bullet.direction_x = bullet_data.get("direction_x", 1.0)
                bullet.direction_y = bullet_data.get("direction_y", 0.0)
                bullet.target_direction_x = bullet_data.get("target_direction_x", 1.0)
                bullet.target_direction_y = bullet_data.get("target_direction_y", 0.0)
                bullet.retargeting_cooldown = bullet_data.get("retargeting_cooldown", 0)

            # 新增：恢复月亮子弹特殊状态
            elif bullet.bullet_type == "moon":
                bullet.rotation = bullet_data.get("moon_rotation", 0)
                bullet.glow_timer = bullet_data.get("moon_glow_timer", 0)
                bullet.initial_col = bullet_data.get("moon_initial_col", bullet.col)
                bullet.wave_amplitude = bullet_data.get("moon_wave_amplitude", 0.1)
                bullet.wave_frequency = bullet_data.get("moon_wave_frequency", 0.1)

            # 新增：恢复迷幻子弹特殊状态
            elif bullet.bullet_type == "psychedelic":
                bullet.dmg = bullet_data.get("psychedelic_dmg", 20)
                bullet.charm_duration = bullet_data.get("psychedelic_charm_duration", 300)
                bullet.max_height = bullet_data.get("psychedelic_max_height", 2)
                bullet.flight_speed = bullet_data.get("psychedelic_flight_speed", 0.03)

                # 恢复飞行状态
                bullet.start_col = bullet_data.get("start_col", bullet.col)
                bullet.flight_progress = bullet_data.get("flight_progress", 0.0)
                bullet.has_landed = bullet_data.get("has_landed", False)
                bullet.has_hit_target = bullet_data.get("has_hit_target", False)

            bullet.hit_zombies = set()
            bullet.splash_hit_zombies = set()

            game["bullets"].append(bullet)

        # 恢复其他状态 - 保持原有逻辑
        if game_manager and "plant_select_state" in saved_data:
            plant_select_state = saved_data["plant_select_state"]
            game_manager.plant_selection_manager.show_plant_select = plant_select_state.get("show_plant_select", False)
            game_manager.plant_selection_manager.selected_plants_for_game = plant_select_state.get(
                "selected_plants_for_game", [])
            game_manager.animation_manager.plant_select_animation_complete = plant_select_state.get(
                "plant_select_animation_complete", False)

        if game_manager and "cart_data" in saved_data:
            cart_data = saved_data["cart_data"]
            if cart_data:
                game_manager.cart_manager.load_save_data(cart_data)

        # 恢复蒲公英种子
        game["dandelion_seeds"] = []
        if "dandelion_seeds" in saved_data:
            for seed_data in saved_data["dandelion_seeds"]:
                seed = bullets.DandelionSeed(
                    start_x=seed_data["start_x"],
                    start_y=seed_data["start_y"],
                    target_zombie=None,
                    constants=get_constants(),
                    images=None
                )

                restore_attributes = [
                    "current_x", "current_y", "target_x", "target_y", "life_time",
                    "progress", "has_hit", "rotation", "wind_amplitude", "wind_frequency",
                    "drift_speed_x", "drift_speed_y", "rotation_speed", "is_fading",
                    "fade_out_timer", "fade_out_duration", "damage", "speed", "max_life_time"
                ]

                for attr in restore_attributes:
                    if attr in seed_data:
                        setattr(seed, attr, seed_data[attr])

                game["dandelion_seeds"].append(seed)

        # 恢复传送带状态）
        if game_manager and "conveyor_belt_data" in saved_data and saved_data["conveyor_belt_data"]:
            conveyor_data = saved_data["conveyor_belt_data"]

            # 检查是否应该有传送带
            if level_manager.has_special_feature("conveyor_belt") or level_manager.current_level == 21:
                # 如果传送带管理器不存在，先创建它
                if not hasattr(game_manager, 'conveyor_belt_manager') or not game_manager.conveyor_belt_manager:
                    from ui.conveyor_belt_manager import ConveyorBeltManager
                    from core.cards_manager import get_available_cards_new

                    # 获取可用植物卡牌
                    available_plants = get_available_cards_new(level_manager, None, None)
                    game_manager.conveyor_belt_manager = ConveyorBeltManager(level_manager, available_plants)

                # 恢复传送带状态
                game_manager.conveyor_belt_manager.load_save_data(conveyor_data)

        # 恢复种子雨状态（简化版）
        if game_manager and "seed_rain_data" in saved_data and saved_data["seed_rain_data"]:
            if level_manager.has_special_feature("seed_rain"):
                if not hasattr(game_manager, 'seed_rain_manager') or not game_manager.seed_rain_manager:
                    # 先创建种子雨管理器
                    from ui.seed_rain_manager import SeedRainManager
                    from core.cards_manager import get_available_cards_new
                    available_plants = get_available_cards_new(level_manager, None, None)
                    game_manager.seed_rain_manager = SeedRainManager(level_manager, available_plants, None)

                # 使用便捷方法恢复
                game_manager.seed_rain_manager.load_save_data(saved_data["seed_rain_data"])
        # 恢复传送门状态
        if "portal_manager_data" in saved_data and saved_data["portal_manager_data"]:
            portal_data = saved_data["portal_manager_data"]

            # 创建传送门管理器，但不让它初始化默认传送门
            from ui.portal_manager import PortalManager, Portal

            # 方案1：修改构造函数调用，传入一个标志阻止默认初始化
            # portal_manager = PortalManager(level_manager, initialize_portals=False)

            # 方案2：先正常创建，然后立即清空并禁用自动生成
            portal_manager = PortalManager(level_manager)

            # 立即清空所有传送门，防止任何默认初始化
            portal_manager.portals.clear()

            # 恢复传送门管理器的核心状态
            portal_manager.switch_timer = portal_data.get("switch_timer", 0)
            portal_manager.switch_interval = portal_data.get("switch_interval", 1200)
            portal_manager.next_portal_id = portal_data.get("next_portal_id", 0)

            # 标记为从保存数据恢复，防止重新随机生成
            portal_manager._is_restoring_from_save = True

            # 恢复每个保存的传送门
            for portal_info in portal_data.get("portals", []):
                portal = Portal(portal_info["row"], portal_info["col"], portal_info["portal_id"])

                # 恢复传送门的详细状态
                portal.spawn_animation_timer = portal_info.get("spawn_animation_timer", 60)
                portal.despawn_animation_timer = portal_info.get("despawn_animation_timer", 0)
                portal.is_spawning = portal_info.get("is_spawning", False)
                portal.is_despawning = portal_info.get("is_despawning", False)
                portal.is_active = portal_info.get("is_active", True)
                portal.rotation_angle = portal_info.get("rotation_angle", 0)

                portal_manager.portals.append(portal)

            # 完成恢复标记
            portal_manager._is_restoring_from_save = False

            game["portal_manager"] = portal_manager

            # 确保传送门数据正确恢复的验证
            print(f"传送门恢复完成: {len(portal_manager.portals)} 个传送门")
            for i, portal in enumerate(portal_manager.portals):
                print(f"  传送门 {i}: 位置({portal.row}, {portal.col}), ID: {portal.portal_id}")

        else:
            # 如果没有传送门数据，设置为None避免创建默认传送门
            game["portal_manager"] = None

        # 恢复关卡管理器状态...（保持原有逻辑）
        if "level_manager_state" in saved_data:
            level_manager_state = saved_data["level_manager_state"]

            saved_wave_mode = saved_data.get("wave_mode", False)
            level_manager.wave_mode = saved_wave_mode

            level_manager.current_wave = level_manager_state.get("current_wave", 1)
            level_manager.waves_completed = level_manager_state.get("waves_completed", 0)
            level_manager.zombies_in_wave = level_manager_state.get("zombies_in_wave", 0)
            level_manager.zombies_defeated = level_manager_state.get("zombies_defeated", 0)
            level_manager.wave_spawned = level_manager_state.get("wave_spawned", False)
            level_manager.all_waves_completed = level_manager_state.get("all_waves_completed", False)
            level_manager.max_waves = level_manager_state.get("max_waves", 3)
            level_manager.sunflower_count = level_manager_state.get("sunflower_count", 0)

            if level_manager.all_waves_completed:
                level_manager.wave_mode = True
        # 恢复冰道管理器状态
        if "ice_trail_manager_data" in saved_data and saved_data["ice_trail_manager_data"]:
            ice_trail_data = saved_data["ice_trail_manager_data"]

            # 创建冰道管理器
            from zombies.ice_trail_manager import IceTrailManager
            ice_trail_manager = IceTrailManager(
                constants=get_constants(),
                images=None  # 图片会在后续设置
            )

            # 恢复所有冰道
            for trail_info in ice_trail_data.get("ice_trails", []):
                from zombies.ice_trail_manager import IceTrail

                # 创建新的冰道对象
                trail = IceTrail(
                    trail_info["row"],
                    trail_info["col"],
                    constants=get_constants(),
                    images=None
                )

                # 恢复冰道状态
                trail.remaining_time = trail_info.get("remaining_time", trail.duration)
                trail.alpha = trail_info.get("alpha", 200)
                trail.sparkle_timer = trail_info.get("sparkle_timer", 0)

                # 添加到管理器
                trail_key = (trail_info["row"], trail_info["col"])
                ice_trail_manager.ice_trails[trail_key] = trail

            game["ice_trail_manager"] = ice_trail_manager
        else:
            # 如果没有保存的冰道数据，检查是否应该有冰道系统
            if level_manager and level_manager.has_special_feature("ice_car_zombie_spawn"):
                from core.game_logic import initialize_ice_trail_system
                initialize_ice_trail_system(game)
        return game

    except Exception as e:
        print(f"恢复游戏状态失败: {e}")
        return None


def create_bullet_from_save_data(bullet_data):
    """
    从保存数据创建子弹的辅助函数 - 新增月亮子弹支持
    """
    # 基本参数
    base_params = {
        "bullet_type": bullet_data["bullet_type"],
        "row": bullet_data["row"],
        "col": bullet_data["col"],
        "can_penetrate": bullet_data["can_penetrate"],
        "constants": get_constants(),
        "images": None
    }

    # 添加特定类型的参数
    if bullet_data["bullet_type"] == "melon":
        base_params["target_col"] = bullet_data.get("target_col")
    elif bullet_data["bullet_type"] == "spike":
        # 尖刺子弹需要目标僵尸，但恢复时无法精确指定，设为None让其重新寻找
        base_params["target_zombie"] = None
    elif bullet_data["bullet_type"] == "moon":
        # 月亮子弹的特殊参数在恢复时会单独处理
        pass

    bullet = bullets.create_bullet(**base_params)

    # 如果是月亮子弹，恢复其特殊状态
    if bullet_data["bullet_type"] == "moon" and hasattr(bullet, 'rotation'):
        bullet.rotation = bullet_data.get("moon_rotation", 0)
        bullet.glow_timer = bullet_data.get("moon_glow_timer", 0)
        bullet.initial_col = bullet_data.get("moon_initial_col", bullet.col)
        bullet.wave_amplitude = bullet_data.get("moon_wave_amplitude", 0.1)
        bullet.wave_frequency = bullet_data.get("moon_wave_frequency", 0.1)

    return bullet


def restore_dandelion_seeds_from_save(saved_seeds_data):
    """
    从保存数据恢复蒲公英种子的辅助函数
    """
    seeds = []
    for seed_data in saved_seeds_data:
        seed = bullets.DandelionSeed(
            start_x=seed_data["start_x"],
            start_y=seed_data["start_y"],
            target_zombie=None,  # 恢复时重新寻找目标
            constants=get_constants(),
            images=None
        )

        # 批量恢复属性
        for attr_name, attr_value in seed_data.items():
            if hasattr(seed, attr_name) and attr_name not in ["start_x", "start_y"]:
                setattr(seed, attr_name, attr_value)

        seeds.append(seed)

    return seeds


def check_level_has_save(game_db, level_num):
    """检查指定关卡是否有保存的进度"""
    return game_db.has_saved_game(level_num)  # 传入关卡编号


# 可选：添加一些验证函数来确保恢复的数据正确性
def validate_restored_bullet(bullet, bullet_data):
    """
    验证恢复的子弹数据是否正确
    """
    try:
        assert bullet.bullet_type == bullet_data["bullet_type"]
        assert bullet.row == bullet_data["row"]
        assert abs(bullet.col - bullet_data["col"]) < 0.01  # 浮点数比较
        assert bullet.can_penetrate == bullet_data["can_penetrate"]
        return True
    except AssertionError as e:
        print(f"子弹数据验证失败: {e}")
        return False


def validate_restored_seed(seed, seed_data):
    """
    验证恢复的蒲公英种子数据是否正确
    """
    try:
        assert abs(seed.start_x - seed_data["start_x"]) < 0.01
        assert abs(seed.start_y - seed_data["start_y"]) < 0.01
        assert abs(seed.current_x - seed_data["current_x"]) < 0.01
        assert abs(seed.current_y - seed_data["current_y"]) < 0.01
        return True
    except AssertionError as e:
        print(f"蒲公英种子数据验证失败: {e}")
        return False