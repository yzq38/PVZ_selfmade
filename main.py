"""
主程序文件 - 植物大战僵尸贴图版
"""
import math
import pygame
import random
import sys
import os
from animation import AnimationManager, PlantFlyingAnimation, Trophy
from core.constants import *
from rsc_mng.audio_manager import BackgroundMusicManager, initialize_sounds, play_sound_with_music_pause, \
    set_sounds_volume
from performance import PerformanceMonitor
from rsc_mng.resource_loader import load_all_images, preload_scaled_images, initialize_fonts, get_images
from database import GameDatabase, auto_save_game_progress, restore_game_from_save, check_level_has_save
from core.game_logic import (
    create_zombie_for_level, update_bullets, update_plant_shooting,
    update_dandelion_seeds, update_hammer_cooldown, handle_plant_placement,
    spawn_zombie_wave_fixed, update_card_cooldowns,
    handle_cucumber_fullscreen_explosion, update_cucumber_effects,
    update_freeze_effects, is_zombie_stunned, is_zombie_spraying,
    add_sun_safely, initialize_portal_system, update_portal_system, update_zombie_portal_interaction,
    # 冰道系统相关函数
    initialize_ice_trail_system, update_ice_trail_system, setup_ice_car_zombie_references,
    reset_ice_car_spawn_manager, update_charm_effects,update_charm_zombie_system,
    handle_plant_explosions,
    handle_zombie_battles
)
from core.level_manager import LevelManager
from core.cards_manager import get_plant_select_grid_new, cards_manager, get_available_cards_new
from shop import ShopManager, CartManager
from core.game_state_manager import GameStateManager
from core.event_handler import EventHandler
from ui import PlantSelectionManager, RendererManager, PortalManager, ConveyorBeltManager
from plants.plant_registry import plant_registry


class GameManager:
    """简化后的游戏管理器 - 协调各种专职管理器 levels"""

    def __init__(self):

        # 初始化Pygame
        pygame.init()
        pygame.mixer.init()

        # 创建游戏窗口
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("植物大战僵尸简易版")
        self.clock = pygame.time.Clock()

        # 全屏状态变量
        self.fullscreen = False
        self.screen_offset_x = 0
        self.screen_offset_y = 0
        self.screen_scale = 1.0

        # 热重载相关设置
        self.hot_reload_enabled = True  # 默认启用热重载

        # 初始化资源
        self.fonts = initialize_fonts()
        self.font_small, self.font_medium, self.font_large, self.font_tiny = self.fonts
        self.images = load_all_images()
        self.scaled_images = preload_scaled_images()
        self.sounds = initialize_sounds()

        # 初始化各种管理器
        self.music_manager = BackgroundMusicManager()
        self.performance_monitor = PerformanceMonitor()
        self.game_db = GameDatabase()
        plant_registry.set_managers(cards_manager)
        # 为状态管理器设置数据库引用
        self.state_manager = GameStateManager()
        self.state_manager.game_db = self.game_db  # 传递数据库引用
        self.plant_selection_manager = PlantSelectionManager()
        self.plant_selection_manager.game_manager = self

        # 专职管理器
        self.animation_manager = AnimationManager()
        self.conveyor_belt_manager = None
        self.seed_rain_manager = None
        self.event_handler = EventHandler(self)
        self.renderer_manager = RendererManager(self)

        # 游戏状态和设置
        self.level_settings = self.game_db.get_level_settings()
        self.game = self.state_manager.reset_game()

        # 音量设置
        self.volume = 0.7
        pygame.mixer.music.set_volume(self.volume)
        set_sounds_volume(self.sounds, self.volume)

        # 铲子配置
        self.shovel = {
            "x": SHOVEL_X, "y": SHOVEL_Y,
            "width": SHOVEL_WIDTH, "height": SHOVEL_HEIGHT,
            "color": SHOVEL_COLOR
        }

        # 游戏表面
        self.game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.shop_manager = ShopManager()
        self.coins = self.game_db.get_coins()

        # 初始化小推车管理器
        self.cart_manager = CartManager(self.shop_manager, self.images, self.sounds)
        # 确保锤子相关的初始化
        # 游戏状态中初始化锤子冷却时间
        if self.game and "hammer_cooldown" not in self.game:
            self.game["hammer_cooldown"] = 0
        # 确保传送门管理器的初始化字段存在
        if self.game and "portal_manager" not in self.game:
            self.game["portal_manager"] = None

        # 确保商店管理器有锤子检查方法
        if not hasattr(self.shop_manager, 'has_hammer'):
            # 为商店管理器添加锤子检查方法
            def has_hammer():
                return self.shop_manager.is_purchased('hammer')

            self.shop_manager.has_hammer = has_hammer

    def reset_carts(self):
        """重置小推车系统"""
        self.cart_manager.reset_all_carts()

    def reset_portal_system(self):
        """重置传送门系统"""
        if "portal_manager" in self.game:
            self.game["portal_manager"] = None

    def _handle_coin_drop(self):
        """处理僵尸死亡时的金币掉落"""
        coin_drop_chance = random.random()
        if coin_drop_chance < 0.01:  # 1%概率掉落10￥
            self.add_coins(10)
        elif coin_drop_chance < 0.06:  # 5%概率掉落5￥（累计概率6%，所以是5%）
            self.add_coins(5)
        elif coin_drop_chance < 0.16:  # 10%概率掉落1￥（累计概率16%，所以是10%）
            self.add_coins(1)

    def add_coins(self, amount):
        """安全地增加金币数量"""
        self.coins += amount
        if self.coins < 0:
            self.coins = 0
        # 同步保存到数据库
        self.game_db.set_coins(self.coins)

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if not self.fullscreen:
            # 切换到全屏
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        else:
            # 切换到窗口模式
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
            self.fullscreen = False

        # 更新屏幕尺寸
        screen_width, screen_height = self.screen.get_size()

        # 计算缩放比例和偏移量，以保持游戏内容居中
        if self.fullscreen:
            # 计算保持宽高比的缩放
            scale_x = screen_width / BASE_WIDTH
            scale_y = screen_height / BASE_HEIGHT
            self.screen_scale = min(scale_x, scale_y)

            # 计算偏移量以使内容居中
            self.screen_offset_x = (screen_width - BASE_WIDTH * self.screen_scale) / 2
            self.screen_offset_y = (screen_height - BASE_HEIGHT * self.screen_scale) / 2
        else:
            self.screen_scale = 1.0
            self.screen_offset_x = 0
            self.screen_offset_y = 0

    def transform_mouse_pos(self, pos):
        """转换鼠标位置到游戏坐标"""
        x, y = pos
        if self.fullscreen:
            # 转换全屏坐标到游戏坐标
            x = (x - self.screen_offset_x) / self.screen_scale
            y = (y - self.screen_offset_y) / self.screen_scale
        return x, y

    def update_game_logic(self):
        """更新游戏逻辑 - 添加冰道系统支持"""
        # 更新过渡动画
        should_load_game = self.state_manager.update_transition_animation()
        if should_load_game:
            self.load_pending_game_data()

        # 更新菜单动画
        new_state = self.animation_manager.update_menu_animations(self.state_manager.game_state)
        if new_state:
            self.state_manager.game_state = new_state

        # 更新植物选择动画和飞行动画（即使游戏逻辑暂停也要更新）
        if self.plant_selection_manager.show_plant_select:
            self.animation_manager.update_plant_select_animation()
            self.plant_selection_manager.update_flying_plants()

            # 更新植物选择退出动画
            exit_animation_complete = self.animation_manager.update_plant_select_exit_animation()
            if exit_animation_complete:
                # 退出动画完成，真正隐藏植物选择界面并开始游戏
                self.plant_selection_manager.hide_plant_selection()
                self.state_manager.game_paused = False

        # 更新配置重载消息显示额外
        self.animation_manager.update_config_reload_message()

        # 在过渡动画期间或菜单退出动画期间暂停游戏逻辑更新
        if (self.state_manager.is_in_transition() or
                self.animation_manager.is_menu_exit_animating()):
            return
        # 同步待处理的金币
        if '_pending_coins' in self.game and self.game['_pending_coins'] > 0:
            self.add_coins(self.game['_pending_coins'])
            self.game['_pending_coins'] = 0
        # 更新游戏主逻辑
        if (self.state_manager.game_state == "playing" and
                not self.game["game_over"] and
                not self.state_manager.should_pause_game_logic() and
                not self.plant_selection_manager.show_plant_select):  # 植物选择界面显示时暂停游戏逻辑

            # 检查配置文件是否更新
            if self.hot_reload_enabled and self.game["level_manager"].check_hot_reload():
                self.animation_manager.show_config_reload_notification()

            # 更新卡片冷却时间
            update_card_cooldowns(self.game)

            # 自动保存游戏进度（每5秒保存一次）
            if not self.game.get("level_completed", False):
                auto_save_game_progress(self.game_db, self.game, self.music_manager, self, save_interval=100)

            # 设置图片引用
            self._set_object_references()

            # 执行主游戏逻辑更新
            self._update_main_game_logic()
            if (self.conveyor_belt_manager and
                    self.game["level_manager"].current_level != 18):
                self.conveyor_belt_manager.update()

    def _set_object_references(self):
        """设置游戏对象的图片和音效引用"""
        for plant in self.game["plants"]:
            plant.images = self.images
        for zombie in self.game["zombies"]:
            zombie.images = self.images
            zombie.sounds = self.sounds
        for bullet in self.game["bullets"]:
            bullet.images = self.images
        if "dandelion_seeds" in self.game:
            for seed in self.game["dandelion_seeds"]:
                seed.images = self.images

        # 设置小推车的图片和声音引用
        self.cart_manager.images = self.images
        self.cart_manager.sounds = self.sounds
        for cart in self.cart_manager.carts.values():
            cart.images = self.images
            cart.sounds = self.sounds

    def _apply_damage_to_zombie(self, zombie, damage):
        """正确处理对僵尸的伤害：先消耗防具血量，再消耗本体血量"""
        remaining_damage = damage

        # 如果僵尸有防具且防具血量大于0，先消耗防具血量
        if zombie.has_armor and zombie.armor_health > 0:
            if remaining_damage >= zombie.armor_health:
                # 伤害足够摧毁防具
                remaining_damage -= zombie.armor_health
                zombie.armor_health = 0
            else:
                # 伤害不足以摧毁防具
                zombie.armor_health -= remaining_damage
                remaining_damage = 0

        # 如果还有剩余伤害，对本体造成伤害
        if remaining_damage > 0:
            zombie.health -= remaining_damage
            # 确保血量不会变成负数
            zombie.health = max(0, zombie.health)

    def _update_main_game_logic(self):
        """更新主要游戏逻辑 - 添加冰道系统支持"""
        # 1. 更新植物（向日葵产阳光）- 只调用一次
        update_plant_shooting(self.game, self.game["level_manager"], sounds=self.sounds)



        # 2. 更新僵尸（移动/攻击）- 这里僵尸可能会攻击植物
        self._update_zombies()
        self._update_luker_attacks()

        # 3. 检查所有植物的状态，特别处理樱桃炸弹和黄瓜
        self._handle_plant_deaths_and_explosions()

        # 4. 计算进入波次模式需要的击杀数量
        level_mgr = self.game["level_manager"]
        required_kills = level_mgr.max_waves * 5

        # 5. 检查是否进入波次模式
        if not self.game["wave_mode"] and self.game["zombies_killed"] >= required_kills:
            self.game["wave_mode"] = True
            self.game["level_manager"].start_wave_mode()
            self.game["wave_timer"] = 0

        # 6. 僵尸生成逻辑
        if self.game["wave_mode"]:
            self._update_wave_mode_spawning()
        else:
            self._update_normal_mode_spawning()

        # 7. 检查是否所有波次完成
        self._check_level_completion()

        # 8. 更新奖杯
        self._update_trophy()

        # 9. 处理淡入淡出效果
        self._update_fade_effects()

        # 10. 更新子弹（移动/碰撞）- 移除重复调用
        update_bullets(self.game, self.game["level_manager"], self.level_settings, self.sounds)
        # 更新蒲公英种子
        update_dandelion_seeds(self.game, self.game["level_manager"], self.level_settings, self.sounds)

        # 11. 随机增加阳光- 添加阳光上限检查
        if not self.game["level_manager"].has_special_feature("no_natural_sun"):
            # 只有在没有"无自然阳光"特性时才随机掉落阳光
            if random.random() < 0.01:
                self.game["sun"] = add_sun_safely(self.game["sun"], 5)

        # 12. 更新魅惑系统
        update_charm_zombie_system(self.game, self.sounds)

        # 13. 更新锤子冷却时间
        self._update_hammer_cooldown()

        # 14. 更新小推车系统
        self._update_cart_system()

        # 15. 更新传送门系统
        self._update_portal_system()


        # 16. 初始化冰道系统（如果需要）
        if self._should_have_ice_trail_system():
            initialize_ice_trail_system(self.game)

        # 17. 更新冰道系统
        update_ice_trail_system(self.game)

        # 18. 为冰车僵尸设置游戏状态引用
        setup_ice_car_zombie_references(self.game)
        # 19. 处理冰车僵尸的植物碾压
        self._handle_ice_car_crushing_direct()
        # 20. 更新种子雨系统
        self._update_seed_rain_system()

    def _update_seed_rain_system(self):
        """更新种子雨系统"""
        if self.seed_rain_manager:
            self.seed_rain_manager.update()

    def _initialize_seed_rain_system(self):
        """初始化种子雨系统"""
        level_manager = self.game.get("level_manager")
        if level_manager and level_manager.has_special_feature("seed_rain"):
            # 获取可用植物卡牌
            available_plants = get_available_cards_new(level_manager, self.level_settings, None)

            # 🔧 额外过滤：确保种子雨中不包含向日葵
            available_plants = [plant for plant in available_plants
                                if plant['type'] not in ['sunflower', 'sun_shroom']]

            from ui.seed_rain_manager import SeedRainManager
            self.seed_rain_manager = SeedRainManager(
                level_manager,
                available_plants,
                self.images
            )
        else:
            self.seed_rain_manager = None

    def _handle_ice_car_crushing_direct(self):
        """直接处理冰车僵尸碾压，确保植物被正确移除 - 修改版本：支持爆炸植物立即爆炸"""
        ice_cars = []
        for zombie in self.game["zombies"]:
            if (hasattr(zombie, 'zombie_type') and
                    zombie.zombie_type == "ice_car" and
                    not zombie.is_dying):
                ice_cars.append(zombie)

        for ice_car in ice_cars:
            # 精确的位置检查
            ice_car_row = ice_car.row
            ice_car_col_exact = ice_car.col
            ice_car_col_grid = int(round(ice_car_col_exact))

            # 检查网格重叠（考虑僵尸可能跨越网格边界）
            cols_to_check = [ice_car_col_grid]
            if abs(ice_car_col_exact - ice_car_col_grid) > 0.3:
                # 如果僵尸明显跨越网格边界，检查相邻格子
                if ice_car_col_exact < ice_car_col_grid:
                    cols_to_check.insert(0, ice_car_col_grid - 1)
                else:
                    cols_to_check.append(ice_car_col_grid + 1)

            # 查找所有可能被碾压的植物
            plants_found = []
            for col in cols_to_check:
                if 0 <= col < 9:  # 确保在游戏网格范围内
                    for plant in self.game["plants"]:
                        if plant.row == ice_car_row and plant.col == col:
                            plants_found.append((plant, col))

            # 处理找到的植物
            if plants_found:
                # 按距离排序，优先处理最近的植物
                plants_found.sort(key=lambda x: abs(x[1] - ice_car_col_exact))

                plant, plant_col = plants_found[0]

                # 关键修改：处理不同类型的植物
                if plant.plant_type == "luker":
                    # 地刺爆炸（原有逻辑）
                    if not ice_car.is_dying:
                        ice_car.start_death_animation()
                        if self.sounds and self.sounds.get("cherry_explosion"):
                            self.sounds["cherry_explosion"].play()


                elif plant.plant_type in ["cherry_bomb", "cucumber"]:
                    # 处理樱桃炸弹和黄瓜的立即爆炸
                    pass

                    # 立即触发植物爆炸
                    if plant.plant_type == "cherry_bomb":
                        if not plant.has_exploded:
                            plant.explode()  # 触发樱桃炸弹爆炸
                            # 樱桃炸弹爆炸时，标记范围内的爆炸僵尸为被爆炸杀死
                            explosion_area = plant.get_explosion_area()
                            for zombie in self.game["zombies"]:
                                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                                    zombie_row = zombie.row
                                    zombie_col = int(round(zombie.col))
                                    if (zombie_row, zombie_col) in explosion_area:
                                        zombie.death_by_explosion = True

                            # 添加音效播放标记，避免重复播放
                            if not hasattr(plant, '_crush_explosion_sound_played'):
                                plant._crush_explosion_sound_played = True
                                if self.sounds and self.sounds.get("cherry_explosion"):
                                    self.sounds["cherry_explosion"].play()

                    elif plant.plant_type == "cucumber":
                        if not plant.has_exploded:
                            plant.explode_cucumber()  # 触发黄瓜爆炸
                            # 黄瓜爆炸标记所有爆炸僵尸为被爆炸杀死
                            for zombie in self.game["zombies"]:
                                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                                    zombie.death_by_explosion = True

                            # 添加音效播放标记，避免重复播放
                            if not hasattr(plant, '_crush_explosion_sound_played'):
                                plant._crush_explosion_sound_played = True
                                if self.sounds and self.sounds.get("cherry_explosion"):
                                    self.sounds["cherry_explosion"].play()

                    # 注意：不立即移除爆炸植物，让它们的爆炸效果正常处理
                    # 爆炸植物会在爆炸动画完成后自动被移除

                else:
                    # 普通植物的碾压处理（原有逻辑）
                    try:
                        self.game["plants"].remove(plant)


                        # 更新向日葵计数
                        if plant.plant_type == "sunflower":
                            self.game["level_manager"].remove_sunflower()

                        # 播放音效
                        sound_played = False
                        sound_options = ["bite", "zombie_eating", "plant_hurt"]
                        for sound_name in sound_options:
                            if self.sounds and self.sounds.get(sound_name):
                                self.sounds[sound_name].play()
                                sound_played = True
                                break

                        if not sound_played:
                            print("警告：没有找到合适的碾压音效")

                    except ValueError:
                        print(f"警告：尝试移除不存在的植物 {plant.plant_type}")
                    except Exception as e:
                        print(f"碾压植物时发生错误：{e}")

    def _should_have_ice_trail_system(self):
        """检查当前关卡是否应该有冰道系统"""
        level_manager = self.game.get("level_manager")
        if not level_manager:
            return False

        # 检查当前关卡是否启用了冰车僵尸特性
        return level_manager.has_special_feature("ice_car_zombie_spawn")

    def _update_luker_attacks(self):
        """更新地刺的攻击（地刺对僵尸隐形，但会主动攻击）"""
        for plant in self.game["plants"]:
            if plant.plant_type == "luker":
                # 地刺主动检测并攻击踩在它身上的僵尸
                plant.attack_zombie_on_position(self.game["zombies"], self.sounds)

    def _update_hammer_cooldown(self):
        """更新锤子冷却时间"""
        if "hammer_cooldown" in self.game and self.game["hammer_cooldown"] > 0:
            self.game["hammer_cooldown"] -= 1
            if self.game["hammer_cooldown"] <= 0:
                self.game["hammer_cooldown"] = 0

    def _update_portal_system(self):
        """更新传送门系统，增加安全检查和自动修复"""
        # 检查是否应该有传送门但缺少传送门管理器
        level_manager = self.game.get("level_manager")
        if level_manager:
            should_have_portals = level_manager.has_special_feature("portal_system")
            current_portal_manager = self.game.get("portal_manager")

            # 如果应该有传送门但没有管理器，重新初始化
            if should_have_portals and not current_portal_manager:

                initialize_portal_system(self.game, level_manager)
                return

        # 更新传送门管理器状态
        if "portal_manager" in self.game and self.game["portal_manager"]:
            update_portal_system(self.game)
            # 处理僵尸与传送门的交互
            update_zombie_portal_interaction(self.game)

    def _update_wave_mode_spawning(self):
        """更新波次模式下的僵尸生成 - 修复版本"""
        level_mgr = self.game["level_manager"]
        if not level_mgr.wave_mode:
            level_mgr.start_wave_mode()

        self.game["wave_timer"] += 1
        if self.game["wave_timer"] >= WAVE_INTERVAL and level_mgr.current_wave < level_mgr.max_waves:
            zombies_per_row = [random.randint(3, 4) for _ in range(GRID_HEIGHT)]
            total_zombie_count = sum(zombies_per_row)

            #  修复：先正式开始波次
            level_mgr.start_wave(total_zombie_count)

            #  修复：再生成僵尸
            spawn_zombie_wave_fixed(self.game, level_mgr.current_wave == 1, zombies_per_row, self.sounds)

            self.game["wave_timer"] = 0

    def _update_normal_mode_spawning(self):
        """更新普通模式下的僵尸生成"""
        self.game["zombie_timer"] += 1
        if (self.game["zombie_timer"] >= NORMAL_SPAWN_DELAY and
                len(self.game["zombies"]) < 10 and
                self.game["zombies_spawned"] < MAX_NORMAL_ZOMBIES):
            zombie = create_zombie_for_level(
                random.randint(0, GRID_HEIGHT - 1),
                self.game["level_manager"],
                False,
                self.level_settings,
                self.game
            )
            zombie.images = self.images
            zombie.sounds = self.sounds

            # 如果是冰车僵尸，设置游戏状态引用
            if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car":
                zombie.set_game_state(self.game)

            self.game["zombies"].append(zombie)
            self.game["zombies_spawned"] += 1
            self.game["zombie_timer"] = 0

    def _update_zombies(game_manager):
        """更新僵尸状态 - 修复版：眩晕状态下仍能显示喷射粒子"""
        for zombie in game_manager.game["zombies"][:]:
            if zombie.is_dying:
                # 处理爆炸僵尸的特殊逻辑
                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                    if zombie.explosion_triggered and not zombie.has_exploded:
                        zombie.explosion_timer -= 1
                        if zombie.explosion_timer <= 0 and not zombie.has_exploded:
                            zombie.explode(game_manager.game["plants"], game_manager.game["zombies"])

                            if game_manager.sounds and game_manager.sounds.get("cherry_explosion"):
                                game_manager.sounds["cherry_explosion"].play()

                zombie.update(game_manager.game["plants"])
                if zombie.death_animation_timer <= 0:
                    game_manager.game["zombies"].remove(zombie)

                    if not game_manager.game["wave_mode"]:
                        game_manager.game["zombies_killed"] += 1

                    # 处理阳光掉落和金币掉落
                    should_drop_sun = True
                    if game_manager.game["wave_mode"]:
                        level_mgr = game_manager.game["level_manager"]
                        if level_mgr.no_sun_drop_in_wave_mode():
                            should_drop_sun = False

                    if should_drop_sun:
                        level_mgr = game_manager.game["level_manager"]
                        sun_amount = 0
                        if level_mgr.has_special_feature("random_sun_drop"):
                            sun_amount = random.choice([5, 10])
                        else:
                            sun_amount = 20

                        if level_mgr.has_special_feature("zombie_sun_reduce"):
                            sun_amount = int(sun_amount * 0.5)

                        if sun_amount > 0:
                            game_manager.game["sun"] = add_sun_safely(game_manager.game["sun"], sun_amount)

                    game_manager._handle_coin_drop()
                    if game_manager.game["wave_mode"]:
                        game_manager.game["level_manager"].zombie_defeated()
                continue

            # 【关键修复】：先处理黄瓜喷射粒子效果（即使僵尸被眩晕）
            zombie_id = id(zombie)
            is_spraying = is_zombie_spraying(game_manager.game, zombie)

            if is_spraying:


                if not hasattr(zombie, 'spray_particle_timer'):
                    zombie.spray_particle_timer = 0


                zombie.spray_particle_timer += 1

                if zombie.spray_particle_timer >= 10:
                    zombie.spray_particle_timer = 0


                    # 确保僵尸有粒子列表
                    if not hasattr(zombie, 'spray_particles'):
                        zombie.spray_particles = []


                    # 直接创建粒子
                    from zombies import CucumberSprayParticle

                    # 计算僵尸位置
                    zombie_x = (BATTLEFIELD_LEFT +
                                zombie.col * (GRID_SIZE + GRID_GAP) +
                                GRID_SIZE // 2)
                    zombie_y = (BATTLEFIELD_TOP +
                                zombie.row * (GRID_SIZE + GRID_GAP) +
                                GRID_SIZE // 2)

                    # 创建喷射粒子
                    particle_count = random.randint(1, 2)
                    for _ in range(particle_count):
                        offset_x = random.randint(-15, 15)
                        offset_y = random.randint(-10, 10)
                        particle = CucumberSprayParticle(
                            zombie_x + offset_x,
                            zombie_y + offset_y,
                            direction=-1  # 向左喷射
                        )
                        zombie.spray_particles.append(particle)


            # 更新已存在的喷射粒子（即使僵尸被眩晕）
            if hasattr(zombie, 'spray_particles'):
                particles_to_remove = []
                for particle in zombie.spray_particles:
                    if not particle.update():
                        particles_to_remove.append(particle)

                for particle in particles_to_remove:
                    zombie.spray_particles.remove(particle)




            # 检查僵尸是否被眩晕，眩晕状态下跳过移动等逻辑
            if is_zombie_stunned(game_manager.game, zombie):
                continue  # 眩晕的僵尸不移动，但上面已经处理了喷射粒子

            # 关键新增：检查僵尸是否在战斗状态
            is_in_battle = hasattr(zombie, 'is_attacking') and zombie.is_attacking

            # 冰车僵尸和巨人僵尸的特殊处理
            should_continue_moving = False

            if hasattr(zombie, 'zombie_type'):
                if zombie.zombie_type == "ice_car":
                    # 冰车僵尸始终继续移动，不受战斗状态影响
                    should_continue_moving = True
                elif zombie.zombie_type == "giant":
                    # 巨人僵尸在战斗时保持砸击动作，但不移动
                    should_continue_moving = False

            # 决定是否应该更新僵尸移动
            if should_continue_moving or not is_in_battle:
                # 过滤植物列表，移除对该僵尸不可见的地刺
                visible_plants = []
                for plant in game_manager.game["plants"]:
                    if plant.plant_type == "luker":
                        if (hasattr(plant, 'is_visible_to_zombie') and
                                callable(getattr(plant, 'is_visible_to_zombie', None)) and
                                plant.is_visible_to_zombie(zombie)):
                            visible_plants.append(plant)
                    else:
                        visible_plants.append(plant)

                # 更新僵尸状态
                zombie.update(visible_plants)
            else:
                # 僵尸在战斗状态下不移动，但可以执行其他动作
                # 这里可以添加战斗动画或特殊行为
                pass

            # 检查边界碰撞和游戏结束条件
            zombie_center_col = zombie.col + 0.3

            if zombie_center_col < 0:
                if game_manager.cart_manager.has_cart_in_row(zombie.row):
                    game_manager.cart_manager.trigger_cart_in_row(zombie.row)
                else:
                    game_manager.game["game_over"] = True
                    if not game_manager.game["game_over_sound_played"] and game_manager.sounds.get("game_over"):
                        play_sound_with_music_pause(game_manager.sounds["game_over"],
                                                    music_manager=game_manager.music_manager)
                        game_manager.game["game_over_sound_played"] = True

            # 检查僵尸死亡
            if zombie.health <= 0 and not zombie.is_dying:
                # 爆炸僵尸的特殊处理
                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                    if not hasattr(zombie, 'death_by_explosion'):
                        zombie.death_by_explosion = False

                    if not zombie.death_by_explosion:
                        zombie.explosion_triggered = True
                        zombie.explosion_timer = zombie.explosion_delay

                zombie.start_death_animation()

                if not game_manager.game["wave_mode"]:
                    game_manager.game["zombies_killed"] += 1

                # 处理阳光掉落
                should_drop_sun = True
                if game_manager.game["wave_mode"]:
                    level_mgr = game_manager.game["level_manager"]
                    if level_mgr.no_sun_drop_in_wave_mode():
                        should_drop_sun = False

                if should_drop_sun:
                    level_mgr = game_manager.game["level_manager"]
                    if level_mgr.has_special_feature("random_sun_drop"):
                        sun_amount = random.choice([5, 10])
                        game_manager.game["sun"] = add_sun_safely(game_manager.game["sun"], sun_amount)
                    else:
                        game_manager.game["sun"] = add_sun_safely(game_manager.game["sun"], 20)

                game_manager._handle_coin_drop()

                if game_manager.game["wave_mode"]:
                    game_manager.game["level_manager"].zombie_defeated()

    def _handle_plant_deaths_and_explosions(self):
        """处理植物死亡和爆炸 - 增强版：正确处理阵营攻击"""
        plants_to_remove = []

        for plant in self.game["plants"]:
            if plant.plant_type in ["cherry_bomb", "cucumber"]:
                # 特殊处理爆炸植物
                if plant.health <= 0 and not plant.has_exploded:
                    if plant.plant_type == "cherry_bomb":
                        plant.explode()
                    elif plant.plant_type == "cucumber":
                        plant.explode_cucumber()

                # 检查是否刚刚爆炸（立即处理伤害）
                if plant.has_exploded and not hasattr(plant, '_damage_applied'):
                    if plant.plant_type == "cherry_bomb":
                        # *** 关键修改：使用修复后的樱桃炸弹方法 ***
                        if hasattr(plant, 'apply_explosion_damage'):
                            plant.apply_explosion_damage(self.game["zombies"])
                        else:
                            # 备用方案：手动处理樱桃炸弹伤害，排除魅惑僵尸
                            explosion_area = plant.get_explosion_area()
                            for zombie in self.game["zombies"]:
                                # 跳过魅惑僵尸
                                if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                                    continue
                                if hasattr(zombie, 'team') and zombie.team == "plant":
                                    continue

                                zombie_grid_row = zombie.row
                                zombie_grid_col = int(round(zombie.col))
                                if (zombie_grid_row, zombie_grid_col) in explosion_area:
                                    if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                                        zombie.death_by_explosion = True
                                    self._apply_damage_to_zombie(zombie, plant.explosion_damage)

                    elif plant.plant_type == "cucumber":
                        pass

                    plant._damage_applied = True

                if plant.should_be_removed:
                    plants_to_remove.append(plant)

            else:
                # 处理其他植物的死亡
                if plant.health <= 0:
                    plants_to_remove.append(plant)

        # 移除已死亡的植物
        for plant in plants_to_remove:
            if plant in self.game["plants"]:
                self.game["plants"].remove(plant)
                if plant.plant_type == "sunflower":
                    self.game["level_manager"].remove_sunflower()

    def _update_cart_system(self):
        """更新小推车系统 - 确保正确处理爆炸僵尸"""
        self.cart_manager.check_zombie_trigger(self.game["zombies"])
        hit_zombies = self.cart_manager.update_carts(self.game["zombies"])

        for zombie in hit_zombies:
            if zombie in self.game["zombies"]:
                # *** 关键修改：小推车撞击爆炸僵尸时标记为被爆炸杀死 ***
                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                    zombie.death_by_explosion = True

                zombie.start_death_animation()

    def _check_level_completion(self):
        """检查关卡是否完成"""
        level_mgr = self.game["level_manager"]
        if (self.game["wave_mode"] and level_mgr.all_waves_completed and
                not level_mgr.trophy and len(self.game["zombies"]) == 0 and
                level_mgr.current_wave >= level_mgr.max_waves):
            trophy_x = BASE_WIDTH // 2 - 30
            trophy_y = BASE_HEIGHT // 2 - 40
            level_mgr.create_trophy(trophy_x, trophy_y, self.images.get('trophy_img'))
            # 奖杯出现时立即清除保存进度和标记通关
            current_game_level = level_mgr.current_level
            self.game_db.mark_level_completed(current_game_level)
            self.game_db.clear_saved_game(current_game_level)
            self.game["level_completed"] = True

    def _update_trophy(self):
        """更新奖杯状态"""
        level_mgr = self.game["level_manager"]
        if level_mgr.trophy:
            level_mgr.trophy.update()
            if level_mgr.trophy.explosion_complete and self.game["fade_state"] == "none":
                self.game["fade_state"] = "fading_out"
                self.game["fade_timer"] = 0

    def _update_fade_effects(self):
        """更新淡入淡出效果"""
        if self.game["fade_state"] != "none":
            self.game["fade_timer"] += 1
            if self.game["fade_state"] == "fading_out":
                self.game["fade_alpha"] = min(255,
                                              int(255 * (self.game["fade_timer"] / self.game["fade_duration"])))
                if self.game["fade_timer"] >= self.game["fade_duration"]:
                    self.game["fade_state"] = "fading_in"
                    self.game["fade_timer"] = 0
                    self.state_manager.switch_to_level_select()
                    self.game = self.state_manager.reset_game()
            elif self.game["fade_state"] == "fading_in":
                self.game["fade_alpha"] = max(0, 255 - int(
                    255 * (self.game["fade_timer"] / self.game["fade_duration"])))
                if self.game["fade_timer"] >= self.game["fade_duration"]:
                    self.game["fade_state"] = "none"
                    self.game["fade_alpha"] = 0

    def get_available_cards_for_current_state(self):
        """获取当前状态下的可用卡片 - 修复：支持第七卡槽，解决空选择状态bug"""
        if self.plant_selection_manager.show_plant_select:
            # 植物选择期间：只显示已完成选择的植物卡片（不包含飞行中的）
            return self.plant_selection_manager.get_selected_plant_cards()
        elif (self.game["level_manager"].current_level >= 9 and
              self.plant_selection_manager.has_selected_plants()):
            # 已选择植物，显示选中的植物卡片
            base_cards = get_available_cards_new(self.game["level_manager"], self.level_settings,
                                                 self.plant_selection_manager.selected_plants_for_game)
        else:
            # 修复：第8关及以下，或者第9关以上但没有选择植物时，使用默认植物
            # 关键修复：确保即使在第9关以上，如果没有选择植物也要显示所有可用植物
            if self.game["level_manager"].current_level >= 9:
                # 第9关以上但没有选择植物时，显示所有可用植物供选择
                # 而不是应用任何限制
                base_cards = get_available_cards_new(self.game["level_manager"], self.level_settings,
                                                     None)
            else:
                # 第8关及以下，使用默认植物
                base_cards = get_available_cards_new(self.game["level_manager"], self.level_settings, None)

        # 修复：检查是否购买了第七卡槽，如果购买了但卡片不足7张，则补充
        if hasattr(self, 'shop_manager') and self.shop_manager.has_7th_card_slot():
            if len(base_cards) < 7:
                # 定义可添加的额外植物卡片池
                extra_plant_cards = [
                    # 这里可以添加额外的植物卡片，如果需要的话
                ]

                # 计算需要添加的卡片数量
                cards_needed = 7 - len(base_cards)

                # 从额外卡片池中添加卡片，但不超过可用的额外植物数量
                for i in range(min(cards_needed, len(extra_plant_cards))):
                    # 确保不添加重复的植物类型
                    extra_card = extra_plant_cards[i]
                    if not any(card["type"] == extra_card["type"] for card in base_cards):
                        base_cards.append(extra_card.copy())

                    # 如果已经凑够7张卡，停止添加
                    if len(base_cards) >= 7:
                        break

        return base_cards

    def should_save_game_on_exit(self):
        """
        检查游戏退出时是否应该保存游戏进度
        修复：改进植物选择页面状态判断
        """
        # 传送带关卡总是允许保存（除非游戏已结束）
        if (self.game.get("level_manager") and
                (self.game["level_manager"].current_level == 21 or
                 self.game["level_manager"].has_special_feature("conveyor_belt"))):
            return self.state_manager.game_state == "playing" and not self.game["game_over"]
        # 如果游戏不在进行中或已经结束，不保存
        if self.state_manager.game_state != "playing" or self.game["game_over"]:
            return False

        # 获取当前关卡
        current_level = self.game["level_manager"].current_level

        # 第9关及以后的关卡需要特殊处理
        if current_level >= 9:
            # 修复：如果正在显示植物选择界面但还未选择任何植物，不保存
            # 这样可以避免保存空的植物选择状态
            if (self.plant_selection_manager.show_plant_select and
                    not self.plant_selection_manager.has_selected_plants()):
                return False
            # 其他情况都保存（包括植物选择页面有已选植物的情况）
            return True

        # 第8关及以下的关卡，只有不在植物选择界面时才保存
        return not self.plant_selection_manager.show_plant_select

    def load_pending_game_data(self):
        """
        加载待处理的游戏数据
        修复：改进植物选择状态的恢复逻辑，特别处理传送带和种子雨关卡
        """
        pending_data, pending_level = self.state_manager.get_pending_game_data()

        if pending_data:
            # 加载保存的游戏
            level_manager = LevelManager("database/levels.json")
            level_manager.start_level(pending_level)
            restored_game = restore_game_from_save(pending_data, level_manager, self)
            if restored_game:
                self.game = restored_game
                music_state = pending_data.get("music_state", {})
                self.music_manager.restore_music_state(music_state)

                # 恢复小推车状态
                cart_data = pending_data.get("cart_data", {})
                if cart_data:
                    self.cart_manager.load_save_data(cart_data)
                else:
                    self.cart_manager.reinitialize_carts()
            else:
                self.game_db.clear_saved_game(pending_level)
                self.game = self.state_manager.reset_game(pending_level)
                self.reset_carts()
        else:
            # 开始新游戏
            self.game = self.state_manager.reset_game(pending_level)
            self.reset_carts()

        # 立即设置图片和声音引用
        self._set_object_references()

        # 初始化传送门系统
        level_manager = self.game.get("level_manager")
        if level_manager:
            existing_portal_manager = self.game.get("portal_manager")
            if existing_portal_manager is None:
                initialize_portal_system(self.game, level_manager)

            # 初始化种子雨系统
            self._initialize_seed_rain_system()

            # **关键修复：检查特殊关卡类型**
            is_conveyor_belt_level = level_manager.has_special_feature("conveyor_belt")
            is_seed_rain_level = level_manager.has_special_feature("seed_rain")

            # **传送带或种子雨关卡：跳过植物选择**
            if is_conveyor_belt_level or is_seed_rain_level:
                # 强制隐藏植物选择界面
                self.plant_selection_manager.hide_plant_selection()
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []
                self.state_manager.game_paused = False

                if is_conveyor_belt_level:
                    # 传送带特殊处理
                    if pending_data and "conveyor_belt_data" in pending_data and pending_data["conveyor_belt_data"]:
                        pass  # 传送带状态已在 restore_game_from_save 中恢复
                    else:
                        self.initialize_conveyor_belt()
                    print(f"传送带关卡加载完成，关卡: {level_manager.current_level}")

                if is_seed_rain_level:
                    # 种子雨无需额外初始化，已在 _initialize_seed_rain_system 中处理
                    print(f"种子雨关卡加载完成，关卡: {level_manager.current_level}")

            else:
                # **非特殊关卡：按原有逻辑处理植物选择**
                # 清理传送带和种子雨相关状态
                if hasattr(self, 'conveyor_belt_manager') and self.conveyor_belt_manager:
                    self.conveyor_belt_manager = None
                if hasattr(self, 'seed_rain_manager') and self.seed_rain_manager:
                    self.seed_rain_manager = None

                # 清理游戏选中状态
                if "selected" in self.game:
                    self.game["selected"] = None

                # 清理植物选择管理器的状态
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []

                # 非特殊关卡：按原有逻辑处理植物选择
                if pending_level >= 9:
                    # 第9关以上的逻辑...
                    current_level_manager = self.game.get("level_manager")

                    if not pending_data:
                        # 新游戏：显示植物选择界面
                        self.plant_selection_manager.show_plant_selection(current_level_manager)
                        self.animation_manager.reset_plant_select_animation()
                        self.plant_selection_manager.init_plant_select_grid(current_level_manager)
                        if not hasattr(self, '_returning_to_plant_select'):
                            self.plant_selection_manager.selected_plants_for_game = []
                            self.plant_selection_manager.flying_plants = []
                        else:
                            delattr(self, '_returning_to_plant_select')
                    else:
                        # 恢复保存的游戏逻辑...
                        plant_select_state = pending_data.get("plant_select_state", {})
                        show_plant_select = plant_select_state.get("show_plant_select", False)
                        selected_plants = plant_select_state.get("selected_plants_for_game", [])

                        self.plant_selection_manager.init_plant_select_grid(current_level_manager)

                        if show_plant_select:
                            if not selected_plants:
                                print("检测到空的植物选择状态，重新初始化植物选择界面")
                                self.plant_selection_manager.show_plant_selection(current_level_manager)
                                self.animation_manager.reset_plant_select_animation()
                                self.plant_selection_manager.selected_plants_for_game = []
                                self.plant_selection_manager.flying_plants = []
                            else:
                                self.plant_selection_manager.show_plant_selection(current_level_manager)
                                self.animation_manager.reset_plant_select_animation()
                                self.plant_selection_manager.selected_plants_for_game = selected_plants.copy()
                        else:
                            self.plant_selection_manager.hide_plant_selection()
                            if selected_plants:
                                self.plant_selection_manager.selected_plants_for_game = selected_plants.copy()
                            else:
                                self.plant_selection_manager.selected_plants_for_game = []
                            self.plant_selection_manager.flying_plants = []
                else:
                    # 第8关及以下：不显示植物选择界面
                    self.plant_selection_manager.hide_plant_selection()
                    if not pending_data:
                        self.plant_selection_manager.selected_plants_for_game = []
                        self.plant_selection_manager.flying_plants = []

                # 设置游戏暂停状态（特殊关卡不暂停）
                self.state_manager.game_paused = self.plant_selection_manager.show_plant_select

        # 切换到游戏状态
        self.state_manager.switch_to_game_state()

        # 清理待处理数据
        self.state_manager.clear_pending_game_data()

        if not pending_data:
            if "hammer_cooldown" not in self.game:
                self.game["hammer_cooldown"] = 0

    def initialize_conveyor_belt(self):
        """初始化传送带系统（仅用于传送带关卡）"""
        level_manager = self.game.get("level_manager")
        # 只在有conveyor_belt特性时初始化
        if level_manager and level_manager.has_special_feature("conveyor_belt"):
            try:
                from ui.conveyor_belt_manager import ConveyorBeltManager
                available_plants = get_available_cards_new(level_manager, self.level_settings, None)

                # 🔧 额外过滤：确保传送带中不包含向日葵
                available_plants = [plant for plant in available_plants
                                    if plant['type'] not in ['sunflower', 'sun_shroom']]

                self.conveyor_belt_manager = ConveyorBeltManager(level_manager, available_plants)
            except ImportError:
                self.conveyor_belt_manager = None
        else:
            self.conveyor_belt_manager = None
            if level_manager:
                pass

    def manual_reload_config(self):
        """手动重新加载配置"""
        if self.state_manager.game_state == "playing":
            old_name = self.game["level_manager"].get_level_name()
            reloaded = self.game["level_manager"].reload_config()
            new_name = self.game["level_manager"].get_level_name()

            if old_name != new_name or reloaded:
                self.animation_manager.show_config_reload_notification()
                print(f"配置已重新加载：{new_name}")

    def toggle_hot_reload(self):
        """切换热重载功能"""
        self.hot_reload_enabled = not self.hot_reload_enabled
        if self.state_manager.game_state == "playing":
            self.game["level_manager"].enable_hot_reload(self.hot_reload_enabled)

        status = "已启用" if self.hot_reload_enabled else "已禁用"

    def show_config_info(self):
        """显示配置信息"""
        if self.state_manager.game_state == "playing":
            config_info = self.game["level_manager"].get_config_info()
            if config_info:
                # 新增：显示特性管理器信息
                features_info = ""
                if config_info.get("current_features"):
                    features_info = f"当前特性: {', '.join(config_info['current_features'])}"

                print("=== 关卡配置信息 ===")
                print(f"配置文件: {config_info['config_path']}")
                print(f"版本: {config_info['version']}")
                print(f"总关卡数: {config_info['total_levels']}")
                print(f"热重载: {'启用' if config_info['hot_reload'] else '禁用'}")
                if features_info:
                    print(features_info)
                print("===================")

    def reset_game_with_initialization(self, keep_level=None):
        """
        重置游戏并重新初始化所有系统（传送门、小推车、冰道等）
        修复重新开始按钮传送门消失的问题
        """
        # 使用状态管理器重置游戏
        self.game = self.state_manager.reset_game(keep_level)

        # 重新设置对象引用
        self._set_object_references()

        # 重新初始化传送门系统
        level_manager = self.game.get("level_manager")
        if level_manager:
            initialize_portal_system(self.game, level_manager)
            print(f"重置后重新初始化传送门系统，关卡: {level_manager.current_level}")

        # 重新初始化小推车系统
        self.reset_carts()

        # 重置冰车生成管理器
        reset_ice_car_spawn_manager()

        # **关键修复：重置传送带系统（如果存在）**
        if hasattr(self, 'conveyor_belt_manager'):
            self.conveyor_belt_manager = None
        if hasattr(self, 'seed_rain_manager') and self.seed_rain_manager:
            self.seed_rain_manager = None

        # **新增：确保清理游戏选中状态**
        if "selected" in self.game:
            self.game["selected"] = None

        # 检查当前关卡类型并进行相应处理
        if level_manager:
            is_conveyor_belt_level = (
                    level_manager.current_level == 21 or
                    level_manager.has_special_feature("conveyor_belt")
            )
            is_seed_rain_level = (
                    level_manager.current_level == 27 or
                    level_manager.has_special_feature("seed_rain")
            )


            if is_conveyor_belt_level:
                # 传送带关卡：强制隐藏植物选择界面
                self.plant_selection_manager.hide_plant_selection()
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []
                self.state_manager.game_paused = False

                # 重新初始化传送带系统
                self.initialize_conveyor_belt()
                print(f"传送带关卡重置完成，关卡: {level_manager.current_level}")

            elif is_seed_rain_level:
                # 种子雨关卡：强制隐藏植物选择界面
                self.plant_selection_manager.hide_plant_selection()
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []
                self.state_manager.game_paused = False

                # 重新初始化种子雨系统
                self._initialize_seed_rain_system()
                print(f"种子雨关卡重置完成，关卡: {level_manager.current_level}")

            elif level_manager.current_level >= 9:
                # 非传送带的第9关及以上：重新初始化植物选择
                self.plant_selection_manager.hide_plant_selection()
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []

                # 如果需要显示植物选择界面
                if not hasattr(self, '_skip_plant_selection_on_reset'):
                    self.plant_selection_manager.show_plant_selection()
                    self.animation_manager.reset_plant_select_animation()
                    self.plant_selection_manager.init_plant_select_grid(level_manager)
                    self.state_manager.game_paused = True
            else:
                # 第8关及以下不显示植物选择
                self.plant_selection_manager.hide_plant_selection()
                self.plant_selection_manager.selected_plants_for_game = []
                self.plant_selection_manager.flying_plants = []
                self.state_manager.game_paused = False

        # 重新初始化其他必要的系统
        if "hammer_cooldown" not in self.game:
            self.game["hammer_cooldown"] = 0

    def handle_game_reset_request(self):
        """
        处理游戏重置请求（重新开始按钮、失败重置等）
        """
        if self.state_manager.game_state == "playing":
            current_level = self.game["level_manager"].current_level

            # 清除保存的游戏进度
            self.game_db.clear_saved_game(current_level)

            # 重置游戏并重新初始化所有系统
            self.reset_game_with_initialization(current_level)

            print(f"游戏已重置，关卡: {current_level}")

            return True
        return False

    def handle_game_over_reset(self):
        """
        处理游戏失败后的重置
        """
        if self.game["game_over"]:
            current_level = self.game["level_manager"].current_level

            # 清除保存的游戏进度
            self.game_db.clear_saved_game(current_level)

            # 重置游戏并重新初始化所有系统
            self.reset_game_with_initialization(current_level)

            # 重置游戏结束状态
            self.game["game_over"] = False
            self.game["game_over_sound_played"] = False

            print(f"游戏失败重置完成，关卡: {current_level}")

            return True
        return False

    def run(self):
        running = True
        while running:
            # 检查游戏状态是否改变，如果改变则切换音乐
            self.state_manager.update_game_state_music(self.music_manager)

            # 更新背景音乐管理器
            self.music_manager.update()
            self.performance_monitor.update()  # 监控性能

            # 确保音乐在播放（处理音乐自然结束的情况）
            self.music_manager.ensure_music_playing(self.state_manager.game_state)

            # 处理事件
            running = self.event_handler.handle_events()
            if not running:
                break

            # 更新游戏逻辑
            self.update_game_logic()

            # 渲染游戏
            self.renderer_manager.render_game()

            # 控制帧率
            self.clock.tick(60)

        # 程序退出前最后一次保存
        if self.state_manager.game_state == "playing" and not self.game["game_over"]:
            self.game_db.save_game_progress(self.game, self.music_manager, self)

        pygame.mixer.music.stop()
        pygame.quit()
        sys.exit()


def main():
    """主函数"""
    game_manager = GameManager()
    game_manager.run()


if __name__ == "__main__":
    main()