"""
游戏逻辑处理模块
"""
import pygame
import random



from .constants import *
from performance import SpatialGrid
from plants import Plant
from zombies import *
import bullets
from .cards_manager import get_available_cards_new, cards_manager
import bullets
from ui.portal_manager import PortalManager

from zombies import CharmEffect


class IceCarSpawnManager:
    """冰车僵尸生成管理器 - 修改版本"""

    def __init__(self):
        self.normal_mode_spawned = {}  # {row: count} - 普通模式下每行已生成的冰车数量
        self.wave_mode_spawned = set()  # 波次模式下已生成冰车的行
        self.total_zombies_spawned = 0  # 总共生成的僵尸数量
        # 新增：记录每行是否已生成过强制冰车僵尸
        self.guaranteed_ice_car_spawned = set()  # 每行是否已生成保证的冰车僵尸

    def reset(self):
        """重置生成状态"""
        self.normal_mode_spawned.clear()
        self.wave_mode_spawned.clear()
        self.guaranteed_ice_car_spawned.clear()
        self.total_zombies_spawned = 0

    def can_spawn_ice_car(self, row, is_wave_mode=False):
        """检查是否可以生成冰车僵尸 - 修改版本"""
        # 前5个僵尸必定不是冰车僵尸
        if self.total_zombies_spawned < 5:
            return False

        if is_wave_mode:
            # 波次模式：每行必出一个冰车僵尸
            return row not in self.wave_mode_spawned
        else:
            # 普通模式：修改逻辑以确保每行至少一个冰车僵尸
            current_count = self.normal_mode_spawned.get(row, 0)

            # 如果该行还没有生成过保证的冰车僵尸
            if row not in self.guaranteed_ice_car_spawned:
                # 检查是否应该强制生成冰车僵尸
                # 当该行僵尸数量达到一定程度时强制生成
                row_zombie_count = self._get_row_zombie_count(row)
                if row_zombie_count >= 3:  # 该行生成3个僵尸后必须生成冰车
                    return True
                # 或者总僵尸数量达到一定程度时也要检查
                if self.total_zombies_spawned >= 15 and current_count == 0:
                    return True

            # 如果已经有保证的冰车僵尸，按原来的随机逻辑
            if current_count >= 2:
                return False
            # 12%的概率生成冰车僵尸（比原来的8%稍高）
            return random.random() < 0.15

    def record_ice_car_spawn(self, row, is_wave_mode=False):
        """记录冰车僵尸生成"""
        if is_wave_mode:
            self.wave_mode_spawned.add(row)
        else:
            self.normal_mode_spawned[row] = self.normal_mode_spawned.get(row, 0) + 1
            # 如果这是该行的第一个冰车僵尸，标记为已生成保证冰车
            if self.normal_mode_spawned[row] == 1:
                self.guaranteed_ice_car_spawned.add(row)

    def record_zombie_spawn(self):
        """记录僵尸生成"""
        self.total_zombies_spawned += 1

    def _get_row_zombie_count(self, row):
        """获取某行已生成的僵尸总数（需要从游戏状态中获取）"""
        # 这是一个简化的实现，实际可能需要从游戏状态中统计
        return self.normal_mode_spawned.get(row, 0) * 2  # 估算值

    def should_force_ice_car_in_row(self, row):
        """检查是否应该强制在某行生成冰车僵尸"""
        return (row not in self.guaranteed_ice_car_spawned and
                self.total_zombies_spawned >= 10)


# 全局冰车生成管理器
ice_car_spawn_manager = IceCarSpawnManager()


def create_zombie_for_level(row, level_manager, is_fast=False, level_settings=None, game_state=None):
    """根据关卡管理器创建僵尸 - 修改版本：支持波次模式下冰车不快速"""
    global ice_car_spawn_manager

    # 记录僵尸生成
    ice_car_spawn_manager.record_zombie_spawn()

    # 获取僵尸基础配置
    armor_prob = level_manager.get_zombie_armor_prob()
    fast_multiplier = level_manager.get_fast_zombie_multiplier()

    # 检查全员快速
    if level_manager.has_all_fast_zombies():
        is_fast = True

    zombie_type = "normal"  # 默认类型

    # 检查是否启用了冰车僵尸特性
    if level_manager.has_special_feature("ice_car_zombie_spawn"):
        # 修复：正确获取波次模式状态
        is_wave_mode = False
        if game_state:
            is_wave_mode = game_state.get("wave_mode", False)
        elif hasattr(level_manager, 'wave_mode'):
            is_wave_mode = level_manager.wave_mode

        # 检查是否可以生成冰车僵尸
        if ice_car_spawn_manager.can_spawn_ice_car(row, is_wave_mode):
            zombie_type = "ice_car"
            ice_car_spawn_manager.record_ice_car_spawn(row, is_wave_mode)

            # 关键修改：波次模式下冰车僵尸不变成快速僵尸
            if is_wave_mode:
                is_fast = False  # 强制设置为非快速
                print(f"生成冰车僵尸在第{row}行（波次模式，非快速）")
            else:
                print(f"生成冰车僵尸在第{row}行（普通模式）")
        else:
            zombie_type = level_manager.get_random_zombie_type()
    else:
        zombie_type = level_manager.get_random_zombie_type()

    # 特殊处理：爆炸僵尸和冰车僵尸不会有护甲
    if zombie_type in ["exploding", "ice_car"]:
        armor_prob = 0

    # 创建僵尸
    zombie = create_zombie(
        row=row,
        zombie_type=zombie_type,
        has_armor_prob=armor_prob,
        is_fast=is_fast,
        wave_mode=True,
        fast_multiplier=fast_multiplier,
        constants=get_constants(),
        sounds=None,
        images=None,
        level_settings=level_settings
    )

    # 如果是冰车僵尸，立即设置游戏状态引用
    if zombie_type == "ice_car" and game_state:
        zombie.set_game_state(game_state)

    return zombie


def initialize_ice_trail_system(game_state):
    """初始化冰道管理系统"""
    if "ice_trail_manager" not in game_state:
        try:
            from zombies.ice_trail_manager import IceTrailManager
            from .constants import get_constants

            # 确保 images 已经加载
            if "images" not in game_state:
                from rsc_mng.resource_loader import load_all_images
                game_state["images"] = load_all_images()

            game_state["ice_trail_manager"] = IceTrailManager(
                constants=get_constants(),
                images=game_state.get("images")
            )
        except ImportError:
            print("警告：无法导入冰道管理器")
            game_state["ice_trail_manager"] = None


def update_ice_trail_system(game_state):
    """更新冰道系统 - 修复版本"""
    if "ice_trail_manager" in game_state and game_state["ice_trail_manager"]:
        ice_trail_manager = game_state["ice_trail_manager"]
        ice_trail_manager.update()

        # 修复：确保为僵尸应用冰道速度加成时使用正确的方法
        if "zombies" in game_state:
            # 在应用速度加成前，确保所有僵尸都有必要的基础速度属性
            for zombie in game_state["zombies"]:
                if not hasattr(zombie, 'base_speed') and hasattr(zombie, 'original_calculated_speed'):
                    zombie.base_speed = zombie.original_calculated_speed

            ice_trail_manager.apply_speed_boost_to_zombies(game_state["zombies"])


def setup_ice_car_zombie_references(game_state):
    """为冰车僵尸设置游戏状态引用"""
    if "zombies" not in game_state:
        return

    for zombie in game_state["zombies"]:
        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car":
            zombie.set_game_state(game_state)


def reset_ice_car_spawn_manager(wave_mode=False):
    """重置冰车生成管理器 - 修改版本"""
    global ice_car_spawn_manager
    if wave_mode:
        # 波次模式开始时，只重置波次相关状态
        ice_car_spawn_manager.wave_mode_spawned.clear()
    else:
        # 完全重置
        ice_car_spawn_manager.reset()


def play_zombie_hit_sound(zombie, sounds, hit_sound_played):
    """统一的僵尸受击音效播放函数"""
    if hit_sound_played or not sounds:
        return hit_sound_played

    # 冰车僵尸总是播放金属受击音效
    if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car":
        if sounds.get("armor_hit"):
            sounds["armor_hit"].play()
        return True

    # 其他僵尸按护甲状态播放音效
    if zombie.has_armor and zombie.armor_health > 0:
        if sounds.get("armor_hit"):
            sounds["armor_hit"].play()
    else:
        if sounds.get("zombie_hit"):
            sounds["zombie_hit"].play()

    return True


def update_bullets(game, level_manager, level_settings=None, sounds=None):
    """优化后的子弹更新逻辑，支持冰车僵尸的寒冰免疫和金属音效"""

    # 更新冰冻效果
    update_freeze_effects(game)

    # 创建空间分区并添加僵尸
    spatial_grid = SpatialGrid(GRID_WIDTH, GRID_HEIGHT)
    for zombie in game["zombies"]:
        spatial_grid.add_zombie(zombie)

    for bullet in game["bullets"][:]:
        # 更新子弹位置
        if bullet.update(game["zombies"]):
            game["bullets"].remove(bullet)
            continue

        # 检测子弹击中僵尸
        bullet_removed = False
        hit_any_zombie = False
        hit_sound_played = False

        # 根据子弹类型进行不同的处理
        if bullet.bullet_type == "melon":
            # 西瓜子弹特殊处理
            if not bullet.has_hit_target and bullet.has_landed:
                zombies_to_check = spatial_grid.get_zombies_in_row(bullet.row)
                target_zombie = None
                min_distance = float('inf')

                for zombie in zombies_to_check:
                    # 跳过被魅惑的僵尸
                    if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                        continue
                    if hasattr(zombie, 'team') and zombie.team == "plant":
                        continue
                    if bullet.can_hit_zombie(zombie):
                        distance = abs(zombie.col - bullet.col)
                        if distance < min_distance:
                            min_distance = distance
                            target_zombie = zombie

                if target_zombie:
                    attack_result = bullet.attack_zombie(target_zombie, level_settings)
                    if attack_result == 1:
                        hit_any_zombie = True
                        bullet.has_hit_target = True

                        if target_zombie.health <= 0 and not target_zombie.is_dying:
                            # 添加爆炸僵尸的特殊处理
                            if hasattr(target_zombie, 'zombie_type') and target_zombie.zombie_type == "exploding":
                                if not hasattr(target_zombie, 'death_by_explosion'):
                                    target_zombie.death_by_explosion = False
                                # 触发爆炸（因为不是被爆炸杀死的）
                                if not target_zombie.death_by_explosion:
                                    target_zombie.explosion_triggered = True
                                    target_zombie.explosion_timer = target_zombie.explosion_delay
                            target_zombie.start_death_animation()

                        # 使用统一的音效播放函数
                        hit_sound_played = play_zombie_hit_sound(target_zombie, sounds, hit_sound_played)
                        # 西瓜还有特殊的西瓜音效
                        if sounds and sounds.get("watermelon_hit") and not hit_sound_played:
                            sounds["watermelon_hit"].play()

                        splash_count = bullet.apply_splash_damage(game["zombies"])

                        for zombie in game["zombies"]:
                            if zombie.health <= 0 and not zombie.is_dying:
                                # 添加爆炸僵尸的特殊处理
                                if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                                    if not hasattr(zombie, 'death_by_explosion'):
                                        zombie.death_by_explosion = False
                                    # 触发爆炸（因为不是被爆炸杀死的）
                                    if not zombie.death_by_explosion:
                                        zombie.explosion_triggered = True
                                        zombie.explosion_timer = zombie.explosion_delay
                                zombie.start_death_animation()
                elif bullet.has_landed:
                    bullet.has_hit_target = True
                    splash_count = bullet.apply_splash_damage(game["zombies"])

        elif bullet.bullet_type == "psychedelic":
            # 迷幻子弹特殊处理
            if not bullet.has_hit_target and bullet.has_landed:
                zombies_to_check = spatial_grid.get_zombies_in_row(bullet.row)
                target_zombie = None
                min_distance = float('inf')

                for zombie in zombies_to_check:
                    # 跳过被魅惑的僵尸
                    if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                        continue
                    if hasattr(zombie, 'team') and zombie.team == "plant":
                        continue
                    if bullet.can_hit_zombie(zombie):
                        distance = abs(zombie.col - bullet.col)
                        if distance < min_distance:
                            min_distance = distance
                            target_zombie = zombie

                if target_zombie:
                    attack_result = bullet.attack_zombie(target_zombie, level_settings)
                    if attack_result == 1:
                        hit_any_zombie = True
                        bullet.has_hit_target = True

                        # 使用统一的音效播放函数
                        hit_sound_played = play_zombie_hit_sound(target_zombie, sounds, hit_sound_played)

                        # 迷幻子弹不造成伤害，只魅惑
                        # target_zombie的健康值不变，但会被设置pending_charm

                elif bullet.has_landed:
                    # 如果着陆但没有击中僵尸，标记为击中目标以便后续移除
                    bullet.has_hit_target = True

            # 检查迷幻子弹是否应该被移除
            if bullet.has_hit_target and bullet in game["bullets"]:
                game["bullets"].remove(bullet)

        elif bullet.bullet_type == "spike":
            # 尖刺子弹的处理逻辑
            zombies_to_check = game["zombies"]

            for zombie in zombies_to_check:
                # 跳过被魅惑的僵尸
                if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                    continue
                if hasattr(zombie, 'team') and zombie.team == "plant":
                    continue
                attack_result = bullet.attack_zombie(zombie, level_settings)
                if attack_result == 1:
                    hit_any_zombie = True

                    # 使用统一的音效播放函数
                    hit_sound_played = play_zombie_hit_sound(zombie, sounds, hit_sound_played)

                    if zombie.health <= 0 and not zombie.is_dying:
                        # 添加爆炸僵尸的特殊处理
                        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                            if not hasattr(zombie, 'death_by_explosion'):
                                zombie.death_by_explosion = False
                            # 触发爆炸（因为不是被爆炸杀死的）
                            if not zombie.death_by_explosion:
                                zombie.explosion_triggered = True
                                zombie.explosion_timer = zombie.explosion_delay
                        zombie.start_death_animation()

                    game["bullets"].remove(bullet)
                    bullet_removed = True
                    break

                elif attack_result == 2:  # 免疫
                    # 使用统一的音效播放函数
                    hit_sound_played = play_zombie_hit_sound(zombie, sounds, hit_sound_played)

                    game["bullets"].remove(bullet)
                    bullet_removed = True
                    break

        elif bullet.bullet_type == "ice":
            # 寒冰子弹的处理逻辑 - 移除重复处理
            zombies_to_check = spatial_grid.get_zombies_in_row(bullet.row)
            for zombie in zombies_to_check:
                # 跳过被魅惑的僵尸
                if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                    continue
                if hasattr(zombie, 'team') and zombie.team == "plant":
                    continue
                attack_result = bullet.attack_zombie(zombie, level_settings)
                if attack_result == 1:
                    hit_any_zombie = True

                    # 使用统一的音效播放函数
                    hit_sound_played = play_zombie_hit_sound(zombie, sounds, hit_sound_played)

                    # 冰冻音效
                    if random.random() < 0.1:
                        if sounds.get("冻结"):
                            sounds["冻结"].play()

                    if zombie.health <= 0 and not zombie.is_dying:
                        # 添加爆炸僵尸的特殊处理
                        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                            if not hasattr(zombie, 'death_by_explosion'):
                                zombie.death_by_explosion = False
                            # 触发爆炸（因为不是被爆炸杀死的）
                            if not zombie.death_by_explosion:
                                zombie.explosion_triggered = True
                                zombie.explosion_timer = zombie.explosion_delay
                        zombie.start_death_animation()
        else:
            # 普通子弹的处理逻辑（豌豆射手）
            zombies_to_check = spatial_grid.get_zombies_in_row(bullet.row)
            for zombie in zombies_to_check:
                # 跳过被魅惑的僵尸
                if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                    continue
                if hasattr(zombie, 'team') and zombie.team == "plant":
                    continue
                attack_result = bullet.attack_zombie(zombie, level_settings)
                if attack_result == 1:
                    hit_any_zombie = True

                    # 使用统一的音效播放函数
                    hit_sound_played = play_zombie_hit_sound(zombie, sounds, hit_sound_played)

                    if zombie.health <= 0 and not zombie.is_dying:
                        # 添加爆炸僵尸的特殊处理
                        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                            if not hasattr(zombie, 'death_by_explosion'):
                                zombie.death_by_explosion = False

                            if not zombie.death_by_explosion:
                                zombie.explosion_triggered = True
                                zombie.explosion_timer = zombie.explosion_delay

                        zombie.start_death_animation()

                    if not bullet.can_penetrate:
                        game["bullets"].remove(bullet)
                        bullet_removed = True
                        break
                    break

                elif attack_result == 2:  # 免疫
                    # 使用统一的音效播放函数
                    hit_sound_played = play_zombie_hit_sound(zombie, sounds, hit_sound_played)

                    if not bullet.can_penetrate:
                        game["bullets"].remove(bullet)
                        bullet_removed = True
                    break

        if bullet_removed:
            continue

        # 更新西瓜爆炸粒子效果
        if bullet.bullet_type == "melon" and bullet.show_explosion:
            bullet.update_explosion_particles()

        # 检查西瓜子弹是否应该被移除
        if (bullet.bullet_type == "melon" and bullet.has_hit_target and
                not bullet.show_explosion and bullet in game["bullets"]):
            game["bullets"].remove(bullet)


def update_charm_effects(game, sounds=None):
    """更新所有魅惑效果 - 修复版本：正确的方向和攻击逻辑"""
    if "charm_effects" not in game:
        game["charm_effects"] = {}

    # 处理待魅惑的僵尸
    for zombie in game["zombies"]:
        if hasattr(zombie, 'pending_charm') and zombie.pending_charm > 0:
            charm_duration = zombie.pending_charm
            zombie_id = id(zombie)

            if zombie_id not in game["charm_effects"]:
                # 保存原始速度（绝对值）
                original_speed = abs(getattr(zombie, 'speed', 0.01))

                # 立即应用魅惑效果
                zombie.is_charmed = True
                zombie.team = "plant"
                # 关键修复：魅惑后向右移动（正速度）
                zombie.speed = original_speed * 0.8  # 正值，向右移动，稍慢一点

                # 创建魅惑效果记录
                game["charm_effects"][zombie_id] = {
                    'zombie': zombie,
                    'duration': charm_duration,
                    'remaining': charm_duration,
                    'original_speed': -abs(original_speed)  # 原始是负速度（向左）
                }

                zombie.pending_charm = 0


    # 更新现有魅惑效果
    effects_to_remove = []
    for zombie_id, effect_data in list(game["charm_effects"].items()):
        zombie = effect_data['zombie']

        # 检查僵尸是否还存在于游戏中
        if zombie not in game["zombies"]:
            effects_to_remove.append(zombie_id)
            continue

        effect_data['remaining'] -= 1

        # 确保魅惑僵尸继续向右移动
        if zombie.speed < 0:
            zombie.speed = abs(zombie.speed) * 0.8

        if effect_data['remaining'] <= 0:
            # 恢复原始状态
            zombie.is_charmed = False
            zombie.team = "zombie"
            zombie.speed = effect_data['original_speed']  # 恢复负速度（向左）
            effects_to_remove.append(zombie_id)


    # 移除已结束的效果
    for zombie_id in effects_to_remove:
        if zombie_id in game["charm_effects"]:
            del game["charm_effects"][zombie_id]

    # 处理僵尸之间的战斗 - 传入sounds参数
    handle_zombie_battles(game, sounds)


def handle_zombie_battles(game, sounds=None):
    """处理僵尸之间的战斗 - 修复：确保魅惑僵尸和敌对僵尸都停下来战斗"""

    # 首先重置所有没有战斗对手的僵尸的攻击状态
    for zombie in game["zombies"]:
        if zombie.is_dying or not hasattr(zombie, 'is_attacking'):
            continue

        # 跳过冰车僵尸的常规战斗逻辑（它们有特殊的持续伤害）
        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "ice_car":
            continue

        if zombie.is_attacking:
            # 检查是否还有有效的战斗对手
            has_battle_opponent = False
            zombie_team = getattr(zombie, 'team', 'zombie')

            for other_zombie in game["zombies"]:
                if (other_zombie != zombie and
                        not other_zombie.is_dying and
                        zombie.row == other_zombie.row):

                    other_team = getattr(other_zombie, 'team', 'zombie')
                    if (zombie_team != other_team and
                            abs(zombie.col - other_zombie.col) < 0.8):  # 增加战斗范围
                        has_battle_opponent = True
                        break

            if not has_battle_opponent:
                zombie.is_attacking = False
                if hasattr(zombie, 'battle_timer'):
                    delattr(zombie, 'battle_timer')

    # 处理冰车僵尸的持续伤害（特殊处理）
    _handle_ice_car_continuous_damage(game, sounds)

    # 新的战斗逻辑：魅惑僵尸与敌对僵尸的战斗
    battle_groups = {}

    # 第一步：找到所有战斗对
    for zombie1 in game["zombies"]:
        if zombie1.is_dying:
            continue

        # 关键修复：检查僵尸是否被眩晕
        if is_zombie_stunned(game, zombie1):
            continue  # 眩晕的僵尸不参与战斗

        # 跳过冰车僵尸的常规战斗逻辑
        if hasattr(zombie1, 'zombie_type') and zombie1.zombie_type == "ice_car":
            continue

        zombie1_team = getattr(zombie1, 'team', 'zombie')
        zombie1_id = id(zombie1)

        if zombie1_id not in battle_groups:
            battle_groups[zombie1_id] = []

        for zombie2 in game["zombies"]:
            if zombie2.is_dying or zombie1 == zombie2:
                continue

            # 检查目标僵尸是否被眩晕
            if is_zombie_stunned(game, zombie2):
                continue  # 眩晕的僵尸不会被攻击（也不能反击）

            zombie2_team = getattr(zombie2, 'team', 'zombie')

            # 检查是否为敌对阵营且在战斗范围内
            if (zombie1_team != zombie2_team and
                    zombie1.row == zombie2.row and
                    abs(zombie1.col - zombie2.col) < 0.8):  # 增加战斗范围
                battle_groups[zombie1_id].append(zombie2)

    # 第二步：处理所有战斗
    for zombie_id, opponents in battle_groups.items():
        if not opponents:
            continue

        main_zombie = None
        for zombie in game["zombies"]:
            if id(zombie) == zombie_id and not zombie.is_dying:
                main_zombie = zombie
                break

        if not main_zombie:
            continue

        # 再次确认主攻击者没有被眩晕
        if is_zombie_stunned(game, main_zombie):
            continue

        # 跳过冰车僵尸的普通战斗逻辑（它们有特殊伤害）
        if hasattr(main_zombie, 'zombie_type') and main_zombie.zombie_type == "ice_car":
            continue

        # 设置主僵尸为攻击状态
        main_zombie.is_attacking = True

        if not hasattr(main_zombie, 'battle_timer'):
            main_zombie.battle_timer = 0
        main_zombie.battle_timer += 1

        # 设置所有敌对僵尸为攻击状态
        for opponent in opponents:
            if not opponent.is_dying:
                opponent.is_attacking = True
                if not hasattr(opponent, 'battle_timer'):
                    opponent.battle_timer = 0
                opponent.battle_timer += 1

        # 处理主僵尸的攻击（每60帧攻击一次）
        if main_zombie.battle_timer >= 60:
            main_zombie.battle_timer = 0

            # 根据僵尸类型决定攻击力
            if hasattr(main_zombie, 'zombie_type') and main_zombie.zombie_type == "giant":
                attack_damage = 50  # 巨人僵尸攻击力更高
            else:
                attack_damage = 30  # 普通攻击力

            for opponent in opponents[:]:
                if opponent.is_dying or opponent not in game["zombies"]:
                    continue

                # 确保目标没有被眩晕
                if is_zombie_stunned(game, opponent):
                    continue

                # 造成伤害
                if opponent.has_armor and opponent.armor_health > 0:
                    armor_damage = min(attack_damage, opponent.armor_health)
                    opponent.armor_health -= armor_damage
                    remaining_damage = attack_damage - armor_damage
                    if remaining_damage > 0:
                        opponent.health -= remaining_damage
                else:
                    opponent.health -= attack_damage

                # 播放攻击音效（每次攻击只播放一次）
                if sounds and sounds.get("bite"):
                    sounds["bite"].play()
                    break

                if opponent.health <= 0 and not opponent.is_dying:
                    opponent.start_death_animation()
                    opponent.is_attacking = False
                    if hasattr(opponent, 'battle_timer'):
                        delattr(opponent, 'battle_timer')

        # 处理对手的反击
        for opponent in opponents[:]:
            if (opponent.is_dying or
                    opponent not in game["zombies"] or
                    not hasattr(opponent, 'battle_timer')):
                continue

            # 眩晕的僵尸不能反击
            if is_zombie_stunned(game, opponent):
                continue

            # 跳过冰车僵尸的普通反击（它们有特殊伤害）
            if hasattr(opponent, 'zombie_type') and opponent.zombie_type == "ice_car":
                continue

            if opponent.battle_timer >= 60:
                opponent.battle_timer = 0

                # 根据僵尸类型决定攻击力
                if hasattr(opponent, 'zombie_type') and opponent.zombie_type == "giant":
                    attack_damage = 50  # 巨人僵尸攻击力更高
                else:
                    attack_damage = 30  # 普通攻击力

                if main_zombie.has_armor and main_zombie.armor_health > 0:
                    armor_damage = min(attack_damage, main_zombie.armor_health)
                    main_zombie.armor_health -= armor_damage
                    remaining_damage = attack_damage - armor_damage
                    if remaining_damage > 0:
                        main_zombie.health -= remaining_damage
                else:
                    main_zombie.health -= attack_damage

                if main_zombie.health <= 0 and not main_zombie.is_dying:
                    main_zombie.start_death_animation()
                    main_zombie.is_attacking = False
                    if hasattr(main_zombie, 'battle_timer'):
                        delattr(main_zombie, 'battle_timer')

                    # 停止所有与该僵尸的战斗
                    for other_opponent in opponents:
                        if not other_opponent.is_dying:
                            other_opponent.is_attacking = False
                            if hasattr(other_opponent, 'battle_timer'):
                                delattr(other_opponent, 'battle_timer')
                    break



def _handle_ice_car_continuous_damage(game, sounds=None):
    """处理冰车僵尸的持续伤害"""
    ice_cars = [z for z in game["zombies"]
                if hasattr(z, 'zombie_type') and z.zombie_type == "ice_car" and not z.is_dying]

    for ice_car in ice_cars:
        ice_car_team = getattr(ice_car, 'team', 'zombie')

        # 对附近的敌对僵尸造成每帧10点伤害
        for zombie in game["zombies"]:
            if zombie == ice_car or zombie.is_dying:
                continue

            zombie_team = getattr(zombie, 'team', 'zombie')

            # 只攻击不同阵营的僵尸
            if (zombie_team != ice_car_team and
                    zombie.row == ice_car.row and
                    abs(zombie.col - ice_car.col) < 1.0):

                # 造成持续伤害
                zombie.health -= 10

                # 检查是否死亡
                if zombie.health <= 0 and not zombie.is_dying:
                    # 标记为爆炸性死亡（如果是爆炸僵尸）
                    if hasattr(zombie, 'take_damage_from_explosion'):
                        zombie.take_damage_from_explosion()
                    zombie.start_death_animation()

                    # 播放击杀音效
                    if sounds and sounds.get("zombie_hit"):
                        sounds["zombie_hit"].play()
                    break  # 每帧每个冰车只播放一次音效

def update_dandelion_seeds(game, level_manager, level_settings=None, sounds=None):
    """更新蒲公英种子状态和碰撞检测 - 使用 bullets 模块，添加冰车僵尸音效支持"""
    if "dandelion_seeds" not in game:
        game["dandelion_seeds"] = []
        return

    for seed in game["dandelion_seeds"][:]:
        # 更新种子位置
        if seed.update(game["zombies"]):
            game["dandelion_seeds"].remove(seed)
            continue

        # 检测种子击中僵尸
        hit_any_zombie = False
        for zombie in game["zombies"][:]:
            if seed.attack_zombie(zombie):
                hit_any_zombie = True

                # 使用统一的音效播放函数
                play_zombie_hit_sound(zombie, sounds, False)

                # 检查僵尸是否需要开始死亡动画
                if zombie.health <= 0 and not zombie.is_dying:
                    # 添加爆炸僵尸的特殊处理
                    if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
                        if not hasattr(zombie, 'death_by_explosion'):
                            zombie.death_by_explosion = False
                        # 触发爆炸（因为不是被爆炸杀死的）
                        if not zombie.death_by_explosion:
                            zombie.explosion_triggered = True
                            zombie.explosion_timer = zombie.explosion_delay

                    zombie.start_death_animation()

                # 种子击中后移除
                if seed in game["dandelion_seeds"]:
                    game["dandelion_seeds"].remove(seed)
                break


def update_plant_shooting(game, level_manager, sounds=None):
    """更新植物射击逻辑 - 支持传送门穿越和月亮花攻速加成"""

    # 获取传送门管理器
    portal_manager = game.get("portal_manager")

    # 统计场上月亮花数量并应用攻速加成
    moon_flower_count = sum(1 for plant in game["plants"] if plant.plant_type == "moon_flower")
    speed_boost_percentage = min(moon_flower_count * 0.1, 0.5)  # 每个月亮花10%，最高50%

    # 更新所有月亮花的显示计数（用于UI显示）
    for plant in game["plants"]:
        if plant.plant_type == "moon_flower":
            plant.set_moon_flower_count(moon_flower_count)

    def has_zombie_in_row_ahead(plant, zombies):
        """检测植物前方是否有敌对僵尸"""
        for zombie in zombies:
            # 跳过被魅惑的僵尸
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

            if zombie.row == plant.row and zombie.col > plant.col:
                return True
        return False

    def has_any_zombie_on_map(zombies):
        """检测地图上是否有敌对僵尸"""
        for zombie in zombies:
            # 跳过被魅惑的僵尸
            if not (hasattr(zombie, 'is_charmed') and zombie.is_charmed):
                return True
        return False

    def find_nearest_zombie_in_row(plant, zombies):
        """寻找行内最近的僵尸，考虑传送门逻辑"""
        return find_nearest_zombie_with_portal(plant, zombies, portal_manager)

    for plant in game["plants"]:
        # 应用月亮花攻速加成到射击型植物
        if hasattr(plant, 'shoot_timer') and speed_boost_percentage > 0:
            # 增加射击计时器的增长速度（相当于减少射击延迟）
            bonus_increment = 1.0 + speed_boost_percentage
            plant.shoot_timer += (bonus_increment - 1.0)  # 额外增量

        update_result = plant.update()

        # 处理向日葵产生阳光
        if isinstance(update_result, int) and update_result > 0:
            game["sun"] = add_sun_safely(game["sun"], update_result)

        # 检测是否有新僵尸波次出现
        if plant.plant_type in ["shooter", "melon_pult", "cattail", "dandelion", "lightning_flower", "ice_cactus",
                                "moon_flower","psychedelic_pitcher"]:
            if plant.plant_type == "cattail":
                has_target = has_any_zombie_on_map(game["zombies"])
            elif plant.plant_type in ["dandelion", "lightning_flower"]:
                has_target = has_any_zombie_on_map(game["zombies"])
            elif plant.plant_type in ["ice_cactus", "moon_flower"]:
                has_target = has_zombie_in_row_ahead(plant, game["zombies"])
            else:
                has_target = has_zombie_in_row_ahead(plant, game["zombies"])
            plant.check_for_new_wave(has_target)

        # 射击逻辑
        if plant.can_shoot():
            should_shoot = False
            target_zombie = None

            if plant.plant_type == "cattail":
                # 修复：猫尾草寻找非魅惑僵尸
                non_charmed_zombies = [z for z in game["zombies"]
                                       if not (hasattr(z, 'is_charmed') and z.is_charmed)]
                if non_charmed_zombies:
                    target_zombie = plant.find_nearest_zombie(non_charmed_zombies)
                    should_shoot = target_zombie is not None
            elif plant.plant_type in ["dandelion", "lightning_flower"]:
                should_shoot = has_any_zombie_on_map(game["zombies"])
            elif plant.plant_type in ["shooter", "melon_pult", "moon_flower","psychedelic_pitcher"]:
                should_shoot = has_zombie_in_row_ahead(plant, game["zombies"])
            elif plant.plant_type == "ice_cactus":
                should_shoot = has_zombie_in_row_ahead(plant, game["zombies"])

            if should_shoot:
                bullet = None

                # 使用 bullets.create_bullet 工厂函数，修复：直接传递传送门参数
                if plant.plant_type == "melon_pult":
                    # 西瓜投手：创建西瓜子弹，考虑传送门目标
                    target_col = get_bullet_target_col_with_portal(plant, game["zombies"], portal_manager)

                    bullet = bullets.create_bullet(
                        bullet_type="melon",
                        row=plant.row,
                        col=plant.col + 0.5,
                        target_col=target_col,
                        constants=get_constants(),
                        images=None
                    )

                elif plant.plant_type == "moon_flower":
                    # 月亮花:创建月亮子弹
                    bullet = bullets.create_bullet(
                        bullet_type="moon",
                        row=plant.row,
                        col=plant.col + 0.5,
                        constants=get_constants(),
                        images=plant.images,
                        portal_manager=portal_manager,
                        source_plant_row=plant.row,
                        source_plant_col=plant.col
                    )
                    if sounds and sounds.get("moon_flower_shoot"):
                        sounds["moon_flower_shoot"].play()

                elif plant.plant_type == "cattail":
                    # 猫尾草：创建追踪尖刺子弹
                    bullet = bullets.create_bullet(
                        bullet_type="spike",
                        row=plant.row,
                        col=plant.col + 0.5,
                        target_zombie=target_zombie,
                        constants=get_constants(),
                        images=None
                    )

                elif plant.plant_type == "dandelion":
                    # 蒲公英：创建飘散种子（特殊处理）
                    seeds = plant.create_dandelion_seeds(game["zombies"])
                    if "dandelion_seeds" not in game:
                        game["dandelion_seeds"] = []
                    game["dandelion_seeds"].extend(seeds)

                    if sounds and sounds.get("dandelion_shoot"):
                        sounds["dandelion_shoot"].play()

                elif plant.plant_type == "lightning_flower":
                    # 闪电花：执行链式攻击
                    zombies_hit = plant.perform_lightning_attack(game["zombies"], sounds)
                    if zombies_hit > 0:
                        if sounds and sounds.get("lightning_flower"):
                            sounds["lightning_flower"].play()

                elif plant.plant_type == "ice_cactus":
                    # 寒冰仙人掌：创建寒冰穿透子弹，支持传送门穿越
                    bullet = bullets.create_bullet(
                        bullet_type="ice",
                        row=plant.row,
                        col=plant.col + 0.5,
                        can_penetrate=True,
                        constants=get_constants(),
                        images=None,
                        portal_manager=portal_manager,
                        source_plant_row=plant.row,
                        source_plant_col=plant.col
                    )

                    if sounds and sounds.get("ice_cactus_shoot"):
                        sounds["ice_cactus_shoot"].play()

                elif plant.plant_type == "psychedelic_pitcher":

                    target_col = get_bullet_target_col_with_portal(plant, game["zombies"], portal_manager)
                    bullet = bullets.create_bullet(
                        bullet_type="psychedelic",
                        row=plant.row,
                        col=plant.col + 0.5,
                        target_col=target_col,
                        constants=get_constants(),
                        images=None
                    )

                else:
                    # 豌豆射手：创建普通子弹，支持传送门穿越
                    can_penetrate = level_manager.has_bullet_penetration()
                    random_penetration_prob = level_manager.get_random_penetration_prob()
                    if random_penetration_prob > 0 and random.random() < random_penetration_prob:
                        can_penetrate = True

                    bullet = bullets.create_bullet(
                        bullet_type="pea",
                        row=plant.row,
                        col=plant.col + 0.5,
                        can_penetrate=can_penetrate,
                        constants=get_constants(),
                        images=None,
                        portal_manager=portal_manager,
                        source_plant_row=plant.row,
                        source_plant_col=plant.col
                    )

                # 将子弹添加到游戏状态
                if bullet:
                    game["bullets"].append(bullet)

                plant.reset_shoot_timer()

def update_hammer_cooldown(game):
    """更新锤子冷却时间"""
    if "hammer_cooldown" in game and game["hammer_cooldown"] > 0:
        game["hammer_cooldown"] -= 1
        if game["hammer_cooldown"] <= 0:
            game["hammer_cooldown"] = 0


def handle_plant_placement(game, cards, x, y, level_manager, level_settings=None, sounds=None, state_manager=None):
    """处理植物种植逻辑"""
    adj_x = x - BATTLEFIELD_LEFT
    adj_y = y - BATTLEFIELD_TOP

    if 0 <= adj_x < total_battlefield_width and 0 <= adj_y < total_battlefield_height:
        # 计算点击的网格坐标
        col = 0
        while col < GRID_WIDTH and adj_x > (col + 1) * GRID_SIZE + col * GRID_GAP:
            col += 1
        row = 0
        while row < GRID_HEIGHT and adj_y > (row + 1) * GRID_SIZE + row * GRID_GAP:
            row += 1

        # 找到该位置的植物（如有）
        target_plant = None
        for p in game["plants"]:
            if p.row == row and p.col == col:
                target_plant = p
                break

        # **修复：铲子模式 - 移除植物但保持铲子选中状态**
        if game["selected"] == "shovel" and target_plant:
            if target_plant.plant_type == "sunflower":
                level_manager.remove_sunflower()
            game["plants"].remove(target_plant)

            # **关键修复：不清除铲子选中状态，让铲子保持选中**
            # 原来的代码会设置 game["selected"] = None，现在移除这行

            # 立即清除植物预览
            if state_manager:
                state_manager.clear_plant_preview()
            return True

        # 锤子模式：杀死该格子内的所有僵尸 - **提前到冰道检查之前**
        elif game["selected"] == "hammer":
            # 检查锤子冷却状态
            hammer_cooldown = game.get("hammer_cooldown", 0)
            if hammer_cooldown > 0:
                return False

            # 杀死指定格子内的所有僵尸（改进的碰撞检测）
            zombies_killed = 0
            for zombie in game["zombies"][:]:  # 使用切片复制避免迭代时修改列表
                zombie_row = int(zombie.row)

                # 只检查同一行的僵尸
                if zombie_row == row:
                    # 计算僵尸的实际占用范围
                    zombie_size = getattr(zombie, 'size_multiplier', 1.0)
                    zombie_left = zombie.col
                    zombie_right = zombie.col + zombie_size
                    zombie_center = zombie.col + zombie_size / 2

                    # 格子的范围
                    grid_left = col
                    grid_right = col + 1

                    # 计算重叠范围
                    overlap_left = max(zombie_left, grid_left)
                    overlap_right = min(zombie_right, grid_right)
                    overlap_length = max(0, overlap_right - overlap_left)

                    # 判断条件：僵尸的四分之一以上在格子内，或者僵尸中心在格子内
                    zombie_quarter_size = zombie_size / 4
                    is_quarter_inside = overlap_length >= zombie_quarter_size
                    is_center_inside = grid_left <= zombie_center <= grid_right

                    # 如果满足任一条件，则杀死僵尸
                    if is_quarter_inside or is_center_inside:
                        # 杀死僵尸
                        game["zombies"].remove(zombie)
                        zombies_killed += 1

                        # 更新击杀计数器（只在非波次模式下计算）
                        if not game.get("wave_mode", False):
                            game["zombies_killed"] += 1

                        # 处理阳光掉落
                        should_drop_sun = True
                        if game.get("wave_mode", False):
                            level_mgr = game.get("level_manager")
                            if level_mgr and level_mgr.no_sun_drop_in_wave_mode():
                                should_drop_sun = False

                        if should_drop_sun:
                            level_mgr = game.get("level_manager")
                            if level_mgr and level_mgr.has_special_feature("random_sun_drop"):
                                sun_amount = random.choice([5, 10])
                                game["sun"] = add_sun_safely(game["sun"], sun_amount)
                            else:
                                game["sun"] = add_sun_safely(game["sun"], 15)

                        # 处理金币掉落
                        if hasattr(game, '_game_manager') and game['_game_manager']:
                            game['_game_manager']._handle_coin_drop()
                        else:
                            coin_drop_chance = random.random()
                            coins_to_add = 0
                            if coin_drop_chance < 0.01:
                                coins_to_add = 10
                            elif coin_drop_chance < 0.05:
                                coins_to_add = 5
                            elif coin_drop_chance < 0.10:
                                coins_to_add = 1

                            if coins_to_add > 0:
                                if '_pending_coins' not in game:
                                    game['_pending_coins'] = 0
                                game['_pending_coins'] += coins_to_add

                        # 重要：如果在波次模式下，需要更新波次进度
                        if game.get("wave_mode", False):
                            level_mgr = game.get("level_manager")
                            if level_mgr:
                                level_mgr.zombie_defeated()

            # 如果杀死了僵尸，播放音效并设置冷却时间
            if zombies_killed > 0:
                if sounds and sounds.get("hammer_hit"):
                    sounds["hammer_hit"].play()

                game["hammer_cooldown"] = HAMMER_COOLDOWN_TIME
                # **关键修复：锤子使用后清除选中状态（保持原有行为）**
                game["selected"] = None

                if state_manager:
                    state_manager.clear_plant_preview()

                print(f"锤子击杀了 {zombies_killed} 只僵尸！")
                return True
            else:
                print("该格子内没有僵尸可以击杀")
                return False

        # **现在检查冰道系统（放在锤子逻辑之后）**
        if "ice_trail_manager" in game and game["ice_trail_manager"]:
            ice_trail_manager = game["ice_trail_manager"]
            if ice_trail_manager.has_ice_trail_at(row, col):
                # 冰道上不能种植物，播放错误音效
                if sounds and sounds.get("plant_place_fail"):
                    sounds["plant_place_fail"].play()
                return False

        # 检查传送门占用情况
        if "portal_manager" in game and game["portal_manager"]:
            portal_manager = game["portal_manager"]
            if not portal_manager.can_place_plant_at(row, col):

                if sounds and sounds.get("plant_place_fail"):
                    sounds["plant_place_fail"].play()
                return False


        # 植物模式：放置植物
        if game["selected"] in [c["type"] for c in cards]:
            selected_card = next(c for c in cards if c["type"] == game["selected"])

            # 使用统一的卡牌管理器检查冷却时间 - 更新：使用特性管理系统
            cooldown_active = False

            # 检查是否需要冷却（第八关或关卡特殊设置） - 使用特性管理系统
            if (level_manager.has_card_cooldown() or
                    (level_settings and level_settings.get("all_card_cooldown", False)) or
                    level_manager.current_level == 8):  # 第八关强制启用冷却

                if game["selected"] in game["card_cooldowns"]:
                    if game["card_cooldowns"][game["selected"]] > 0:
                        cooldown_active = True

            if cooldown_active:
                return False  # 卡牌还在冷却中，不能使用

            # 如果该位置有不满血坚果墙，则可以修复
            if game["selected"] == "wall_nut":
                if (target_plant and
                        target_plant.plant_type == "wall_nut" and
                        target_plant.health < target_plant.max_health):

                    # 修复坚果墙到满血
                    target_plant.health = target_plant.max_health

                    # 扣除阳光（修复成本可以和种植成本相同或更低）
                    selected_card = next(c for c in cards if c["type"] == "wall_nut")
                    repair_cost = selected_card["cost"]  # 或者设置更低的修复成本，比如 repair_cost = selected_card["cost"] // 2

                    if game["sun"] >= repair_cost:
                        game["sun"] -= repair_cost

                        # 播放音效
                        if sounds and sounds.get("plant_place"):
                            sounds["plant_place"].play()

                        # 设置卡牌冷却（如果启用）
                        if (level_manager.has_card_cooldown() or
                                (level_settings and level_settings.get("all_card_cooldown", False)) or
                                level_manager.current_level == 8):
                            cooldown_time = cards_manager.get_card_cooldown_time("wall_nut", level_manager)
                            game["card_cooldowns"]["wall_nut"] = cooldown_time

                        # 立即清除植物预览
                        if state_manager:
                            state_manager.clear_plant_preview()

                        return True
                    else:
                        return False  # 阳光不足，无法修复

            # 检查位置是否为空且阳光足够
            if not target_plant and game["sun"] >= selected_card["cost"]:
                # 特殊检查：向日葵限制 - 使用特性管理系统
                if game["selected"] == "sunflower":
                    if not level_manager.can_plant_sunflower():
                        return False  # 不能种植向日葵
                    level_manager.plant_sunflower()

                # 种植植物
                plant_type = game["selected"]
                if plant_type == "melon_pult":
                    plant_type = "melon_pult"
                elif plant_type == "cattail":
                    plant_type = "cattail"
                elif plant_type == "wall_nut":
                    plant_type = "wall_nut"
                elif plant_type == "cucumber":
                    plant_type = "cucumber"
                elif plant_type == "sun_shroom":
                    plant_type = "sun_shroom"
                elif plant_type == "psychedelic_pitcher":
                    plant_type = "psychedelic_pitcher"

                plant = Plant(row, col, plant_type, get_constants(), None, game["level_manager"])
                game["plants"].append(plant)
                game["sun"] -= selected_card["cost"]

                # 使用统一的卡牌管理器设置冷却时间 - 使用特性管理系统
                if (level_manager.has_card_cooldown() or
                        (level_settings and level_settings.get("all_card_cooldown", False)) or
                        level_manager.current_level == 8):  # 第八关强制启用冷却

                    # 使用卡牌管理器获取统一的冷却时间（包括第八关+1秒处理）
                    cooldown_time = cards_manager.get_card_cooldown_time(game["selected"], level_manager)
                    game["card_cooldowns"][game["selected"]] = cooldown_time

                # 播放种植音效
                if sounds and sounds.get("plant_place"):
                    sounds["plant_place"].play()

                # 关键修复：种植成功后立即清除植物预览
                if state_manager:
                    state_manager.clear_plant_preview()

                return True

    return False


def handle_conveyor_belt_plant_placement(game, x, y, plant_type, level_manager, sounds=None, state_manager=None):
    """
    传送带模式下的植物种植逻辑 - 不消耗阳光，不检查卡牌冷却
    """
    from utils import pixel_to_grid
    from plants import Plant

    adj_x = x - BATTLEFIELD_LEFT
    adj_y = y - BATTLEFIELD_TOP

    if 0 <= adj_x < total_battlefield_width and 0 <= adj_y < total_battlefield_height:
        # 计算点击的网格坐标
        col = 0
        while col < GRID_WIDTH and adj_x > (col + 1) * GRID_SIZE + col * GRID_GAP:
            col += 1
        row = 0
        while row < GRID_HEIGHT and adj_y > (row + 1) * GRID_SIZE + row * GRID_GAP:
            row += 1

        # 找到该位置的植物（如有）
        target_plant = None
        for p in game["plants"]:
            if p.row == row and p.col == col:
                target_plant = p
                break

        # **修复：铲子模式 - 移除植物但保持铲子选中状态**
        if plant_type == "shovel" and target_plant:
            if target_plant.plant_type == "sunflower":
                level_manager.remove_sunflower()
            game["plants"].remove(target_plant)

            # **关键修复：传送带模式下铲子使用后不清除选中状态**
            # 原来的代码会设置 game["selected"] = None，现在移除这行

            if state_manager:
                state_manager.clear_plant_preview()
            return True

        # 锤子模式：杀死该格子内的所有僵尸 - **提前到冰道检查之前**
        elif plant_type == "hammer":
            hammer_cooldown = game.get("hammer_cooldown", 0)
            if hammer_cooldown > 0:
                return False

            zombies_killed = 0
            for zombie in game["zombies"][:]:
                zombie_row = int(zombie.row)
                if zombie_row == row:
                    zombie_size = getattr(zombie, 'size_multiplier', 1.0)
                    zombie_left = zombie.col
                    zombie_right = zombie.col + zombie_size
                    zombie_center = zombie.col + zombie_size / 2

                    grid_left = col
                    grid_right = col + 1

                    overlap_left = max(zombie_left, grid_left)
                    overlap_right = min(zombie_right, grid_right)
                    overlap_length = max(0, overlap_right - overlap_left)

                    zombie_quarter_size = zombie_size / 4
                    is_quarter_inside = overlap_length >= zombie_quarter_size
                    is_center_inside = grid_left <= zombie_center <= grid_right

                    if is_quarter_inside or is_center_inside:
                        game["zombies"].remove(zombie)
                        zombies_killed += 1

                        if not game.get("wave_mode", False):
                            game["zombies_killed"] += 1

                        should_drop_sun = True
                        if game.get("wave_mode", False):
                            level_mgr = game.get("level_manager")
                            if level_mgr and level_mgr.no_sun_drop_in_wave_mode():
                                should_drop_sun = False

                        if should_drop_sun:
                            level_mgr = game.get("level_manager")
                            if level_mgr and level_mgr.has_special_feature("random_sun_drop"):
                                sun_amount = random.choice([5, 10])
                                game["sun"] = add_sun_safely(game["sun"], sun_amount)
                            else:
                                game["sun"] = add_sun_safely(game["sun"], 15)

                        if hasattr(game, '_game_manager') and game['_game_manager']:
                            game['_game_manager']._handle_coin_drop()
                        else:
                            coin_drop_chance = random.random()
                            coins_to_add = 0
                            if coin_drop_chance < 0.01:
                                coins_to_add = 10
                            elif coin_drop_chance < 0.05:
                                coins_to_add = 5
                            elif coin_drop_chance < 0.10:
                                coins_to_add = 1

                            if coins_to_add > 0:
                                if '_pending_coins' not in game:
                                    game['_pending_coins'] = 0
                                game['_pending_coins'] += coins_to_add

                        if game.get("wave_mode", False):
                            level_mgr = game.get("level_manager")
                            if level_mgr:
                                level_mgr.zombie_defeated()

            if zombies_killed > 0:
                if sounds and sounds.get("hammer_hit"):
                    sounds["hammer_hit"].play()
                game["hammer_cooldown"] = HAMMER_COOLDOWN_TIME

                # **关键修复：传送带模式下锤子使用后清除选中状态（保持原有行为）**
                game["selected"] = None

                if state_manager:
                    state_manager.clear_plant_preview()
                print(f"锤子击杀了 {zombies_killed} 只僵尸！")
                return True
            else:
                print("该格子内没有僵尸可以击杀")
                return False

        # **新增：检查冰道系统（移到锤子逻辑之后）**
        if "ice_trail_manager" in game and game["ice_trail_manager"]:
            ice_trail_manager = game["ice_trail_manager"]
            # 检查该位置是否有冰道
            if ice_trail_manager.has_ice_trail_at(row, col):
                # 冰道上不能种植物，播放错误音效
                if sounds and sounds.get("plant_place_fail"):
                    sounds["plant_place_fail"].play()
                return False

        # 检查传送门占用情况
        if "portal_manager" in game and game["portal_manager"]:
            portal_manager = game["portal_manager"]
            if not portal_manager.can_place_plant_at(row, col):
                if sounds and sounds.get("plant_place_fail"):
                    sounds["plant_place_fail"].play()
                return False

        # 植物种植模式
        if plant_type not in ["shovel", "hammer"]:
            # 坚果墙修复检查
            if plant_type == "wall_nut":
                if (target_plant and
                        target_plant.plant_type == "wall_nut" and
                        target_plant.health < target_plant.max_health):
                    # 传送带模式：免费修复坚果墙
                    target_plant.health = target_plant.max_health
                    if sounds and sounds.get("plant_place"):
                        sounds["plant_place"].play()
                    if state_manager:
                        state_manager.clear_plant_preview()
                    return True

            # 检查位置是否为空（传送带模式不检查阳光）
            if not target_plant:
                # 特殊检查：向日葵限制
                if plant_type == "sunflower":
                    if not level_manager.can_plant_sunflower():
                        return False
                    level_manager.plant_sunflower()

                # 种植植物（传送带模式不消耗阳光）
                plant = Plant(row, col, plant_type, get_constants(), None, level_manager)
                game["plants"].append(plant)

                # 播放种植音效
                if sounds and sounds.get("plant_place"):
                    sounds["plant_place"].play()

                # 清除预览状态
                if state_manager:
                    state_manager.clear_plant_preview()

                return True

    return False

def initialize_portal_system(game_state, level_manager):
    """初始化传送门系统 - 基于特性管理器的修复版本"""
    should_have_portals = False

    if level_manager:
        current_level = level_manager.current_level

        # 直接从特性管理器获取该关卡的推荐特性
        from core.features_manager import features_manager
        recommended_features = features_manager.get_recommended_features_for_level(current_level)

        # 检查推荐特性中是否包含传送门系统
        if "portal_system" in recommended_features:
            should_have_portals = True
            print(f"关卡 {current_level} 的推荐特性包含传送门系统")

        # 备选方案：也检查level_manager的特性配置
        elif hasattr(level_manager, 'has_special_feature') and level_manager.has_special_feature("portal_system"):
            should_have_portals = True
            print(f"关卡 {current_level} 通过level_manager配置了传送门系统")

    if should_have_portals:
        # 获取传送门系统的配置参数
        from core.features_manager import features_manager
        portal_feature = features_manager.get_feature("portal_system")
        portal_config = portal_feature.default_value if portal_feature else {}

        # 创建传送门管理器
        from ui.portal_manager import PortalManager
        portal_manager = PortalManager(level_manager, auto_initialize=True)

        # 应用特性管理器中的配置（如果需要的话）
        if portal_config:
            portal_manager.switch_interval = portal_config.get("switch_interval", 20) * 60  # 转换为帧数
            # 可以根据需要应用更多配置

        game_state["portal_manager"] = portal_manager

    else:
        game_state["portal_manager"] = None
        if level_manager:
            pass


def update_portal_system(game):
    """更新传送门系统"""
    if "portal_manager" in game and game["portal_manager"]:
        game["portal_manager"].update()


def update_zombie_portal_interaction(game):
    """更新僵尸与传送门的交互 - 修复版本：阻止死亡动画期间的传送"""
    if "portal_manager" not in game or not game["portal_manager"]:
        return

    portal_manager = game["portal_manager"]

    # 检查每个僵尸是否经过传送门
    for zombie in game["zombies"][:]:
        # 关键修复：检查僵尸是否正在播放死亡动画
        if zombie.is_dying:
            continue  # 跳过正在死亡的僵尸，不允许传送

        # 检查僵尸当前位置是否有传送门
        portal = portal_manager.get_portal_at_position(int(zombie.row), int(zombie.col))
        if portal and portal.is_active:
            # 30%概率传送僵尸
            if random.random() < 0.3:  # 可以从特性配置中读取这个概率
                success = portal_manager.teleport_zombie(zombie)
                if success:
                    pass


def spawn_zombie_wave_fixed(game_state, first_wave=False, zombies_per_row=None, sounds=None):
    """生成僵尸波次 - 简化版本"""
    if first_wave and sounds and sounds.get("wave_warning"):
        sounds["wave_warning"].play()

    if zombies_per_row is None:
        zombies_per_row = [random.randint(3, 4) for _ in range(GRID_HEIGHT)]

    level_manager = game_state.get("level_manager")
    if not level_manager:
        return  # 没有关卡管理器则不生成

    # 获取配置
    all_fast = level_manager.has_all_fast_zombies()

    for row in range(GRID_HEIGHT):
        zombie_count = zombies_per_row[row]

        # 决定哪些是快速僵尸
        if all_fast:
            fast_zombie_indices = list(range(zombie_count))
        else:
            fast_zombie_indices = [random.randint(0, zombie_count - 1)] if zombie_count > 0 else []

        for i in range(zombie_count):
            # 是否为快速僵尸
            is_fast = (i in fast_zombie_indices)

            # 创建僵尸（类型由level_manager随机决定）
            zombie = create_zombie_for_level(row, level_manager, is_fast, None,game_state)

            # 设置音效和图片引用
            zombie.sounds = sounds

            # 错开位置
            zombie.col += i * 0.3
            game_state["zombies"].append(zombie)


def get_level_zombie_info(level_manager):
    """获取当前关卡的僵尸信息（用于UI显示）"""
    info = {
        "zombie_types": [],
        "special_features": []
    }

    # 获取僵尸类型和概率
    probabilities = level_manager.get_zombie_spawn_probabilities()
    for zombie_type, prob in probabilities.items():
        if prob > 0:
            info["zombie_types"].append({
                "type": zombie_type,
                "probability": prob,
                "name": get_zombie_display_name(zombie_type)
            })

    # 获取特殊特性
    if level_manager.has_all_fast_zombies():
        info["special_features"].append("全员快速")

    if level_manager.has_special_feature("zombie_immunity"):
        info["special_features"].append("僵尸免疫")

    if level_manager.has_special_feature("zombie_health_reduce"):
        info["special_features"].append("血量减少20%")

    armor_prob = level_manager.get_zombie_armor_prob()
    if armor_prob > 0.5:
        info["special_features"].append(f"高铁门率({armor_prob:.0%})")

    return info


def get_zombie_display_name(zombie_type):
    """获取僵尸类型的显示名称"""
    names = {
        "normal": "普通僵尸",
        "giant": "巨人僵尸",
        "exploding": "爆炸僵尸"
    }
    return names.get(zombie_type, "未知僵尸")

def update_card_cooldowns(game):
    """更新卡牌冷却时间"""
    if "card_cooldowns" in game:
        for card_type in list(game["card_cooldowns"].keys()):
            if game["card_cooldowns"][card_type] > 0:
                game["card_cooldowns"][card_type] -= 1
            else:
                # 冷却完成，移除记录
                del game["card_cooldowns"][card_type]


def handle_cucumber_fullscreen_explosion(game, cucumber_explosion_data, sounds=None):
    """
    处理黄瓜的全屏爆炸效果 - 修复：排除魅惑僵尸
    """
    if not cucumber_explosion_data:

        return

    stun_duration = cucumber_explosion_data['stun_duration']
    spray_duration = cucumber_explosion_data['spray_duration']
    death_probability = cucumber_explosion_data['death_probability']


    # 播放黄瓜爆炸音效
    if sounds and sounds.get("cherry_explosion"):
        sounds["cherry_explosion"].play()

    # 确保游戏状态有必要的字典
    if "zombie_stun_timers" not in game:
        game["zombie_stun_timers"] = {}

    if "cucumber_spray_timers" not in game:
        game["cucumber_spray_timers"] = {}


    affected_zombies = 0
    # 对敌对僵尸应用眩晕和喷射效果（排除魅惑僵尸）
    for zombie in game["zombies"]:
        # 跳过魅惑僵尸
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:

            continue
        if hasattr(zombie, 'team') and zombie.team == "plant":

            continue

        zombie_id = id(zombie)
        affected_zombies += 1
        # 检查僵尸是否已经冰冻，如果是则保存冰冻状态
        was_frozen = hasattr(zombie, 'is_frozen') and zombie.is_frozen
        original_speed = getattr(zombie, 'original_speed', None)
        freeze_start_time = getattr(zombie, 'freeze_start_time', None)

        # 1. 应用眩晕效果（5秒）
        game["zombie_stun_timers"][zombie_id] = stun_duration


        # 2. 设置喷射计时器（2秒）
        game["cucumber_spray_timers"][zombie_id] = spray_duration


        # 3. 50%概率在喷射后死亡（延迟执行）
        if random.random() < death_probability:
            if not hasattr(zombie, 'cucumber_marked_for_death'):
                zombie.cucumber_marked_for_death = True


        # 恢复冰冻状态（如果之前是冰冻的）
        if was_frozen:
            zombie.is_frozen = True
            if original_speed is not None:
                zombie.original_speed = original_speed
            if freeze_start_time is not None:
                zombie.freeze_start_time = freeze_start_time

    # 治疗所有受伤的植物（保持原有逻辑）
    if "cucumber_plant_healing" not in game:
        game["cucumber_plant_healing"] = {}

    for plant in game["plants"]:
        plant_key = f"{plant.row}_{plant.col}"
        game["cucumber_plant_healing"][plant_key] = spray_duration


def handle_plant_explosions(game, sounds=None):
    """处理植物爆炸效果 - 修复：排除魅惑僵尸"""
    plants_to_remove = []

    for plant in game["plants"]:
        # 处理樱桃炸弹
        if plant.plant_type == "cherry_bomb":
            if plant.should_play_explosion_sound():
                plant.mark_sound_played()
                if sounds and sounds.get("cherry_explosion"):
                    sounds["cherry_explosion"].play()

            if plant.has_exploded and not plant.explosion_started:
                # 对敌对僵尸造成伤害（排除魅惑僵尸）
                plant.apply_explosion_damage(game["zombies"])

            if plant.should_be_removed:
                plants_to_remove.append(plant)

        # 处理黄瓜炸弹
        elif plant.plant_type == "cucumber":
            if plant.should_play_explosion_sound():
                plant.mark_sound_played()
                if sounds and sounds.get("cucumber_explosion"):
                    sounds["cucumber_explosion"].play()

            # 检查是否有全屏爆炸数据
            cucumber_explosion_data = plant.get_fullscreen_explosion_data()
            if cucumber_explosion_data:
                handle_cucumber_fullscreen_explosion(game, cucumber_explosion_data, sounds)

            if plant.should_be_removed:
                plants_to_remove.append(plant)

    # 移除已爆炸完成的植物
    for plant in plants_to_remove:
        if plant in game["plants"]:
            game["plants"].remove(plant)


def update_exploding_zombies(game):
    """更新爆炸僵尸状态 - 修复：支持阵营攻击"""
    for zombie in game["zombies"]:
        if hasattr(zombie, 'zombie_type') and zombie.zombie_type == "exploding":
            if zombie.explosion_triggered and not zombie.has_exploded:
                zombie.explosion_timer -= 1
                if zombie.explosion_timer <= 0:
                    # 传入植物和僵尸列表，让爆炸僵尸能攻击敌对目标
                    zombie.explode(game["plants"], game["zombies"])

def update_cucumber_effects(game, sounds=None):
    """
    更新黄瓜效果状态 - 改进持续治疗效果
    """
    if "zombie_stun_timers" not in game:
        game["zombie_stun_timers"] = {}
    if "cucumber_spray_timers" not in game:
        game["cucumber_spray_timers"] = {}
    if "cucumber_plant_healing" not in game:
        game["cucumber_plant_healing"] = {}

    # 更新眩晕计时器
    stun_timers_to_remove = []
    for zombie_id, timer in game["zombie_stun_timers"].items():
        game["zombie_stun_timers"][zombie_id] = timer - 1
        if game["zombie_stun_timers"][zombie_id] <= 0:
            stun_timers_to_remove.append(zombie_id)

    # 移除已经结束的眩晕效果
    for zombie_id in stun_timers_to_remove:
        del game["zombie_stun_timers"][zombie_id]

    healing_to_remove = []
    for plant_key, timer in game["cucumber_plant_healing"].items():
        game["cucumber_plant_healing"][plant_key] = timer - 1

        # 每20帧治疗一次植物
        if timer % 20 == 0:
            row_str, col_str = plant_key.split('_')
            row, col = int(row_str), int(col_str)

            # 查找并治疗植物
            for plant in game["plants"]:
                if plant.row == row and plant.col == col:
                    if plant.health < plant.max_health:
                        old_health = plant.health
                        # 每次治疗50点血量
                        heal_amount = min(50, plant.max_health - plant.health)
                        plant.health = min(plant.max_health, plant.health + heal_amount)

                        # 计算治疗进度
                        health_percentage = (plant.health / plant.max_health) * 100

                    break

        if game["cucumber_plant_healing"][plant_key] <= 0:
            healing_to_remove.append(plant_key)

    # 移除已经结束的治疗效果
    for plant_key in healing_to_remove:
        del game["cucumber_plant_healing"][plant_key]

    # 更新喷射计时器
    spray_timers_to_remove = []
    zombies_to_remove = []

    for zombie_id, timer in game["cucumber_spray_timers"].items():
        game["cucumber_spray_timers"][zombie_id] = timer - 1

        # 喷射结束时检查是否需要死亡
        if game["cucumber_spray_timers"][zombie_id] <= 0:
            spray_timers_to_remove.append(zombie_id)

            # 查找对应的僵尸对象
            for zombie in game["zombies"]:
                if id(zombie) == zombie_id:
                    if hasattr(zombie, 'cucumber_marked_for_death') and zombie.cucumber_marked_for_death:
                        zombies_to_remove.append(zombie)
                    break

    # 移除已经结束的喷射效果
    for zombie_id in spray_timers_to_remove:
        del game["cucumber_spray_timers"][zombie_id]

    # 移除标记死亡的僵尸
    for zombie in zombies_to_remove:
        if zombie in game["zombies"]:
            # 在移除僵尸前检查是否处于冰冻状态
            was_frozen = hasattr(zombie, 'is_frozen') and zombie.is_frozen

            game["zombies"].remove(zombie)

            # 更新击杀计数器（只在非波次模式下计算）
            if not game.get("wave_mode", False):
                game["zombies_killed"] += 1

            # 处理阳光掉落
            should_drop_sun = True
            if game.get("wave_mode", False):
                level_mgr = game.get("level_manager")
                if level_mgr and level_mgr.no_sun_drop_in_wave_mode():
                    should_drop_sun = False

            if should_drop_sun:
                level_mgr = game.get("level_manager")
                if level_mgr and level_mgr.has_special_feature("random_sun_drop"):
                    # 随机掉落5或10阳光
                    sun_amount = random.choice([5, 10])
                    game["sun"] = add_sun_safely(game["sun"], sun_amount)
                else:
                    # 默认掉落20阳光
                    game["sun"] = add_sun_safely(game["sun"], 15)

            if hasattr(game, '_game_manager') and game['_game_manager']:
                game['_game_manager']._handle_coin_drop()
            else:
                # 如果无法访问game_manager，直接在这里实现金币掉落逻辑
                coin_drop_chance = random.random()
                coins_to_add = 0
                if coin_drop_chance < 0.01:  # 1%概率掉落10￥
                    coins_to_add = 10
                elif coin_drop_chance < 0.05:  # 5%概率掉落5￥
                    coins_to_add = 5
                elif coin_drop_chance < 0.10:  # 10%概率掉落1￥
                    coins_to_add = 1

                # 将金币数量存储到游戏状态中，稍后同步到game_manager
                if coins_to_add > 0:
                    if '_pending_coins' not in game:
                        game['_pending_coins'] = 0
                    game['_pending_coins'] += coins_to_add

            # 重要：如果在波次模式下，需要更新波次进度
            if game.get("wave_mode", False):
                level_mgr = game.get("level_manager")
                if level_mgr:
                    level_mgr.zombie_defeated()


def update_freeze_effects(game):
    """更新所有僵尸的冰冻效果 """
    current_time = pygame.time.get_ticks()
    freeze_duration = 5000  # 5秒 = 5000毫秒

    for zombie in game["zombies"]:
        if hasattr(zombie, 'is_frozen') and zombie.is_frozen:
            # 检查冰冻是否过期
            time_frozen = current_time - zombie.freeze_start_time

            if time_frozen >= freeze_duration:
                # 解除冰冻
                zombie.is_frozen = False
                if hasattr(zombie, 'original_speed'):
                    zombie.speed = zombie.original_speed
                    print(f"僵尸冰冻效果结束，速度恢复到 {zombie.speed}")
                    del zombie.original_speed
                if hasattr(zombie, 'freeze_start_time'):
                    del zombie.freeze_start_time



def is_zombie_stunned(game, zombie):
    """
    检查僵尸是否处于眩晕状态

    Args:
        game: 游戏状态字典
        zombie: 僵尸对象

    Returns:
        bool: 是否眩晕
    """
    if "zombie_stun_timers" not in game:
        return False

    zombie_id = id(zombie)
    return zombie_id in game["zombie_stun_timers"] and game["zombie_stun_timers"][zombie_id] > 0


def is_zombie_spraying(game, zombie):
    """
    检查僵尸是否正在喷射

    Args:
        game: 游戏状态字典
        zombie: 僵尸对象

    Returns:
        bool: 是否正在喷射
    """
    if "cucumber_spray_timers" not in game:
        return False

    zombie_id = id(zombie)
    return zombie_id in game["cucumber_spray_timers"] and game["cucumber_spray_timers"][zombie_id] > 0

def add_sun_safely(current_sun, amount):
    """安全地增加阳光，避免超过上限"""
    MAX_SUN = 1000  # 最大阳光数量
    new_sun = current_sun + amount
    if new_sun > MAX_SUN:
        return MAX_SUN
    return new_sun


def has_zombie_in_row_ahead_with_portal(plant, zombies, portal_manager):
    """检测植物前方是否有僵尸，考虑传送门穿越逻辑 - 排除魅惑僵尸"""
    if not portal_manager:
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        return _has_zombie_in_row_ahead_normal(plant, zombies)

    # 检查传送门左侧是否有僵尸（排除魅惑僵尸）
    has_zombie_before_portal = _has_zombie_between_positions(
        zombies, plant.row, plant.col, nearest_portal.col, exclude_charmed=True
    )

    if has_zombie_before_portal:
        return True

    # 检查其他传送门出口是否有僵尸
    return _has_zombie_at_portal_exits(zombies, portal_manager, nearest_portal, exclude_charmed=True)


def find_nearest_zombie_with_portal(plant, zombies, portal_manager):
    """寻找最近的僵尸，考虑传送门穿越逻辑"""
    if not portal_manager:
        return _find_nearest_zombie_normal(plant, zombies)

    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        return _find_nearest_zombie_normal(plant, zombies)

    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        return _find_nearest_zombie_normal(plant, zombies)

    # 优先攻击传送门左侧的僵尸
    nearest_before_portal = _find_nearest_zombie_between_positions(
        zombies, plant.row, plant.col, nearest_portal.col
    )

    if nearest_before_portal:
        return nearest_before_portal

    # 寻找其他传送门出口的僵尸
    return _find_nearest_zombie_at_portal_exits(zombies, portal_manager, nearest_portal)


def get_bullet_target_col_with_portal(plant, zombies, portal_manager):
    """获取子弹目标列位置，考虑传送门穿越"""
    target_zombie = find_nearest_zombie_with_portal(plant, zombies, portal_manager)

    if target_zombie:
        if _is_zombie_at_portal_exit(target_zombie, plant, portal_manager):
            plant_row_portals = _get_portals_in_row(portal_manager, plant.row)
            nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)
            if nearest_portal:
                return float(nearest_portal.col)

        return target_zombie.col

    return 9.0


def _get_portals_in_row(portal_manager, row):
    """获取指定行的所有活跃传送门"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return []
    return [portal for portal in portal_manager.portals
            if portal.row == row and portal.is_active]


def _find_nearest_portal_to_right(plant, portals):
    """找到植物右侧最近的传送门"""
    nearest_portal = None
    min_distance = float('inf')

    for portal in portals:
        if portal.col > plant.col:
            distance = portal.col - plant.col
            if distance < min_distance:
                min_distance = distance
                nearest_portal = portal

    return nearest_portal


def _has_zombie_in_row_ahead_normal(plant, zombies):
    """普通的前方僵尸检测逻辑 - 排除魅惑僵尸"""
    for zombie in zombies:
        # 跳过魅惑僵尸
        if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
            continue
        if hasattr(zombie, 'team') and zombie.team == "plant":
            continue

        if zombie.row == plant.row and zombie.col > plant.col:
            return True
    return False


def _find_nearest_zombie_normal(plant, zombies):
    """普通的最近僵尸寻找逻辑"""
    nearest_zombie = None
    min_distance = float('inf')

    for zombie in zombies:
        if zombie.row == plant.row and zombie.col > plant.col:
            distance = zombie.col - plant.col
            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

    return nearest_zombie


def _has_zombie_between_positions(zombies, row, start_col, end_col, exclude_charmed=False):
    """检查指定位置范围内是否有僵尸"""
    for zombie in zombies:
        # 如果需要排除魅惑僵尸
        if exclude_charmed:
            if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                continue
            if hasattr(zombie, 'team') and zombie.team == "plant":
                continue

        if (zombie.row == row and start_col < zombie.col < end_col):
            return True
    return False


def _find_nearest_zombie_between_positions(zombies, row, start_col, end_col):
    """寻找指定位置范围内最近的僵尸"""
    nearest_zombie = None
    min_distance = float('inf')

    for zombie in zombies:
        if (zombie.row == row and start_col < zombie.col < end_col):
            distance = zombie.col - start_col
            if distance < min_distance:
                min_distance = distance
                nearest_zombie = zombie

    return nearest_zombie


def _has_zombie_at_portal_exits(zombies, portal_manager, source_portal, exclude_charmed=False):
    """检查其他传送门出口是否有僵尸"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return False

    exit_portals = [portal for portal in portal_manager.portals
                    if (portal.is_active and portal != source_portal)]

    for exit_portal in exit_portals:
        for zombie in zombies:
            # 如果需要排除魅惑僵尸
            if exclude_charmed:
                if hasattr(zombie, 'is_charmed') and zombie.is_charmed:
                    continue
                if hasattr(zombie, 'team') and zombie.team == "plant":
                    continue

            if (zombie.row == exit_portal.row and zombie.col > exit_portal.col):
                return True

    return False


def _is_zombie_at_portal_exit(zombie, plant, portal_manager):
    """检查僵尸是否位于传送门出口"""
    if not portal_manager:
        return False

    plant_row_portals = _get_portals_in_row(portal_manager, plant.row)

    if not plant_row_portals:
        return False

    nearest_portal = _find_nearest_portal_to_right(plant, plant_row_portals)

    if not nearest_portal:
        return False

    exit_portals = [portal for portal in portal_manager.portals
                    if (portal.is_active and portal != nearest_portal)]

    for exit_portal in exit_portals:
        if zombie.row == exit_portal.row:
            return True

    return False


def update_charm_zombie_system(game, sounds=None):
    """
    更新魅惑僵尸系统的所有相关逻辑
    应该在游戏主循环的每帧中调用此函数
    """

    # 1. 处理植物爆炸效果（排除魅惑僵尸）
    handle_plant_explosions(game, sounds)

    # 2. 更新爆炸僵尸状态（支持阵营攻击）
    update_exploding_zombies(game)

    # 3. 处理僵尸之间的战斗（包括冰车僵尸持续伤害）
    handle_zombie_battles(game, sounds)

    # 4. 更新魅惑效果状态（原有逻辑）
    update_charm_effects(game, sounds)

    # 5. 更新黄瓜效果（原有逻辑）
    update_cucumber_effects(game, sounds)