"""
传送带管理器 - 管理第21关的传送带系统
"""
import pygame
import random
from core.constants import *


class ConveyorCard:
    """传送带上的卡牌"""

    def __init__(self, card_type, x, y, card_data):
        self.card_type = card_type
        self.x = x
        self.y = y
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT
        self.card_data = card_data  # 包含cost, color等信息
        self.selected = False
        self.hover = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, speed):
        """更新位置"""
        self.x -= speed

    def is_offscreen(self):
        """检查是否移出屏幕"""
        return self.x + self.width < 0

    def is_visible_in_belt(self, belt_start_x, belt_end_x):
        """检查卡牌是否在传送带区域内可见"""
        # 如果卡牌与传送带区域有任何重叠，就认为可见
        return not (self.x + self.width <= belt_start_x or self.x >= belt_end_x)


class ConveyorBeltManager:
    def __init__(self, level_manager, available_plants):
        self.level_manager = level_manager
        self.all_available_plants = available_plants

        # 建立植物类型与特性ID的映射关系
        self.plant_feature_mapping = {
            'sunflower': None,  # 向日葵默认可用
            'shooter': None,  # 豌豆射手默认可用
            'melon_pult': 'melon_pult_available',
            'cattail': 'cattail_available',
            'wall_nut': 'wall_nut_available',
            'cherry_bomb': 'cherry_bomb_available',
            'cucumber': 'cucumber_available',
            'dandelion': 'dandelion_available',
            'lightning_flower': 'lightning_flower_available',
            'ice_cactus': 'ice_cactus_available',
            'moon_flower': 'moon_flower_available',
            'luker': 'luker_available',
            'psychedelic_pitcher': 'psychedelic_pitcher_available',
            'sun_shroom': 'sun_shroom_available'
        }

        # 根据特性过滤可用植物
        self.available_plants = self._filter_plants_by_features()

        # 传送带位置
        self.belt_y = CARD_Y
        self.belt_height = CARD_HEIGHT
        self.belt_start_x = CARD_START_X
        self.belt_width = 7 * CARD_WIDTH
        self.belt_end_x = self.belt_start_x + self.belt_width

        # 传送带参数
        config = level_manager.get_feature_value("conveyor_belt", {})
        self.belt_speed = config.get("belt_speed", 1.0)  # 提高默认速度
        self.spawn_interval = config.get("card_spawn_interval", 240)  # 生成间隔
        self.max_cards = config.get("max_cards_on_belt", 11)  # 增加最大卡牌数
        self.random_spawn = config.get("random_spawn", True)

        # 卡牌列表
        self.cards_on_belt = []
        self.spawn_timer = 0
        self.selected_card = None

    def _filter_plants_by_features(self):
        """根据特性管理器的配置过滤可用植物"""
        filtered_plants = []

        for plant_info in self.all_available_plants:
            plant_type = plant_info.get("type")

            # 检查植物是否有对应的特性要求
            required_feature = self.plant_feature_mapping.get(plant_type)

            if required_feature is None:
                # 没有特性要求的植物（如向日葵、豌豆射手）默认可用
                # 但需要检查是否有禁用特性
                if plant_type == 'sunflower':
                    # 检查向日葵相关的禁用特性
                    if (self.level_manager.has_special_feature("no_sunflower") or
                            self.level_manager.has_special_feature("sunflower_no_produce")):
                        continue
                filtered_plants.append(plant_info)
            else:
                # 检查是否启用了对应的解锁特性
                if self.level_manager.has_special_feature(required_feature):
                    filtered_plants.append(plant_info)

        return filtered_plants

    def _check_special_plant_restrictions(self, plant_type):
        """检查特殊植物的限制条件"""
        if plant_type == 'sunflower':
            # 检查向日葵相关限制
            if self.level_manager.has_special_feature("no_sunflower"):
                return False
            if self.level_manager.has_special_feature("sunflower_no_produce"):
                # 向日葵停产模式下，可能仍允许在传送带出现但不产阳光
                return True
        return True

    def update_available_plants(self):
        """更新可用植物列表（当特性发生变化时调用）"""
        self.available_plants = self._filter_plants_by_features()

        # 如果当前选中的植物不再可用，清除选择
        if (self.selected_card and
                self.selected_card.card_type not in [p["type"] for p in self.available_plants]):
            self.clear_selection()

    def update(self):
        """更新传送带系统"""
        # 更新所有卡牌的位置
        for card in self.cards_on_belt[:]:  # 使用切片避免在迭代时修改列表
            card.update(self.belt_speed)

            # 移除已经移出屏幕的卡牌
            if card.is_offscreen():
                self.cards_on_belt.remove(card)
                # 如果移除的是选中的卡牌，清除选中状态
                if card == self.selected_card:
                    self.selected_card = None

        # 更新生成计时器
        self.spawn_timer += 1

        # 生成新卡牌
        if (self.spawn_timer >= self.spawn_interval and
                len(self.cards_on_belt) < self.max_cards and
                len(self.available_plants) > 0):  # 确保有可用植物
            self._spawn_new_card()
            self.spawn_timer = 0

    def _spawn_new_card(self):
        """生成新的卡牌到传送带上"""
        if not self.available_plants:
            return

        # 随机选择一个植物类型
        if self.random_spawn:
            card_info = random.choice(self.available_plants)
        else:
            # 按顺序循环选择
            if not hasattr(self, '_next_card_index'):
                self._next_card_index = 0
            card_info = self.available_plants[self._next_card_index]
            self._next_card_index = (self._next_card_index + 1) % len(self.available_plants)

        # 再次检查植物是否符合特殊限制
        if not self._check_special_plant_restrictions(card_info["type"]):
            return

        # 创建新卡牌，从传送带右端开始
        new_card = ConveyorCard(
            card_type=card_info["type"],
            x=self.belt_end_x,
            y=self.belt_y,
            card_data=card_info
        )

        self.cards_on_belt.append(new_card)

    def handle_click(self, mouse_pos, sun=0):
        """处理点击事件 - 传送带模式不检查阳光"""
        x, y = mouse_pos

        for card in self.cards_on_belt:
            # 只有在传送带区域内可见的卡牌才能被点击
            if card.is_visible_in_belt(self.belt_start_x, self.belt_end_x):
                card_rect = card.get_rect()

                # 检查点击是否在卡牌范围内，但要考虑传送带边界
                click_in_card = card_rect.collidepoint(x, y)
                click_in_belt_area = (self.belt_start_x <= x <= self.belt_end_x and
                                      self.belt_y <= y <= self.belt_y + self.belt_height)

                if click_in_card and click_in_belt_area:
                    # 传送带模式：不检查阳光，直接选中禁用植物选择界面
                    self.selected_card = card
                    card.selected = True

                    # 取消其他卡的选中状态
                    for other_card in self.cards_on_belt:
                        if other_card != card:
                            other_card.selected = False

                    return card.card_type

        return None

    def handle_hover(self, mouse_pos):
        """处理悬停效果"""
        x, y = mouse_pos

        # 清除所有悬停状态
        for card in self.cards_on_belt:
            card.hover = False

        # 设置新的悬停状态
        for card in self.cards_on_belt:
            if card.is_visible_in_belt(self.belt_start_x, self.belt_end_x):
                card_rect = card.get_rect()
                hover_in_card = card_rect.collidepoint(x, y)
                hover_in_belt_area = (self.belt_start_x <= x <= self.belt_end_x and
                                      self.belt_y <= y <= self.belt_y + self.belt_height)

                if hover_in_card and hover_in_belt_area:
                    card.hover = True
                    break

    def draw(self, surface, sun, scaled_images, font_small):
        """绘制传送带和卡牌 - 传送带模式不显示阳光限制"""
        # 绘制传送带背景
        belt_rect = pygame.Rect(self.belt_start_x, self.belt_y,
                                self.belt_width, self.belt_height)
        pygame.draw.rect(surface, (30, 30, 30), belt_rect)  # 深灰色背景
        pygame.draw.rect(surface, (100, 100, 100), belt_rect, 3)  # 灰色边框

        # 绘制传送带纹理线条
        for i in range(0, self.belt_width, 20):
            line_x = self.belt_start_x + i
            pygame.draw.line(surface, (50, 50, 50),
                             (line_x, self.belt_y),
                             (line_x, self.belt_y + self.belt_height), 1)

        # 绘制卡牌
        price_font = pygame.font.Font(None, 20)

        for card in self.cards_on_belt:
            if card.is_visible_in_belt(self.belt_start_x, self.belt_end_x):
                card_rect = card.get_rect()

                # 传送带模式：所有卡牌都可用（不检查阳光）
                # 绘制卡牌背景
                if card.selected:
                    card_color = (200, 200, 100)  # 选中时的金色
                elif card.hover:
                    card_color = (150, 150, 150)  # 悬停时的亮灰色
                else:
                    card_color = card.card_data["color"]  # 正常颜色

                # 裁剪绘制区域
                clip_rect = pygame.Rect(
                    max(card.x, self.belt_start_x),
                    card.y,
                    min(card.x + card.width, self.belt_end_x) - max(card.x, self.belt_start_x),
                    card.height
                )

                original_clip = surface.get_clip()
                surface.set_clip(clip_rect)

                # 绘制卡牌
                pygame.draw.rect(surface, card_color, card_rect)
                border_color = (255, 255, 255) if card.selected else (100, 100, 100)
                border_width = 3 if card.selected else 2
                pygame.draw.rect(surface, border_color, card_rect, border_width)

                # 绘制植物图标
                if scaled_images:
                    img_key = self._get_image_key(card.card_type)
                    if img_key and img_key in scaled_images:
                        surface.blit(scaled_images[img_key],
                                     (card.x + 10, card.y + 10))

                surface.set_clip(original_clip)

    def _get_image_key(self, card_type):
        """获取植物图片键"""
        image_map = {
            'sunflower': 'sunflower_60',
            'shooter': 'pea_shooter_60',
            'melon_pult': 'watermelon_60',
            'cattail': 'cattail_60',
            'wall_nut': 'wall_nut_60',
            'cherry_bomb': 'cherry_bomb_60',
            'cucumber': 'cucumber_60',
            'dandelion': 'dandelion_60',
            'lightning_flower': 'lightning_flower_60',
            'ice_cactus': 'ice_cactus_60',
            'moon_flower': 'moon_flower_60',
            'luker': 'luker_60',
            'psychedelic_pitcher': 'psychedelic_pitcher_60',
            'sun_shroom': 'sun_shroom_60'
        }
        return image_map.get(card_type)

    def get_selected_card(self):
        """获取当前选中的卡牌"""
        return self.selected_card

    def remove_selected_card(self):
        """移除已使用的卡牌费"""
        if self.selected_card and self.selected_card in self.cards_on_belt:
            self.cards_on_belt.remove(self.selected_card)
            self.selected_card = None

    def clear_selection(self):
        """清除选择状态"""
        self.selected_card = None
        for card in self.cards_on_belt:
            card.selected = False

    def get_available_plant_types(self):
        """获取当前可用的植物类型列表"""
        return [plant["type"] for plant in self.available_plants]

    def get_save_data(self):
        """获取传送带的保存数据"""
        save_data = {
            "belt_speed": self.belt_speed,
            "spawn_interval": self.spawn_interval,
            "max_cards": self.max_cards,
            "random_spawn": self.random_spawn,
            "spawn_timer": self.spawn_timer,
            "cards_on_belt": [],
            "selected_card_index": None,
            "_next_card_index": getattr(self, '_next_card_index', 0),
            "available_plants": self.available_plants  # 保存过滤后的植物列表
        }

        # 保存传送带上的卡牌
        for i, card in enumerate(self.cards_on_belt):
            card_data = {
                "card_type": card.card_type,
                "x": card.x,
                "y": card.y,
                "selected": card.selected,
                "card_info": {
                    "type": card.card_data["type"],
                    "cost": card.card_data["cost"],
                    "color": card.card_data["color"]
                }
            }
            save_data["cards_on_belt"].append(card_data)

            # 记录选中的卡牌索引
            if card == self.selected_card:
                save_data["selected_card_index"] = i

        return save_data

    def load_save_data(self, save_data):
        """从保存数据恢复传送带状态"""
        if not save_data:
            return

        # 恢复配置参数
        self.belt_speed = save_data.get("belt_speed", 1.0)
        self.spawn_interval = save_data.get("spawn_interval", 120)
        self.max_cards = save_data.get("max_cards", 12)
        self.random_spawn = save_data.get("random_spawn", True)
        self.spawn_timer = save_data.get("spawn_timer", 0)
        self._next_card_index = save_data.get("_next_card_index", 0)

        # 恢复可用植物列表（如果保存了的话）
        if "available_plants" in save_data:
            self.available_plants = save_data["available_plants"]
        else:
            # 如果没有保存，重新过滤
            self.available_plants = self._filter_plants_by_features()

        # 清空现有卡牌
        self.cards_on_belt = []
        self.selected_card = None

        # 恢复传送带上的卡牌
        selected_card_index = save_data.get("selected_card_index")

        for i, card_data in enumerate(save_data.get("cards_on_belt", [])):
            # 重建卡牌对象
            card = ConveyorCard(
                card_type=card_data["card_type"],
                x=card_data["x"],
                y=card_data["y"],
                card_data=card_data["card_info"]
            )
            card.selected = card_data.get("selected", False)

            self.cards_on_belt.append(card)

            # 恢复选中的卡牌引用
            if selected_card_index is not None and i == selected_card_index:
                self.selected_card = card