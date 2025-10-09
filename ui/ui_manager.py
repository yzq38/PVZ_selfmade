"""
UI管理模块 - 处理游戏界面绘制和交互（添加图鉴功能）
"""
import pygame
import math
import random
import sys
import os



from core.constants import *
from animation.effects import AnimationEffects

def draw_grid(surface, grid_bg_img=None):
    """绘制战场网格（使用背景图片或棕色边框）"""
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            x = BATTLEFIELD_LEFT + col * (GRID_SIZE + GRID_GAP)
            y = BATTLEFIELD_TOP + row * (GRID_SIZE + GRID_GAP)

            if grid_bg_img:
                surface.blit(grid_bg_img, (x, y))
            else:
                pygame.draw.rect(surface, BROWN, (x, y, GRID_SIZE, GRID_SIZE), 1)


def draw_progress_bar(surface, level_manager, game_state, wave_mode, font_small):
    """
    重新设计的进度条绘制逻辑
    - 普通模式：每击杀一个僵尸进度增加，达到预定数目时进度条满
    - 波次模式：只在进度条末端显示一个旗帜，第一波开始时旗帜升起
    - 位置：设置按钮左边
    """
    import math
    import pygame

    # 进度条位置和尺寸 - 移动到设置按钮左边
    bar_width = 200
    bar_height = 15
    bar_x = SETTINGS_BUTTON_X - bar_width - 20  # 设置按钮左边，留20像素间距
    bar_y = SETTINGS_BUTTON_Y + (SETTINGS_BUTTON_HEIGHT - bar_height) // 2  # 与设置按钮垂直居中对齐

    # 绘制进度条背景
    bar_bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(surface, (50, 50, 50), bar_bg_rect)
    pygame.draw.rect(surface, WHITE, bar_bg_rect, 2)

    # 计算进度
    if not wave_mode:
        # 普通模式：根据击杀数计算进度
        required_kills = level_manager.max_waves * 5  # 进入波次模式需要的击杀数
        current_kills = game_state.get("zombies_killed", 0)

        if required_kills > 0:
            progress = min(1.0, current_kills / required_kills)  # 进度可以达到100%
        else:
            progress = 0.0
    else:
        # 波次模式：进度条保持满状态
        progress = 1.0

    # 确保进度在合理范围内
    progress = max(0.0, min(progress, 1.0))

    # 绘制绿色进度条
    progress_width = int(bar_width * progress)
    if progress_width > 0:
        progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
        pygame.draw.rect(surface, (0, 200, 0), progress_rect)

    # 绘制箭头（进度头）
    if progress_width > 0:
        arrow_x = bar_x + progress_width
        arrow_y = bar_y + bar_height // 2
        arrow_size = 8

        # 绘制向右的箭头
        arrow_points = [
            (arrow_x, arrow_y),
            (arrow_x + arrow_size, arrow_y - arrow_size // 2),
            (arrow_x + arrow_size, arrow_y + arrow_size // 2)
        ]
        pygame.draw.polygon(surface, (0, 255, 0), arrow_points)
        pygame.draw.polygon(surface, WHITE, arrow_points, 1)

    # 绘制旗帜（只在进度条末端显示一个）
    flag_x = bar_x + bar_width  # 旗帜位置固定在进度条末端
    base_y = bar_y - 25  # 基础Y位置（进度条上方25像素）

    # 确定旗帜状态
    if wave_mode and level_manager.current_wave >= 1:
        # 波次模式且已开始第一波：旗帜升起（突出显示）
        flag_y = base_y - 5  # 上移5像素

        # 添加轻微的上下浮动效果
        time_factor = pygame.time.get_ticks() * 0.005
        float_offset = math.sin(time_factor) * 2  # 2像素的浮动范围
        flag_y += float_offset

        flag_color = (255, 100, 100)  # 亮红色
        pole_color = (150, 75, 75)  # 深红色旗杆
        show_glow = True  # 显示发光效果
    else:
        # 普通模式或波次模式未开始：旗帜正常位置
        flag_y = base_y
        flag_color = (200, 0, 0)  # 暗红色
        pole_color = (100, 0, 0)  # 深红色旗杆
        show_glow = False

    # 绘制旗杆（细线）
    pole_bottom_y = bar_y - 2  # 旗杆底部到进度条顶部2像素
    pygame.draw.line(surface, pole_color, (flag_x, flag_y), (flag_x, pole_bottom_y), 2)

    # 绘制小红旗（三角形）
    flag_size = 8
    flag_points = [
        (flag_x, flag_y),  # 旗杆顶端
        (flag_x + flag_size, flag_y + flag_size // 2),  # 旗帜右端
        (flag_x, flag_y + flag_size)  # 旗帜底端
    ]
    pygame.draw.polygon(surface, flag_color, flag_points)
    pygame.draw.polygon(surface, (0, 0, 0), flag_points, 1)  # 黑色边框

    # 为激活状态的旗帜添加发光效果
    if show_glow:
        # 绘制半透明的发光圈
        glow_surface = pygame.Surface((flag_size * 3, flag_size * 3), pygame.SRCALPHA)
        glow_center = (flag_size * 1.5, flag_size * 1.5)
        glow_color = (255, 255, 100, 50)  # 半透明黄色
        pygame.draw.circle(glow_surface, glow_color, glow_center, flag_size + 3)
        surface.blit(glow_surface, (flag_x - flag_size * 1.5, flag_y - flag_size // 2))

    # 在旗帜下方显示"终点"文字
    end_text = font_small.render("大波", True, WHITE)
    text_x = flag_x - end_text.get_width() // 2
    text_y = bar_y + bar_height + 5  # 进度条下方5像素
    surface.blit(end_text, (text_x - 5, text_y))


def draw_ui(surface, sun, cards, shovel, selected, level_manager, wave_mode=False,
            wave_timer=0, wave_interval=360, show_settings=False, game_state=None,
            level_settings=None, scaled_images=None, font_small=None, font_medium=None, images=None, game_manager=None
            , conveyor_belt_manager=None, seed_rain_manager = None,plant_registry=None):
    """绘制UI：阳光+铲子+卡槽+波次信息+卡牌冷却+阳光不足灰化 - 现在使用植物注册表"""

    # 导入植物注册表（如果未传入参数）
    if plant_registry is None:
        from plants.plant_registry import plant_registry as global_plant_registry
        plant_registry = global_plant_registry

    # 1. 绘制顶部UI背景（深灰）
    pygame.draw.rect(surface, GRAY_DARK, (0, 0, BASE_WIDTH, BATTLEFIELD_TOP))
    # 2. 绘制底部UI背景（深灰）
    bottom_height = BASE_HEIGHT - (BATTLEFIELD_TOP + total_battlefield_height)
    pygame.draw.rect(surface, GRAY_DARK,
                     (0, BATTLEFIELD_TOP + total_battlefield_height, BASE_WIDTH, bottom_height))

    # 3. 显示阳光数量（左上）
    sun_text = font_medium.render(f"阳光: {int(sun)}", True, YELLOW)
    surface.blit(sun_text, (20, 20))
    if hasattr(game_manager, 'coins'):
        coins_text = font_medium.render(f"金币: {game_manager.coins}", True, (255, 215, 0))  # 金色
        surface.blit(coins_text, (20, 55))

    # 4. 显示关卡信息（移动到左下角原来进度条的位置）
    level_name = level_manager.get_level_name()

    # 在左下角显示关卡标题
    title_x = 20
    title_y = BASE_HEIGHT - 65  # 比原来进度条位置稍微上一点

    # 使用较大的字体绘制关卡名称
    name_text = font_medium.render(level_name, True, WHITE)
    surface.blit(name_text, (title_x, title_y))

    # 在关卡名称下方显示向日葵种植限制
    sunflower_status = level_manager.get_sunflower_status_text()
    if sunflower_status:
        status_text = font_small.render(sunflower_status, True, ORANGE)
        surface.blit(status_text, (title_x, title_y + 35))  # 关卡名称下方25像素

        if not level_manager.can_plant_sunflower():
            warning_text = font_small.render("", True, RED)
            surface.blit(warning_text, (title_x, title_y + 45))

    # 5. 绘制进度条（移动到设置按钮左边）
    draw_progress_bar(surface, level_manager, game_state, wave_mode, font_small)

    # 6. 绘制铲子（卡牌左侧）
    shovel_rect = pygame.Rect(SHOVEL_X, SHOVEL_Y, SHOVEL_WIDTH, SHOVEL_HEIGHT)
    if images and images.get('shovel_img'):
        surface.blit(images['shovel_img'], (SHOVEL_X, SHOVEL_Y))
    else:
        pygame.draw.rect(surface, SHOVEL_COLOR, shovel_rect)

    # 选中铲子时画白色边框
    if selected == "shovel":
        pygame.draw.rect(surface, WHITE, shovel_rect, 3)

    # 6.5. 绘制锤子（铲子左侧）
    if hasattr(game_manager, 'shop_manager') and game_manager.shop_manager.has_hammer():
        # 检查锤子是否在冷却中
        hammer_cooldown = game_state.get("hammer_cooldown", 0) if game_state else 0
        is_hammer_ready = hammer_cooldown <= 0

        # 修改：使用和铲子一样的尺寸
        hammer_rect = pygame.Rect(HAMMER_X, HAMMER_Y, SHOVEL_WIDTH, SHOVEL_HEIGHT)

        # 检查锤子是否被选中（跟随鼠标）
        hammer_selected = (selected == "hammer")

        # 绘制锤子背景和图标
        if images and images.get('hammer_img') and is_hammer_ready:
            # 锤子可用时显示正常图像，完全填充按钮
            hammer_img_scaled = pygame.transform.scale(images['hammer_img'], (SHOVEL_WIDTH, SHOVEL_HEIGHT))

            if hammer_selected:
                # 锤子被选中时，原位置显示半透明图像
                hammer_img_alpha = hammer_img_scaled.copy()
                hammer_img_alpha.set_alpha(80)  # 设置为半透明
                surface.blit(hammer_img_alpha, (HAMMER_X, HAMMER_Y))

                # 绘制空槽边框，表示锤子已被拿起
                pygame.draw.rect(surface, (100, 100, 100), hammer_rect, 2)
            else:
                # 锤子未被选中时，正常显示
                surface.blit(hammer_img_scaled, (HAMMER_X, HAMMER_Y))

        elif images and images.get('hammer_img'):
            # 锤子冷却中显示灰色图像，完全填充按钮
            hammer_img_scaled = pygame.transform.scale(images['hammer_img'], (SHOVEL_WIDTH, SHOVEL_HEIGHT))
            hammer_img_gray = hammer_img_scaled.copy()
            hammer_img_gray.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)
            surface.blit(hammer_img_gray, (HAMMER_X, HAMMER_Y))
        else:
            # 没有图像时绘制简单矩形，使用和铲子一样的尺寸
            if hammer_selected:
                # 锤子被选中时，原位置显示半透明矩形
                color = (*HAMMER_COLOR[:3], 80) if is_hammer_ready else (100, 100, 100, 80)
                # 创建半透明表面
                alpha_surface = pygame.Surface((SHOVEL_WIDTH, SHOVEL_HEIGHT), pygame.SRCALPHA)
                alpha_surface.fill(color)
                surface.blit(alpha_surface, (HAMMER_X, HAMMER_Y))
                # 绘制空槽边框
                pygame.draw.rect(surface, (100, 100, 100), hammer_rect, 2)
            else:
                # 锤子未被选中时，正常显示
                color = HAMMER_COLOR if is_hammer_ready else (100, 100, 100)
                pygame.draw.rect(surface, color, hammer_rect)

        # 选中锤子时不在原位置画白色边框（因为锤子已经跟随鼠标）
        if selected == "hammer" and is_hammer_ready:
            pass  # 不在原位置绘制选中边框
        elif selected != "hammer":
            # 未选中时可以绘制悬浮效果等
            pass

        # 显示冷却倒计时
        if hammer_cooldown > 0:
            # 绘制冷却覆盖层
            cooldown_surface = pygame.Surface((SHOVEL_WIDTH, SHOVEL_HEIGHT), pygame.SRCALPHA)
            cooldown_surface.fill((0, 0, 0, 150))  # 半透明黑色
            surface.blit(cooldown_surface, (HAMMER_X, HAMMER_Y))

            # 绘制冷却倒计时
            cooldown_seconds = int(hammer_cooldown / 60) + 1  # 转换为秒，向上取整
            cooldown_text = font_medium.render(str(cooldown_seconds), True, WHITE)
            text_rect = cooldown_text.get_rect(center=(HAMMER_X + SHOVEL_WIDTH // 2, HAMMER_Y + SHOVEL_HEIGHT // 2))
            surface.blit(cooldown_text, text_rect)

    # **关键修复：正确检查传送带特性**
    # 检查当前关卡是否真的启用了传送带特性
    has_conveyor_belt_feature = (level_manager and
                                 level_manager.has_special_feature("conveyor_belt"))
    has_seed_rain_feature = (level_manager and
                                 level_manager.has_special_feature("seed_rain"))

    if has_conveyor_belt_feature and conveyor_belt_manager:
        # 使用传送带模式:绘制传送带而不是传统卡槽
        conveyor_belt_manager.draw(surface, sun, scaled_images, font_small)
    elif has_seed_rain_feature and seed_rain_manager:
        pass
    else:
        # 传统卡槽模式：绘制普通的植物卡片槽

        # 创建卡槽价格专用字体
        price_font = pygame.font.Font(None, 24)

        # 7. 绘制植物卡槽（包含冷却效果和阳光不足灰化） - 使用植物注册表
        card_cooldowns = game_state.get("card_cooldowns", {}) if game_state else {}

        # 检查是否购买了第七卡槽
        base_max_cards = 6  # 基础卡槽数量
        if hasattr(game_manager, 'shop_manager') and game_manager.shop_manager.has_7th_card_slot():
            base_max_cards = 7  # 如果购买了第七卡槽，增加到7个

        max_cards = max(base_max_cards, len(cards))  # 至少显示基础数量的卡槽，如果卡片更多则显示更多

        for i in range(max_cards):
            card_x = CARD_START_X + i * CARD_WIDTH
            card_rect = pygame.Rect(card_x, CARD_Y, CARD_WIDTH, CARD_HEIGHT)

            if images and images.get('card_bg_img'):
                surface.blit(images['card_bg_img'], (card_x, CARD_Y))
            else:
                pygame.draw.rect(surface, (100, 100, 100), card_rect)

            if i < len(cards):
                # 有卡片的槽位 - 使用植物注册表获取信息
                card = cards[i]
                plant_type = card["type"]

                # 检查向日葵是否可用
                card_available = True
                if plant_type == "sunflower" and not level_manager.can_plant_sunflower():
                    card_available = False
                if plant_type == "sunflower" and level_manager.get_sunflower_limit() == 0:
                    card_available = False

                # 检查卡片是否在冷却中 - 使用统一的冷却管理
                is_cooling = False
                cooldown_remaining = 0

                # 检查是否需要冷却（第八关强制启用）
                needs_cooldown = (level_manager.has_card_cooldown() or
                                  (level_settings and level_settings.get("all_card_cooldown", False)) or
                                  level_manager.current_level == 8)

                if needs_cooldown:
                    if plant_type in card_cooldowns:
                        cooldown_remaining = card_cooldowns[plant_type]
                        is_cooling = cooldown_remaining > 0

                # 使用植物注册表获取价格
                plant_cost = plant_registry.get_plant_price(plant_type) if plant_registry else card.get("cost", 0)

                # 检查阳光是否足够
                sun_sufficient = sun >= plant_cost

                # 综合判断卡片是否完全可用（考虑所有条件）
                card_fully_available = card_available and not is_cooling and sun_sufficient

                # 绘制卡片背景
                if images and images.get('card_bg_img'):
                    if card_fully_available:
                        surface.blit(images['card_bg_img'], (card_x, CARD_Y))
                    else:
                        gray_surface = images['card_bg_img'].copy()
                        gray_surface.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)
                        surface.blit(gray_surface, (card_x, CARD_Y))
                else:
                    color = card["color"] if card_fully_available else (100, 100, 100)
                    pygame.draw.rect(surface, color, card_rect)

                # 使用植物注册表获取植物图标
                if scaled_images and plant_registry:
                    plant_img_key = plant_registry.get_plant_icon_key(plant_type)

                    if plant_img_key and plant_img_key in scaled_images:
                        if card_fully_available:
                            surface.blit(scaled_images[plant_img_key], (card_x + 10, CARD_Y + 10))
                        else:
                            # 使用预缓存的灰化图片
                            gray_key = plant_img_key + '_gray'
                            if gray_key in scaled_images:
                                surface.blit(scaled_images[gray_key], (card_x + 10, CARD_Y + 10))
                            else:
                                # 如果没有灰化图片，手动创建灰化效果
                                img = scaled_images[plant_img_key].copy()
                                img.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)
                                surface.blit(img, (card_x + 10, CARD_Y + 10))

                # 选中卡片时画白色边框（但冷却中或阳光不足的不能选中）
                if selected == plant_type and card_fully_available:
                    pygame.draw.rect(surface, WHITE, card_rect, 3)

                # 绘制卡片成本（右下） - 使用植物注册表的价格
                cost_color = WHITE if sun_sufficient else RED  # 阳光不足时成本显示为红色
                cost_text = price_font.render(f"{plant_cost}", True, cost_color)
                surface.blit(cost_text, (card_rect.right - 55, card_rect.bottom - 25))

                # 如果卡片不可用（向日葵限制），显示禁用标识
                if not card_available:
                    pygame.draw.line(surface, RED, card_rect.topleft, card_rect.bottomright, 3)
                    pygame.draw.line(surface, RED, card_rect.topright, card_rect.bottomleft, 3)

                # 绘制冷却效果
                if is_cooling:
                    # 绘制冷却覆盖层
                    cooldown_surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                    cooldown_surface.fill((0, 0, 0, 150))  # 半透明黑色
                    surface.blit(cooldown_surface, (card_x, CARD_Y))

                    # 绘制冷却倒计时
                    cooldown_seconds = int(cooldown_remaining / 60) + 1  # 转换为秒，向上取整
                    cooldown_text = font_medium.render(str(cooldown_seconds), True, WHITE)
                    text_rect = cooldown_text.get_rect(center=(card_x + CARD_WIDTH // 2, CARD_Y + CARD_HEIGHT // 2))
                    surface.blit(cooldown_text, text_rect)
            else:
                pass

    # 8. 绘制设置按钮（右下角）
    settings_rect = pygame.Rect(SETTINGS_BUTTON_X, SETTINGS_BUTTON_Y,
                                SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
    if scaled_images and 'settings_50' in scaled_images:
        surface.blit(scaled_images['settings_50'], (SETTINGS_BUTTON_X, SETTINGS_BUTTON_Y))
    else:
        pygame.draw.rect(surface, (100, 100, 100), settings_rect)
        # 绘制齿轮图标（简单的多边形）
        pygame.draw.circle(surface, WHITE, settings_rect.center, 15, 2)
        for i in range(8):
            angle = i * 45
            rad = math.radians(angle)
            x = settings_rect.centerx + math.cos(rad) * 20
            y = settings_rect.centery + math.sin(rad) * 20
            pygame.draw.line(surface, WHITE, settings_rect.center, (x, y), 2)

    return settings_rect

def show_game_over(surface, game_over_sound_played, font_large, font_medium):
    """显示游戏结束弹窗"""
    # 半透明黑底
    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 弹窗框（深灰+红边框）
    popup = pygame.Rect((BASE_WIDTH - 400) // 2, (BASE_HEIGHT - 250) // 2, 400, 250)
    pygame.draw.rect(surface, GRAY_DARK, popup)
    pygame.draw.rect(surface, RED, popup, 4)

    # 弹窗文字
    title = font_large.render("游戏结束!", True, RED)
    msg = font_medium.render("僵尸吃掉了你的脑子!", True, WHITE)
    surface.blit(title, title.get_rect(centerx=popup.centerx, top=popup.top + 30))
    surface.blit(msg, msg.get_rect(centerx=popup.centerx, top=popup.top + 90))

    # 按钮（重试/退出）
    retry_btn = pygame.Rect(popup.left + 50, popup.top + 150, 150, 50)
    quit_btn = pygame.Rect(popup.left + 200, popup.top + 150, 150, 50)
    pygame.draw.rect(surface, (0, 150, 0), retry_btn)
    pygame.draw.rect(surface, (150, 0, 0), quit_btn)
    # 按钮文字
    retry_text = font_medium.render("再次尝试", True, WHITE)
    quit_text = font_medium.render("返回主页", True, WHITE)
    surface.blit(retry_text, retry_text.get_rect(center=retry_btn.center))
    surface.blit(quit_text, quit_text.get_rect(center=quit_btn.center))

    return retry_btn, quit_btn, game_over_sound_played


def show_settings_menu_with_hotreload(surface, volume, in_game=True, hot_reload_enabled=True,
                                      font_large=None, font_medium=None, font_small=None, state_manager=None):
    """显示设置菜单弹窗，现在包含重新开始按钮（仅游戏内）和返回选关页面按钮"""
    # 弹窗框（调整高度以适应新布局）
    popup_width = 400
    popup_height = 400 if in_game else 300  # 游戏内增加50像素高度
    popup = pygame.Rect((BASE_WIDTH - popup_width) // 2,
                        (BASE_HEIGHT - popup_height) // 2,
                        popup_width, popup_height)
    # 使用更亮的背景色确保突出显示
    pygame.draw.rect(surface, (80, 80, 80), popup)  # 更亮的灰色
    pygame.draw.rect(surface, (100, 150, 255), popup, 4)  # 更亮的蓝色边框

    # 弹窗标题（更亮的白色）
    title = font_large.render("设置", True, (255, 255, 255))
    surface.blit(title, title.get_rect(centerx=popup.centerx, top=popup.top + 20))

    # 重新计算垂直布局 - 所有元素居中分布
    content_start_y = popup.top + 60  # 标题下方开始
    content_height = popup_height - 120  # 减去标题和底部边距

    # 音量调节区域
    volume_y = content_start_y + 10
    volume_text = font_medium.render("音量:", True, (255, 255, 255))
    surface.blit(volume_text, (popup.left + 30, volume_y))

    # 音量滑块背景（更亮）
    slider_bg = pygame.Rect(popup.left + 120, volume_y + 20, 200, 10)
    pygame.draw.rect(surface, (120, 120, 120), slider_bg)  # 更亮的灰色

    # 音量滑块（更亮的蓝色）
    slider_pos = popup.left + 120 + int(volume * 200)
    slider = pygame.Rect(slider_pos - 10, volume_y + 15, 20, 20)
    pygame.draw.rect(surface, (100, 150, 255), slider)

    # 音量百分比
    volume_percent = font_small.render(f"{int(volume * 100)}%", True, (255, 255, 255))
    surface.blit(volume_percent, (popup.right - 60, volume_y + 10))

    # 计算按钮区域的起始位置（音量控件下方）
    buttons_start_y = volume_y + 60
    button_spacing = 15  # 按钮间距
    button_height = 40

    # 计算总的按钮数量和所需高度
    button_count = 4 if in_game else 2  # 游戏内：全屏+重新开始+返回选关+继续/退出，主菜单：全屏+重置+继续/退出
    total_buttons_height = button_count * button_height + (button_count - 1) * button_spacing

    # 在可用空间内居中
    available_space = popup.bottom - 60 - buttons_start_y  # 底部留60像素给继续/退出按钮
    buttons_center_y = buttons_start_y + (available_space - total_buttons_height) // 2

    current_y = buttons_center_y

    # 全屏切换按钮
    fullscreen_btn = pygame.Rect(popup.left + 75, current_y, 250, button_height)
    is_fullscreen_hovered = state_manager and state_manager.is_button_hovered("fullscreen", "settings")
    fullscreen_color = get_button_color((150, 150, 255), is_fullscreen_hovered)

    pygame.draw.rect(surface, fullscreen_color, fullscreen_btn)
    fullscreen_text = font_medium.render("切换全屏", True, (255, 255, 255))
    surface.blit(fullscreen_text, fullscreen_text.get_rect(center=fullscreen_btn.center))

    current_y += button_height + button_spacing

    # 重置进度按钮（只在主菜单设置中显示）
    reset_btn = None
    if not in_game:
        reset_btn = pygame.Rect(popup.left + 75, current_y, 250, button_height)
        is_reset_hovered = state_manager and state_manager.is_button_hovered("reset", "settings")
        reset_color = get_button_color((255, 100, 100), is_reset_hovered)

        pygame.draw.rect(surface, reset_color, reset_btn)
        reset_text = font_medium.render("重置关卡进度", True, (255, 255, 255))
        surface.blit(reset_text, reset_text.get_rect(center=reset_btn.center))

        current_y += button_height + button_spacing

    # 重新开始按钮（只在游戏内显示）
    restart_game_btn = None
    if in_game:
        restart_game_btn = pygame.Rect(popup.left + 75, current_y, 250, button_height)
        is_restart_hovered = state_manager and state_manager.is_button_hovered("restart_game", "settings")
        restart_color = get_button_color((255, 150, 50), is_restart_hovered)

        pygame.draw.rect(surface, restart_color, restart_game_btn)
        pygame.draw.rect(surface, (255, 255, 255), restart_game_btn, 2)
        restart_text = font_medium.render("重新开始关卡", True, (255, 255, 255))
        surface.blit(restart_text, restart_text.get_rect(center=restart_game_btn.center))

        current_y += button_height + button_spacing

    # 新增：返回选关页面按钮（只在游戏内显示）
    return_to_level_select_btn = None
    if in_game:
        return_to_level_select_btn = pygame.Rect(popup.left + 75, current_y, 250, button_height)
        is_level_select_hovered = state_manager and state_manager.is_button_hovered("return_level_select", "settings")
        level_select_color = get_button_color((100, 150, 255), is_level_select_hovered)

        pygame.draw.rect(surface, level_select_color, return_to_level_select_btn)
        pygame.draw.rect(surface, (255, 255, 255), return_to_level_select_btn, 2)
        level_select_text = font_medium.render("返回选关页面", True, (255, 255, 255))
        surface.blit(level_select_text, level_select_text.get_rect(center=return_to_level_select_btn.center))

    # 继续/返回主页按钮 - 放在弹窗底部
    bottom_buttons_y = popup.bottom - 55
    continue_btn = pygame.Rect(popup.left + 50, bottom_buttons_y, 140, 35)
    quit_btn = pygame.Rect(popup.left + 210, bottom_buttons_y, 140, 35)

    # 按钮悬浮检测
    is_continue_hovered = state_manager and state_manager.is_button_hovered("continue", "settings")
    is_quit_hovered = state_manager and state_manager.is_button_hovered("quit", "settings")

    continue_color = get_button_color((0, 200, 0), is_continue_hovered)
    quit_color = get_button_color((200, 0, 0), is_quit_hovered)

    # 绘制按钮
    pygame.draw.rect(surface, continue_color, continue_btn)
    pygame.draw.rect(surface, quit_color, quit_btn)

    # 按钮文字
    continue_text = font_medium.render("继续", True, (255, 255, 255))
    quit_text = font_medium.render("返回主页" if in_game else "退出", True, (255, 255, 255))
    surface.blit(continue_text, continue_text.get_rect(center=continue_btn.center))
    surface.blit(quit_text, quit_text.get_rect(center=quit_btn.center))

    return continue_btn, quit_btn, slider_bg, slider, fullscreen_btn, reset_btn, restart_game_btn, return_to_level_select_btn


def ease_out_cubic(t):
    """缓动函数：三次方缓出效果，开始快结束慢阳光向日葵"""
    return 1 - pow(1 - t, 3)


def ease_in_cubic(t):
    """缓动函数：三次方缓入效果，开始慢结束快"""
    return t * t * t


def ease_out_quart(t):
    """缓动函数：四次方缓出效果，减速更明显"""
    return 1 - pow(1 - t, 4)


def draw_main_menu(surface, animation_timer, exit_animation=False, has_saved_game=False, menu_bg_img=None,
                   font_medium=None, state_manager=None, font_tiny=None):
    """主菜单绘制函数 - 支持退出动画，添加图鉴按钮"""
    if font_tiny is None:
        font_tiny = pygame.font.Font(None, 20)
        # 1. 先绘制背景
    if menu_bg_img:
        surface.blit(menu_bg_img, (0, 0))
    else:
        surface.fill((0, 100, 0))

    # 2. 右侧菜单区域设置
    menu_width = 250
    menu_x = BASE_WIDTH - menu_width - 50
    menu_y = 150

    # 3. 动画参数
    stagger_delay = 15
    button_animation_duration = 30

    # 按钮标签
    button_labels = ["主线模式", "挑战模式", "无尽模式", "设置"]
    base_button_color = GRAY  # 确保这是一个颜色元组，如 (128, 128, 128)
    base_border_color = DARK_BLUE

    buttons = []

    if exit_animation:
        # 退出动画：按钮从当前位置右移出屏幕
        exit_duration = 60
        for i, label in enumerate(button_labels):
            # 每个按钮的退出时间错开
            button_exit_start = i * 10  # 每个按钮延迟10帧开始退出
            button_exit_time = max(0, animation_timer - button_exit_start)

            if button_exit_time > 0:
                # 计算退出进度
                exit_progress = min(1.0, button_exit_time / (exit_duration - button_exit_start))
                eased_exit_progress = ease_in_cubic(exit_progress)  # 加速退出

                # 按钮位置：从正常位置移动到屏幕右侧外
                start_x = menu_x
                end_x = BASE_WIDTH + 100  # 移出屏幕右侧
                current_x = start_x + (end_x - start_x) * eased_exit_progress

                # 透明度逐渐减少
                alpha = int(255 * (1 - exit_progress))
            else:
                # 还没开始退出，保持原位置
                current_x = menu_x
                alpha = 255

            btn_y = menu_y + i * 70
            btn_rect = pygame.Rect(current_x, btn_y, menu_width, 50)

            if alpha > 0:  # 只有在可见时才绘制
                # 创建带透明度的表面
                button_surface = pygame.Surface((menu_width, 50), pygame.SRCALPHA)

                # 修复：直接使用 base_button_color，不进行索引操作
                button_color = (*base_button_color, alpha)
                border_color = (*DARK_BLUE, alpha)

                pygame.draw.rect(button_surface, button_color, (0, 0, menu_width, 50))
                pygame.draw.rect(button_surface, border_color, (0, 0, menu_width, 50), 3)

                # 绘制按钮文字
                btn_text = font_medium.render(label, True, WHITE)
                text_surface = pygame.Surface(btn_text.get_size(), pygame.SRCALPHA)
                text_surface.blit(btn_text, (0, 0))
                text_surface.set_alpha(alpha)

                button_surface.blit(text_surface,
                                    (menu_width // 2 - btn_text.get_width() // 2,
                                     25 - btn_text.get_height() // 2))

                surface.blit(button_surface, (current_x, btn_y))


    else:
        # 入场动画：按钮从右侧滑入
        for i, label in enumerate(button_labels):
            # 计算当前按钮的动画进度
            button_start_time = i * stagger_delay
            button_current_time = max(0, animation_timer - button_start_time)
            progress = min(1.0, button_current_time / button_animation_duration)
            eased_progress = ease_out_cubic(progress) if progress > 0 else 0

            # 计算按钮位置
            start_x = BASE_WIDTH + 50
            end_x = menu_x
            current_x = start_x + (end_x - start_x) * eased_progress
            alpha = int(255 * eased_progress)

            # 检查是否悬浮
            is_hovered = state_manager and state_manager.is_button_hovered(i, "main_menu")

            # 修复：直接使用 base_button_color，不进行索引操作
            base_color = base_button_color

            # 计算按钮颜色
            button_color = get_button_color((*base_color, alpha), is_hovered)
            border_color = get_button_color((*base_border_color, alpha), is_hovered)

            btn_y = menu_y + i * 70
            btn_rect = pygame.Rect(current_x, btn_y, menu_width, 50)

            if button_current_time > 0 and progress > 0:
                # 创建带透明度的表面
                button_surface = pygame.Surface((menu_width, 50), pygame.SRCALPHA)

                pygame.draw.rect(button_surface, button_color, (0, 0, menu_width, 50))
                pygame.draw.rect(button_surface, border_color, (0, 0, menu_width, 50), 3)

                # 绘制按钮文字
                btn_text = font_medium.render(label, True, WHITE)
                text_surface = pygame.Surface(btn_text.get_size(), pygame.SRCALPHA)
                text_surface.blit(btn_text, (0, 0))
                text_surface.set_alpha(alpha)

                button_surface.blit(text_surface,
                                    (menu_width // 2 - btn_text.get_width() // 2,
                                     25 - btn_text.get_height() // 2))

                surface.blit(button_surface, (current_x, btn_y))

                if progress > 0:  # 只要按钮开始显示就能点击
                    buttons.append((btn_rect, label))

    # 绘制左侧图鉴按钮（新增）
    codex_button_size = CODEX_BUTTON_SIZE
    codex_x = CODEX_BUTTON_X
    codex_y = CODEX_BUTTON_Y
    codex_btn_rect = pygame.Rect(codex_x, codex_y, codex_button_size, codex_button_size)

    # 检查图鉴按钮是否悬浮
    is_codex_hovered = state_manager and state_manager.is_button_hovered("codex", "main_menu")

    # 计算图鉴按钮的动画效果（复用现有动画逻辑）
    if exit_animation:
        # 退出动画：图鉴按钮向左滑出屏幕
        codex_alpha = int(255 * (1 - min(1.0, animation_timer / 60)))
        codex_current_x = codex_x - int((codex_x + 100) * min(1.0, animation_timer / 60))  # 修改：向左滑出
    else:
        # 入场动画：图鉴按钮从左侧滑入
        progress = min(1.0, animation_timer / 60) if animation_timer > 0 else 0
        eased_progress = ease_out_cubic(progress) if progress > 0 else 0
        codex_alpha = int(255 * eased_progress)
        codex_current_x = -100 + int((codex_x + 100) * eased_progress)

    # 只在可见时绘制图鉴按钮
    if codex_alpha > 0:
        # 创建图鉴按钮表面
        codex_surface = pygame.Surface((codex_button_size, codex_button_size), pygame.SRCALPHA)

        # 设置图鉴按钮颜色（悬浮时变亮）
        base_codex_color = (120, 80, 200)  # 紫色基调
        if is_codex_hovered:
            codex_color = tuple(min(255, c + 30) for c in base_codex_color)
        else:
            codex_color = base_codex_color

        # 绘制图鉴按钮背景
        pygame.draw.rect(codex_surface, (*codex_color, codex_alpha), (0, 0, codex_button_size, codex_button_size))
        pygame.draw.rect(codex_surface, (*DARK_BLUE, codex_alpha), (0, 0, codex_button_size, codex_button_size), 3)

        # 绘制图鉴图标（书本图标）
        icon_size = codex_button_size - 20
        icon_x = 10
        icon_y = 10

        # 书本主体
        book_rect = (icon_x + 15, icon_y + 15, icon_size - 30, icon_size - 25)
        pygame.draw.rect(codex_surface, (255, 255, 255, codex_alpha), book_rect)

        # 书脊
        spine_rect = (icon_x + 12, icon_y + 15, 6, icon_size - 25)
        pygame.draw.rect(codex_surface, (200, 200, 200, codex_alpha), spine_rect)

        # 书页线条
        for i in range(3):
            line_y = icon_y + 25 + i * 8
            pygame.draw.line(codex_surface, (150, 150, 150, codex_alpha),
                             (icon_x + 20, line_y), (icon_x + icon_size - 20, line_y), 1)

        # 图鉴文字
        codex_text = font_tiny.render("图鉴", True, (255, 255, 255, codex_alpha))
        text_rect = codex_text.get_rect(center=(codex_button_size // 2, codex_button_size - 15))
        codex_surface.blit(codex_text, text_rect)

        # 绘制到主表面
        surface.blit(codex_surface, (codex_current_x, codex_y))

        # 如果按钮可见且动画完成，添加到可点击按钮列表
        if not exit_animation and progress > 0.8:  # 动画接近完成时才可点击查看
            adjusted_codex_rect = pygame.Rect(codex_current_x, codex_y, codex_button_size, codex_button_size)
            buttons.append((adjusted_codex_rect, "图鉴"))

    # 绘制左侧正方形商店按钮
    shop_button_size = 80  # 正方形边长
    shop_x = 100  # 左侧位置
    shop_y = BASE_HEIGHT // 2 + 50  # 中间偏下
    shop_btn_rect = pygame.Rect(shop_x, shop_y, shop_button_size, shop_button_size)

    # 检查商店按钮是否悬浮
    is_shop_hovered = state_manager and state_manager.is_button_hovered("shop", "main_menu")

    # 计算商店按钮的动画效果（复用现有动画逻辑）
    if exit_animation:
        # 退出动画：商店按钮向左滑出屏幕
        shop_alpha = int(255 * (1 - min(1.0, animation_timer / 60)))
        shop_current_x = shop_x - int((shop_x + 100) * min(1.0, animation_timer / 60))  # 修改：向左滑出
    else:
        # 入场动画：商店按钮从左侧滑入
        progress = min(1.0, animation_timer / 60) if animation_timer > 0 else 0
        eased_progress = ease_out_cubic(progress) if progress > 0 else 0
        shop_alpha = int(255 * eased_progress)
        shop_current_x = -100 + int((shop_x + 100) * eased_progress)

    # 只在可见时绘制商店按钮
    if shop_alpha > 0:
        # 创建商店按钮表面
        shop_surface = pygame.Surface((shop_button_size, shop_button_size), pygame.SRCALPHA)

        # 设置商店按钮颜色（悬浮时变亮）
        base_shop_color = (80, 150, 200)  # 蓝色基调
        if is_shop_hovered:
            shop_color = tuple(min(255, c + 30) for c in base_shop_color)
        else:
            shop_color = base_shop_color

        # 绘制商店按钮背景
        pygame.draw.rect(shop_surface, (*shop_color, shop_alpha), (0, 0, shop_button_size, shop_button_size))
        pygame.draw.rect(shop_surface, (*DARK_BLUE, shop_alpha), (0, 0, shop_button_size, shop_button_size), 3)

        # 绘制商店图标（简单的购物袋图标）
        icon_size = shop_button_size - 20
        icon_x = 10
        icon_y = 10

        # 购物袋主体
        bag_rect = (icon_x + 15, icon_y + 20, icon_size - 30, icon_size - 30)
        pygame.draw.rect(shop_surface, (255, 255, 255, shop_alpha), bag_rect)

        # 购物袋把手
        handle_width = 20
        handle_x = icon_x + (icon_size - handle_width) // 2
        handle_y = icon_y + 5
        pygame.draw.arc(shop_surface, (255, 255, 255, shop_alpha),
                        (handle_x, handle_y, handle_width, 20), 0, 3.14, 3)

        # 商店文字
        shop_text = font_tiny.render("商店", True, (255, 255, 255, shop_alpha))
        text_rect = shop_text.get_rect(center=(shop_button_size // 2, shop_button_size - 15))
        shop_surface.blit(shop_text, text_rect)

        # 绘制到主表面
        surface.blit(shop_surface, (shop_current_x, shop_y))

        # 如果按钮可见且动画完成，添加到可点击按钮列表
        if not exit_animation and progress > 0.8:  # 动画接近完成时才可点击
            adjusted_shop_rect = pygame.Rect(shop_current_x, shop_y, shop_button_size, shop_button_size)
            buttons.append((adjusted_shop_rect, "商店"))

    return buttons


def draw_codex_page(surface, animation_timer, animation_complete, exit_animation, exit_timer,
                    font_large, font_medium, state_manager=None):
    """绘制图鉴页面 - 支持入场和退出动画，包含植物和僵尸两个大按钮"""

    # 计算页面偏移（图鉴从右侧滑入和滑出）
    if exit_animation:
        # 退出动画：从当前位置向右滑出屏幕
        exit_duration = 60
        progress = min(1.0, exit_timer / exit_duration)
        eased_progress = ease_in_cubic(progress)  # 加速退出

        page_start_x = 0  # 当前位置
        page_end_x = BASE_WIDTH  # 滑出到右侧屏幕外
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)
    else:
        # 入场动画：从右侧滑入
        animation_duration = 80
        progress = min(1.0, animation_timer / animation_duration) if not animation_complete else 1.0
        eased_progress = ease_out_quart(progress)

        page_start_x = BASE_WIDTH  # 从右侧屏幕外开始
        page_end_x = 0  # 最终位置
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)

    # 创建临时表面来绘制整个图鉴界面
    codex_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)

    # 绘制背景（深蓝紫色渐变）
    for y in range(BASE_HEIGHT):
        ratio = y / BASE_HEIGHT
        r = int(20 + (40 - 20) * ratio)
        g = int(30 + (60 - 30) * ratio)
        b = int(80 + (120 - 80) * ratio)
        pygame.draw.line(codex_surface, (r, g, b), (0, y), (BASE_WIDTH, y))

    # 绘制返回按钮
    back_btn = pygame.Rect(20, 20, 100, 40)
    pygame.draw.rect(codex_surface, RED, back_btn)
    back_text = font_medium.render("返回", True, WHITE)
    codex_surface.blit(back_text, (back_btn.centerx - back_text.get_width() // 2,
                                   back_btn.centery - back_text.get_height() // 2))

    # 绘制标题
    title = font_large.render("游戏图鉴", True, (255, 255, 255))
    title_x = (BASE_WIDTH - title.get_width()) // 2
    title_y = 30
    codex_surface.blit(title, (title_x, title_y))

    # 计算两个大按钮的位置和尺寸
    button_width = 320
    button_height = 400
    button_spacing = 60

    # 计算总宽度并居中
    total_width = 2 * button_width + button_spacing
    start_x = (BASE_WIDTH - total_width) // 2
    start_y = 120

    # 植物按钮（左侧）
    plant_btn = pygame.Rect(start_x, start_y, button_width, button_height)
    is_plant_hovered = state_manager and state_manager.is_button_hovered("plants", "codex")

    plant_color = (100, 180, 100) if not is_plant_hovered else (120, 200, 120)
    pygame.draw.rect(codex_surface, plant_color, plant_btn)
    pygame.draw.rect(codex_surface, (255, 255, 255), plant_btn, 4)

    # 植物按钮图标区域（上半部分）
    icon_area_height = button_height * 2 // 3
    plant_icon_area = pygame.Rect(plant_btn.x + 20, plant_btn.y + 20,
                                  button_width - 40, icon_area_height - 40)
    pygame.draw.rect(codex_surface, (80, 150, 80), plant_icon_area)

    # 绘制植物图标（简单的花朵图案）
    center_x = plant_icon_area.centerx
    center_y = plant_icon_area.centery - 20

    # 花瓣
    petal_size = 30
    for angle in range(0, 360, 72):  # 5个花瓣
        rad = math.radians(angle)
        petal_x = center_x + math.cos(rad) * 40
        petal_y = center_y + math.sin(rad) * 40
        pygame.draw.circle(codex_surface, (255, 100, 100), (int(petal_x), int(petal_y)), petal_size)

    # 花芯
    pygame.draw.circle(codex_surface, (255, 255, 100), (center_x, center_y), 25)

    # 植物按钮文字
    plant_title = font_large.render("植物图鉴", True, WHITE)
    plant_text_y = plant_btn.bottom - 80
    codex_surface.blit(plant_title, (plant_btn.centerx - plant_title.get_width() // 2, plant_text_y))

    # 僵尸按钮（右侧）
    zombie_btn = pygame.Rect(start_x + button_width + button_spacing, start_y, button_width, button_height)
    is_zombie_hovered = state_manager and state_manager.is_button_hovered("zombies", "codex")

    zombie_color = (180, 100, 100) if not is_zombie_hovered else (200, 120, 120)
    pygame.draw.rect(codex_surface, zombie_color, zombie_btn)
    pygame.draw.rect(codex_surface, (255, 255, 255), zombie_btn, 4)

    # 僵尸按钮图标区域
    zombie_icon_area = pygame.Rect(zombie_btn.x + 20, zombie_btn.y + 20,
                                   button_width - 40, icon_area_height - 40)
    pygame.draw.rect(codex_surface, (150, 80, 80), zombie_icon_area)

    # 绘制僵尸图标（简单的骷髅头图案）
    skull_center_x = zombie_icon_area.centerx
    skull_center_y = zombie_icon_area.centery - 20

    # 头骨
    pygame.draw.circle(codex_surface, (220, 220, 220), (skull_center_x, skull_center_y), 50)

    # 眼窟
    eye_size = 15
    pygame.draw.circle(codex_surface, (0, 0, 0), (skull_center_x - 25, skull_center_y - 15), eye_size)
    pygame.draw.circle(codex_surface, (0, 0, 0), (skull_center_x + 25, skull_center_y - 15), eye_size)

    # 鼻子
    nose_points = [
        (skull_center_x, skull_center_y + 5),
        (skull_center_x - 8, skull_center_y + 20),
        (skull_center_x + 8, skull_center_y + 20)
    ]
    pygame.draw.polygon(codex_surface, (0, 0, 0), nose_points)

    # 嘴巴
    mouth_rect = pygame.Rect(skull_center_x - 20, skull_center_y + 25, 40, 15)
    pygame.draw.rect(codex_surface, (0, 0, 0), mouth_rect)

    # 僵尸按钮文字
    zombie_title = font_large.render("僵尸图鉴", True, WHITE)
    zombie_text_y = zombie_btn.bottom - 80
    codex_surface.blit(zombie_title, (zombie_btn.centerx - zombie_title.get_width() // 2, zombie_text_y))


    # 将整个图鉴表面绘制到主表面，应用水平偏移
    surface.blit(codex_surface, (page_offset_x, 0))

    # 调整按钮位置（考虑页面偏移）
    adjusted_back_btn = pygame.Rect(back_btn.x + page_offset_x, back_btn.y, back_btn.width, back_btn.height)
    adjusted_plant_btn = pygame.Rect(plant_btn.x + page_offset_x, plant_btn.y, plant_btn.width, plant_btn.height)
    adjusted_zombie_btn = pygame.Rect(zombie_btn.x + page_offset_x, zombie_btn.y, zombie_btn.width, zombie_btn.height)

    return adjusted_back_btn, adjusted_plant_btn, adjusted_zombie_btn


def draw_level_select(surface, game_db, level_settings=None, menu_bg_img=None,
                      font_medium=None, font_small=None, settings_img=None,
                      animation_timer=0, animation_complete=False, exit_animation=False, exit_timer=0, hover_pos=None,
                      hover_level=None, state_manager=None):
    """绘制选关界面 - 支持入场和退出动画，新增关卡解锁系统"""

    # 绘制背景
    if menu_bg_img:
        surface.blit(menu_bg_img, (0, 0))
    else:
        surface.fill((0, 100, 0))

    # 计算页面偏移
    if exit_animation:
        # 退出动画：从当前位置向左滑出屏幕
        exit_duration = 60
        progress = min(1.0, exit_timer / exit_duration)
        eased_progress = ease_in_cubic(progress)  # 加速退出

        page_start_x = 0  # 当前位置
        page_end_x = -BASE_WIDTH  # 滑出到左侧屏幕外
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)
    else:
        # 入场动画：从左侧滑入
        animation_duration = 80
        progress = min(1.0, animation_timer / animation_duration) if not animation_complete else 1.0
        eased_progress = ease_out_quart(progress)

        page_start_x = -BASE_WIDTH  # 从左侧屏幕外开始
        page_end_x = 0  # 最终位置
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)

    # 创建临时表面来绘制整个选关界面
    level_select_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)

    # 绘制返回按钮
    back_btn = pygame.Rect(20, 20, 100, 40)
    pygame.draw.rect(level_select_surface, RED, back_btn)
    back_text = font_small.render("返回", True, WHITE)
    level_select_surface.blit(back_text, (back_btn.centerx - back_text.get_width() // 2,
                                          back_btn.centery - back_text.get_height() // 2))

    # 绘制统计信息
    completed_count = game_db.get_completion_count()
    stats_text = font_medium.render(f"已通关: {completed_count}/28", True, WHITE)
    level_select_surface.blit(stats_text, (BASE_WIDTH - stats_text.get_width() - 20, 30))

    # 获取已通关的关卡列表
    completed_levels = game_db.get_completed_levels()

    # 计算下一个可玩关卡（最高通关关卡+1，但不超过28）
    if completed_levels:
        next_playable_level = max(completed_levels) + 1
        if next_playable_level > 28:
            next_playable_level = None  # 所有关卡都已通关
    else:
        next_playable_level = 1  # 如果没有通关任何关卡，第1关可玩

    # 绘制关卡网格 (4x7)
    level_buttons = []
    grid_width = 7
    grid_height = 4
    level_size = 80
    level_spacing = 20
    grid_start_x = (BASE_WIDTH - (grid_width * (level_size + level_spacing) - level_spacing)) // 2
    grid_start_y = 100

    for row in range(grid_height):
        for col in range(grid_width):
            level_num = row * grid_width + col + 1
            if level_num > 28:  # 最多28关
                break

            level_x = grid_start_x + col * (level_size + level_spacing)
            level_y = grid_start_y + row * (level_size + level_spacing)
            level_rect = pygame.Rect(level_x, level_y, level_size, level_size)

            # 检查关卡状态
            is_completed = level_num in completed_levels
            is_next_playable = (level_num == next_playable_level)
            is_locked = not is_completed and not is_next_playable
            is_hovered = (hover_level == level_num)

            # 确定按钮颜色
            if is_completed:
                # 已通关关卡：绿色
                button_color = (100, 255, 100)
                if is_hovered:
                    button_color = (120, 255, 120)  # 悬浮时更亮的绿色
            elif is_next_playable:
                # 下一个可玩关卡：蓝色
                button_color = LIGHT_BLUE
                if is_hovered:
                    button_color = (120, 170, 255)  # 悬浮时更亮的蓝色
            else:
                # 未解锁关卡：灰色
                button_color = (100, 100, 100)
                if is_hovered:
                    button_color = (120, 120, 120)  # 悬浮时稍亮的灰色

            # 绘制关卡按钮
            pygame.draw.rect(level_select_surface, button_color, level_rect)

            # 边框颜色也根据状态调整
            if is_locked:
                border_color = (80, 80, 80)  # 锁定状态用深灰色边框
            else:
                border_color = DARK_BLUE

            pygame.draw.rect(level_select_surface, border_color, level_rect, 3)

            # 悬浮时添加发光边框（但锁定状态不发光）
            if is_hovered and not is_locked:
                glow_color = (255, 255, 255, 100)  # 半透明白色
                glow_surface = pygame.Surface((level_size + 8, level_size + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, glow_color, (0, 0, level_size + 8, level_size + 8), 4)
                level_select_surface.blit(glow_surface, (level_x - 4, level_y - 4))

            # 绘制关卡数字
            text_color = WHITE if not is_locked else (150, 150, 150)  # 锁定状态用灰色文字
            level_text = font_medium.render(str(level_num), True, text_color)
            level_select_surface.blit(level_text, (level_rect.centerx - level_text.get_width() // 2,
                                                   level_rect.centery - level_text.get_height() // 2))

            # 如果已通关，在右上角绘制红色三角形
            if is_completed:
                triangle_points = [
                    (level_rect.right - 20, level_rect.top),
                    (level_rect.right, level_rect.top),
                    (level_rect.right, level_rect.top + 20)
                ]
                pygame.draw.polygon(level_select_surface, RED, triangle_points)

            # 如果是锁定状态，绘制锁定图标
            if is_locked:
                # 绘制简单的锁定图标
                lock_size = 20
                lock_x = level_rect.centerx - lock_size // 2
                lock_y = level_rect.centery + 15

                # 锁身（矩形）
                lock_body = pygame.Rect(lock_x + 4, lock_y + 6, lock_size - 8, lock_size - 10)
                pygame.draw.rect(level_select_surface, (80, 80, 80), lock_body)

                # 锁环（圆弧）
                lock_ring_rect = pygame.Rect(lock_x + 6, lock_y, lock_size - 12, lock_size - 8)
                pygame.draw.arc(level_select_surface, (80, 80, 80), lock_ring_rect, 0, 3.14, 3)

            # 调整按钮矩形位置（考虑页面偏移）
            adjusted_level_rect = pygame.Rect(level_x + page_offset_x, level_y, level_size, level_size)

            # 只有非锁定状态的关卡才能点击
            if not is_locked:
                level_buttons.append((adjusted_level_rect, level_num))

    # 将整个临时表面绘制到主表面，应用水平偏移
    surface.blit(level_select_surface, (page_offset_x, 0))

    # 绘制工具提示（悬浮时显示关卡名称）
    if hover_level and hover_pos and not exit_animation:
        # 根据关卡状态显示不同的提示信息
        completed_levels = game_db.get_completed_levels()
        is_completed = hover_level in completed_levels
        is_next_playable = (hover_level == next_playable_level)
        is_locked = not is_completed and not is_next_playable

        if is_locked:
            # 锁定关卡显示解锁提示
            draw_level_tooltip(surface, hover_level, hover_pos, font_small, game_db, "locked")
        else:
            draw_level_tooltip(surface, hover_level, hover_pos, font_small, game_db, "unlocked")

    # 调整返回按钮的位置
    adjusted_back_btn = pygame.Rect(back_btn.x + page_offset_x, back_btn.y, back_btn.width, back_btn.height)

    return adjusted_back_btn, level_buttons


def draw_level_tooltip(surface, level_num, mouse_pos, font_small, game_db, status):
    """绘制带状态的关卡工具提示"""
    # 添加类型检查，防止传入错误的参数类型
    if not isinstance(mouse_pos, (tuple, list)) or len(mouse_pos) != 2:
        return  # 直接返回，不绘制提示

    # 获取关卡名称（需要创建临时关卡管理器获取配置）
    from core.level_manager import LevelManager
    temp_level_manager = LevelManager("database/levels.json")
    temp_level_manager.start_level(level_num)
    level_name = temp_level_manager.get_level_name()

    # 获取通关状态
    is_completed = game_db.is_level_completed(level_num)

    # 根据状态组合显示文本
    if status == "locked":
        tooltip_text = f"{level_name} (已锁定)"
        text_color = (200, 200, 200)  # 灰色文字
    else:
        status_text = "已通关" if is_completed else "可挑战"
        tooltip_text = f"{level_name} "
        text_color = (100, 255, 100) if is_completed else WHITE

    # 创建工具提示表面
    text_surface = font_small.render(tooltip_text, True, text_color)
    tooltip_width = text_surface.get_width() + 20
    tooltip_height = text_surface.get_height() + 10

    # 计算工具提示位置（鼠标右下方，但不超出屏幕）
    mouse_x, mouse_y = mouse_pos
    tooltip_x = mouse_x + 15
    tooltip_y = mouse_y + 15

    # 防止超出屏幕边界
    if tooltip_x + tooltip_width > BASE_WIDTH:
        tooltip_x = mouse_x - tooltip_width - 5
    if tooltip_y + tooltip_height > BASE_HEIGHT:
        tooltip_y = mouse_y - tooltip_height - 5

    # 绘制工具提示背景
    tooltip_bg = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
    if status == "locked":
        tooltip_bg.fill((60, 60, 60, 240))  # 深灰色背景表示锁定
        border_color = (100, 100, 100)
    else:
        tooltip_bg.fill((50, 50, 50, 240))  # 半透明深灰色
        border_color = (200, 200, 200)

    pygame.draw.rect(tooltip_bg, border_color, (0, 0, tooltip_width, tooltip_height), 1)

    surface.blit(tooltip_bg, (tooltip_x, tooltip_y))
    surface.blit(text_surface, (tooltip_x + 10, tooltip_y + 5))


def draw_continue_dialog(surface, saved_game_info, level_num, font_large=None, font_medium=None, font_small=None):
    """绘制继续游戏对话框，现在包含返回按钮"""
    # 半透明背景
    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 对话框 - 调整高度以容纳更多内容
    dialog_width = 500
    dialog_height = 350
    dialog = pygame.Rect(
        (BASE_WIDTH - dialog_width) // 2,
        (BASE_HEIGHT - dialog_height) // 2,
        dialog_width, dialog_height
    )
    pygame.draw.rect(surface, (60, 60, 60), dialog)
    pygame.draw.rect(surface, (100, 150, 255), dialog, 4)

    # 标题
    title = font_large.render(f"第{level_num}关", True, WHITE)
    surface.blit(title, title.get_rect(centerx=dialog.centerx, top=dialog.top + 15))

    # 提示文字
    prompt = font_medium.render("发现保存的游戏进度", True, YELLOW)
    surface.blit(prompt, prompt.get_rect(centerx=dialog.centerx, top=dialog.top + 65))

    # 显示保存信息
    if saved_game_info:
        info_y = dialog.top + 105

        # 保存时间
        time_text = font_small.render(f"保存时间: {saved_game_info['save_time']}", True, WHITE)
        surface.blit(time_text, time_text.get_rect(centerx=dialog.centerx, top=info_y))

        # 波次信息
        if saved_game_info['wave_mode']:
            wave_text = font_small.render(f"波次: {saved_game_info['current_wave']}/{saved_game_info['max_waves']}",
                                          True, WHITE)
            surface.blit(wave_text, wave_text.get_rect(centerx=dialog.centerx, top=info_y + 50))
        else:
            progress_text = font_small.render("普通模式", True, WHITE)
            surface.blit(progress_text, progress_text.get_rect(centerx=dialog.centerx, top=info_y + 50))

    # 按钮 - 三个按钮横向排列特性:
    button_y = dialog.bottom - 70
    button_width = 130
    button_height = 45

    continue_btn = pygame.Rect(dialog.left + 30, button_y, button_width, button_height)
    restart_btn = pygame.Rect(dialog.centerx - button_width // 2, button_y, button_width, button_height)
    back_btn = pygame.Rect(dialog.right - button_width - 30, button_y, button_width, button_height)

    # 绘制按钮
    pygame.draw.rect(surface, (0, 150, 0), continue_btn)
    pygame.draw.rect(surface, (150, 100, 0), restart_btn)
    pygame.draw.rect(surface, (100, 100, 100), back_btn)  # 灰色返回按钮

    pygame.draw.rect(surface, WHITE, continue_btn, 2)
    pygame.draw.rect(surface, WHITE, restart_btn, 2)
    pygame.draw.rect(surface, WHITE, back_btn, 2)

    # 按钮文字
    continue_text = font_small.render("继续游戏", True, WHITE)
    restart_text = font_small.render("重新开始", True, WHITE)
    back_text = font_small.render("返回", True, WHITE)

    surface.blit(continue_text, continue_text.get_rect(center=continue_btn.center))
    surface.blit(restart_text, restart_text.get_rect(center=restart_btn.center))
    surface.blit(back_text, back_text.get_rect(center=back_btn.center))

    return continue_btn, restart_btn, back_btn


def draw_plant_select_grid(surface, plant_grid, animation_timer, animation_complete,
                           scaled_images, font_small, font_medium, selected_plants=None, plant_selection_manager=None,
                           exit_progress=0.0, plant_registry=None):
    """
    在战场区域绘制植物选择网格（6×5），符合原版植物大战僵尸风格
    修复：每种植物只能选择一次，选择后变灰且不可再次点击 - 完全使用植物注册表
    """
    import pygame

    # 导入植物注册表（如果未传入参数）
    if plant_registry is None:
        from plants.plant_registry import plant_registry as global_plant_registry
        plant_registry = global_plant_registry

    # 获取已选中的植物类型计数
    if selected_plants is None:
        selected_plants = []

    selected_count_dict = plant_selection_manager.get_total_selected_count_for_ui()

    # 计算动画进度
    if not animation_complete:
        progress = min(1.0, animation_timer / 60)
        alpha = int(255 * progress)
    else:
        alpha = 255

    # 计算退出动画的垂直偏移
    if exit_progress > 0:
        # 使用四次方缓入函数，让动画开始慢，然后加速向下
        from animation import AnimationManager
        eased_progress = AnimationEffects.ease_in_quart(exit_progress)

        # 计算向下移出的距离
        exit_offset_y = int(eased_progress * (BASE_HEIGHT + 200))  # 移出屏幕下方

        # 退出动画期间也要降低透明度
        alpha = int(alpha * (1.0 - exit_progress * 0.5))  # 逐渐变透明
    else:
        exit_offset_y = 0

    # 网格参数
    grid_cols = 6
    grid_rows = 5
    cell_width = GRID_SIZE
    cell_height = GRID_SIZE
    cell_spacing = 4

    # 计算起始位置（在战场区域居中）+ 退出动画偏移
    total_width = grid_cols * cell_width + (grid_cols - 1) * cell_spacing
    total_height = grid_rows * cell_height + (grid_rows - 1) * cell_spacing
    start_x = BATTLEFIELD_LEFT + (total_battlefield_width - total_width) // 2
    start_y = BATTLEFIELD_TOP + (total_battlefield_height - total_height) // 2 + exit_offset_y

    # 绘制棕色背景覆盖整个战场区域，应用退出动画偏移但保持原透明度
    battlefield_overlay = pygame.Surface((total_battlefield_width, total_battlefield_height), pygame.SRCALPHA)
    battlefield_overlay.fill((101, 67, 33, 249))  # 保持原来的固定透明度
    # 关键修改：背景板也应用退出动画偏移
    background_y = BATTLEFIELD_TOP + exit_offset_y
    surface.blit(battlefield_overlay, (BATTLEFIELD_LEFT, background_y))

    # 确保设置按钮区域保持可见和可点击
    # 绘制设置按钮的清除区域（透明）
    settings_clear_width = SETTINGS_BUTTON_WIDTH + 10  # 稍微扩大清除区域
    settings_clear_height = SETTINGS_BUTTON_HEIGHT + 10
    settings_clear_x = SETTINGS_BUTTON_X - 5
    settings_clear_y = SETTINGS_BUTTON_Y - 5

    # 如果设置按钮区域与战场覆盖区域重叠，则清除该区域
    if (settings_clear_x < BATTLEFIELD_LEFT + total_battlefield_width and
            settings_clear_x + settings_clear_width > BATTLEFIELD_LEFT and
            settings_clear_y < BATTLEFIELD_TOP + total_battlefield_height and
            settings_clear_y + settings_clear_height > BATTLEFIELD_TOP):

        # 计算重叠区域并清除
        overlap_x = max(settings_clear_x, BATTLEFIELD_LEFT)
        overlap_y = max(settings_clear_y, BATTLEFIELD_TOP)
        overlap_width = min(settings_clear_x + settings_clear_width,
                            BATTLEFIELD_LEFT + total_battlefield_width) - overlap_x
        overlap_height = min(settings_clear_y + settings_clear_height,
                             BATTLEFIELD_TOP + total_battlefield_height) - overlap_y

        if overlap_width > 0 and overlap_height > 0:
            clear_surface = pygame.Surface((overlap_width, overlap_height), pygame.SRCALPHA)
            clear_surface.fill((0, 0, 0, 0))  # 完全透明
            surface.blit(clear_surface, (overlap_x, overlap_y))

    # 绘制标题
    title = font_medium.render("选择你的植物", True, (255, 255, 255))
    title_x = start_x + (total_width - title.get_width()) // 2
    title_y = start_y - 50
    surface.blit(title, (title_x, title_y))

    # 绘制网格背景板
    grid_bg_surface = pygame.Surface((total_width + 20, total_height + 20), pygame.SRCALPHA)
    grid_bg_surface.fill((139, 69, 19, 220))
    grid_bg_surface.set_alpha(alpha)
    surface.blit(grid_bg_surface, (start_x - 10, start_y - 10))

    # 绘制网格边框
    grid_border_color = (160, 82, 45)
    pygame.draw.rect(surface, grid_border_color,
                     (start_x - 10, start_y - 10, total_width + 20, total_height + 20), 4)

    # 创建小字体用于价格显示
    price_font = pygame.font.Font(None, 24)

    # 绘制网格
    plant_rects = []

    for row in range(grid_rows):
        for col in range(grid_cols):
            cell_x = start_x + col * (cell_width + cell_spacing)
            cell_y = start_y + row * (cell_height + cell_spacing)
            cell_rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)

            plant_data = plant_grid[row][col]

            # 绘制槽位背景
            cell_surface = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)

            if plant_data is not None:
                plant_type = plant_data['type']
                is_selected = selected_count_dict.get(plant_type, 0) > 0

                if is_selected:
                    # 已选中的植物 - 浅灰色背景
                    cell_surface.fill((160, 160, 160, 200))  # 浅灰色
                    border_color = (120, 120, 120)  # 灰色边框
                else:
                    # 未选中的植物 - 亮棕色
                    cell_surface.fill((160, 120, 80, 255))
                    border_color = (200, 150, 100)  # 亮棕色边框
            else:
                # 空槽位 - 暗棕色
                cell_surface.fill((120, 80, 50, 200))
                border_color = (80, 60, 40)

            cell_surface.set_alpha(alpha)
            surface.blit(cell_surface, (cell_x, cell_y))

            # 绘制槽位边框
            pygame.draw.rect(surface, border_color, cell_rect, 2 if plant_data else 1)

            if plant_data is not None:
                plant_type = plant_data['type']
                is_selected = selected_count_dict.get(plant_type, 0) > 0

                # 绘制植物图标 - 完全使用植物注册表
                if scaled_images and plant_registry:
                    img_key = plant_registry.get_plant_icon_key(plant_type)

                    if img_key and img_key in scaled_images:
                        img = scaled_images[img_key].copy()

                        # 如果植物已被选中，应用灰度效果
                        if is_selected:
                            # 创建灰度版本
                            img = img.copy()
                            img.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)

                        # 缩放图标以适应格子
                        scaled_img = pygame.transform.scale(img, (cell_width - 16, cell_height - 30))
                        img_x = cell_x + 8
                        img_y = cell_y + 4
                        surface.blit(scaled_img, (img_x, img_y))

                        # 绘制植物价格（在卡槽下部） - 使用植物注册表
                        plant_price = plant_registry.get_plant_price(plant_type)
                        if plant_price > 0:
                            price_text = price_font.render(str(plant_price), True, (255, 255, 255))
                            # 计算价格文本位置（卡槽内下部居中）
                            price_x = cell_x + (cell_width - price_text.get_width()) // 2
                            price_y = cell_y + cell_height - price_text.get_height() - 3  # 距离底部3像素

                            # 直接绘制价格文本，无背景
                            surface.blit(price_text, (price_x, price_y))
                    else:
                        # 如果找不到图标，绘制占位符
                        placeholder_rect = pygame.Rect(cell_x + 8, cell_y + 4, cell_width - 16, cell_height - 30)

                        # 使用植物注册表获取颜色，如果没有则使用默认颜色
                        plant_color = plant_registry.get_plant_color(plant_type) if plant_registry else (150, 150, 150)

                        if is_selected:
                            # 选中状态下的颜色变暗
                            plant_color = tuple(c // 2 for c in plant_color)

                        pygame.draw.rect(surface, plant_color, placeholder_rect)
                        pygame.draw.rect(surface, WHITE, placeholder_rect, 1)

                        # 绘制植物名称首字符作为占位符
                        plant_name = plant_registry.get_plant_display_name(plant_type) if plant_registry else plant_type
                        if plant_name:
                            first_char = plant_name[0]
                            char_text = font_medium.render(first_char, True, WHITE)
                            char_x = placeholder_rect.centerx - char_text.get_width() // 2
                            char_y = placeholder_rect.centery - char_text.get_height() // 2
                            surface.blit(char_text, (char_x, char_y))

                # 只有未选中的植物才可以点击，并添加视觉提示
                if not is_selected:
                    # 添加点击高亮效果（表示可点击）
                    hover_surface = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                    hover_surface.fill((255, 255, 255, 30))
                    surface.blit(hover_surface, (cell_x, cell_y))

                    plant_rects.append((cell_rect, plant_data))

            # 绘制槽位间的浅棕色细线
            separator_color = (180, 140, 100)
            separator_alpha = min(alpha, 180)

            # 右侧分隔线
            if col < grid_cols - 1:
                sep_surface = pygame.Surface((cell_spacing, cell_height), pygame.SRCALPHA)
                sep_surface.fill((*separator_color, separator_alpha))
                surface.blit(sep_surface, (cell_x + cell_width, cell_y))

            # 下方分隔线
            if row < grid_rows - 1:
                sep_surface = pygame.Surface((cell_width, cell_spacing), pygame.SRCALPHA)
                sep_surface.fill((*separator_color, separator_alpha))
                surface.blit(sep_surface, (cell_x, cell_y + cell_height))

    # 绘制完成选择按钮
    finish_btn_width = 140
    finish_btn_height = 40
    finish_btn_x = start_x + (total_width - finish_btn_width) // 2
    finish_btn_y = start_y + total_height + 20
    finish_btn = pygame.Rect(finish_btn_x, finish_btn_y, finish_btn_width, finish_btn_height)

    # 完成按钮背景 - 使用渐变效果
    btn_surface = pygame.Surface((finish_btn_width, finish_btn_height), pygame.SRCALPHA)

    # 绘制渐变背景（绿色到亮绿色）
    for i in range(finish_btn_height):
        ratio = i / finish_btn_height
        r = int(60 + (120 - 60) * ratio)
        g = int(180 + (220 - 180) * ratio)
        b = int(60 + (120 - 60) * ratio)
        gradient_alpha = min(255, int(220 + 35 * ratio))

        line_color = (r, g, b, gradient_alpha)
        pygame.draw.line(btn_surface, line_color, (0, i), (finish_btn_width, i))

    btn_surface.set_alpha(alpha)
    surface.blit(btn_surface, (finish_btn_x, finish_btn_y))

    # 绘制按钮边框
    border_surface = pygame.Surface((finish_btn_width, finish_btn_height), pygame.SRCALPHA)
    border_surface.fill((0, 0, 0, 0))
    pygame.draw.rect(border_surface, (255, 255, 255), (0, 0, finish_btn_width, finish_btn_height), 3)
    surface.blit(border_surface, (finish_btn_x, finish_btn_y))

    # 完成按钮文字
    finish_text = font_small.render("开始战斗!", True, WHITE)
    text_x = finish_btn_x + (finish_btn_width - finish_text.get_width()) // 2
    text_y = finish_btn_y + (finish_btn_height - finish_text.get_height()) // 2
    surface.blit(finish_text, (text_x, text_y))

    return plant_rects, finish_btn


def get_button_color(base_color, is_hovered, hover_boost=30):
    """根据悬浮状态计算按钮颜色"""
    if not is_hovered:
        return base_color

    # 提高亮度
    if len(base_color) == 3:  # RGB
        return tuple(min(255, c + hover_boost) for c in base_color)
    else:  # RGBA
        return tuple(min(255, c + hover_boost) if i < 3 else c for i, c in enumerate(base_color))


def draw_shop_page(surface, animation_timer, animation_complete, exit_animation, exit_timer,
                   font_large, font_medium, state_manager, shop_manager, scaled_images=None, font_tiny=None,
                   font_small=None, game_manager=None):
    """绘制商店页面 - 支持入场和退出动画，显示小推车图片和购买状态"""

    # 计算页面偏移（商店从右侧滑入和滑出）
    if exit_animation:
        # 退出动画：从当前位置向右滑出屏幕
        exit_duration = 60
        progress = min(1.0, exit_timer / exit_duration)
        eased_progress = ease_in_cubic(progress)  # 加速退出

        page_start_x = 0  # 当前位置
        page_end_x = BASE_WIDTH  # 滑出到右侧屏幕外
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)
    else:
        # 入场动画：从右侧滑入
        animation_duration = 80
        progress = min(1.0, animation_timer / animation_duration) if not animation_complete else 1.0
        eased_progress = ease_out_quart(progress)

        page_start_x = BASE_WIDTH  # 从右侧屏幕外开始
        page_end_x = 0  # 最终位置
        page_offset_x = int(page_start_x + (page_end_x - page_start_x) * eased_progress)

    # 创建临时表面来绘制整个商店界面
    shop_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)

    # 绘制返回按钮
    back_btn = pygame.Rect(20, 20, 100, 40)
    pygame.draw.rect(shop_surface, RED, back_btn)
    back_text = font_medium.render("返回", True, WHITE)
    shop_surface.blit(back_text, (back_btn.centerx - back_text.get_width() // 2,
                                  back_btn.centery - back_text.get_height() // 2))

    # 改进的金币显示 - 动态调整宽度
    if hasattr(game_manager, 'coins'):
        coins_text = font_medium.render(f"金币: {game_manager.coins}", True, (255, 255, 255))
        text_width = coins_text.get_width()
        text_height = coins_text.get_height()

        # 计算背景矩形的位置和大小 - 动态调整宽度
        padding_x = 20  # 水平内边距（增加以适应更长的数字）
        padding_y = 10  # 垂直内边距

        # 设置最小宽度，但允许根据内容扩展
        min_width = 150  # 最小宽度
        bg_width = max(min_width, text_width + padding_x * 2)  # 取最小宽度和实际需要宽度的较大值
        bg_height = text_height + padding_y

        # 保持居中位置
        bg_x = (BASE_WIDTH - bg_width) // 2
        bg_y = 70 - padding_y // 2

        # 绘制背景矩形（金色渐变效果）
        bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)

        # 主背景色（深金色）
        pygame.draw.rect(shop_surface, (184, 134, 11), bg_rect)

        # 添加内部渐变效果（可选，让框更有层次感）
        # 绘制稍亮的顶部边缘
        top_highlight = pygame.Rect(bg_x + 2, bg_y + 2, bg_width - 4, 3)
        pygame.draw.rect(shop_surface, (220, 170, 30), top_highlight)

        # 添加亮边框（亮金色）
        pygame.draw.rect(shop_surface, (255, 215, 0), bg_rect, 3)  # 增加边框宽度到3像素，更显眼

        # 添加外部发光效果（可选，让金框更突出）
        glow_rect = pygame.Rect(bg_x - 1, bg_y - 1, bg_width + 2, bg_height + 2)
        pygame.draw.rect(shop_surface, (255, 235, 100), glow_rect, 1)

        # 绘制文字（在背景矩形中居中）
        text_x = bg_x + (bg_width - text_width) // 2
        text_y = bg_y + padding_y // 2
        shop_surface.blit(coins_text, (text_x, text_y))

    # 商品网格参数
    grid_cols = 4
    grid_rows = 2
    item_width = 120
    item_height = 140
    item_spacing_x = 30
    item_spacing_y = 20

    # 计算网格起始位置（居中）
    total_grid_width = grid_cols * item_width + (grid_cols - 1) * item_spacing_x
    total_grid_height = grid_rows * item_height + (grid_rows - 1) * item_spacing_y
    grid_start_x = (BASE_WIDTH - total_grid_width) // 2
    grid_start_y = 120

    # 获取当前页面的商品
    current_items = shop_manager.get_current_page_items()
    item_rects = []

    # 绘制商品网格
    for i, item in enumerate(current_items):
        row = i // grid_cols
        col = i % grid_cols

        item_x = grid_start_x + col * (item_width + item_spacing_x)
        item_y = grid_start_y + row * (item_height + item_spacing_y)
        item_rect = pygame.Rect(item_x, item_y, item_width, item_height)

        # 检查是否悬浮
        is_hovered = state_manager and state_manager.is_button_hovered(f"item_{i}", "shop")

        # 检查是否已购买
        is_purchased = shop_manager.is_purchased(item['id'])

        # 绘制商品背景
        if is_purchased:
            bg_color = (50, 70, 50) if not is_hovered else (60, 80, 60)  # 已购买显示为暗绿色
        else:
            bg_color = (70, 90, 120) if not is_hovered else (90, 110, 140)
        pygame.draw.rect(shop_surface, bg_color, item_rect)
        pygame.draw.rect(shop_surface, (150, 150, 150), item_rect, 2)

        # 绘制商品图标区域
        icon_rect = pygame.Rect(item_x + 10, item_y + 10, item_width - 20, 60)
        pygame.draw.rect(shop_surface, (50, 50, 50), icon_rect)

        # 绘制商品图标 - 特别处理小推车
        if item['id'] == 'cart' and scaled_images and 'cart_img' in scaled_images:
            # 显示小推车图片
            cart_img = scaled_images['cart_img']
            # 缩放到合适大小
            cart_scaled = pygame.transform.scale(cart_img, (50, 50))
            icon_x = icon_rect.centerx - 25
            icon_y = icon_rect.centery - 25
            shop_surface.blit(cart_scaled, (icon_x, icon_y))
        elif scaled_images and item.get('icon') in scaled_images:
            icon_img = scaled_images[item['icon']]
            icon_scaled = pygame.transform.scale(icon_img, (50, 50))
            icon_x = icon_rect.centerx - 25
            icon_y = icon_rect.centery - 25
            shop_surface.blit(icon_scaled, (icon_x, icon_y))
        else:
            # 绘制默认图标（简单的矩形）
            default_icon_color = {
                'tool': (255, 200, 100),
                'plant': (100, 255, 100),
                'consumable': (255, 100, 255)
            }.get(item.get('type', 'tool'), (200, 200, 200))

            pygame.draw.rect(shop_surface, default_icon_color,
                             (icon_rect.centerx - 20, icon_rect.centery - 20, 40, 40))

        # 绘制商品名称
        name_text = font_tiny.render(item['name'], True, WHITE)
        name_x = item_x + (item_width - name_text.get_width()) // 2
        name_y = item_y + 75
        shop_surface.blit(name_text, (name_x, name_y))

        # 绘制价格
        price_text = font_tiny.render(f"{item['price']}金币", True, YELLOW)
        price_x = item_x + (item_width - price_text.get_width()) // 2
        price_y = item_y + 95
        shop_surface.blit(price_text, (price_x, price_y))

        # 绘制购买按钮
        buy_btn = pygame.Rect(item_x + 20, item_y + 115, item_width - 40, 20)

        if is_purchased:
            # 已购买 - 灰色按钮
            btn_color = (100, 100, 100)
            btn_text = "已购买"
            btn_text_color = (180, 180, 180)
        else:
            # 未购买 - 绿色按钮
            btn_color = (0, 150, 0) if not is_hovered else (0, 180, 0)
            btn_text = "购买"
            btn_text_color = WHITE

        pygame.draw.rect(shop_surface, btn_color, buy_btn)
        pygame.draw.rect(shop_surface, WHITE, buy_btn, 1)

        buy_text = font_tiny.render(btn_text, True, btn_text_color)
        buy_text_x = buy_btn.centerx - buy_text.get_width() // 2
        buy_text_y = buy_btn.centery - buy_text.get_height() // 2
        shop_surface.blit(buy_text, (buy_text_x, buy_text_y))

        # 保存商品矩形（用于点击检测）
        adjusted_item_rect = pygame.Rect(item_x + page_offset_x, item_y, item_width, item_height)
        item_rects.append((adjusted_item_rect, item, i))

    # 绘制分页按钮
    page_y = grid_start_y + total_grid_height + 40

    # 上一页按钮
    prev_btn = pygame.Rect(BASE_WIDTH // 2 - 120, page_y, 80, 35)
    prev_enabled = shop_manager.can_prev_page()
    prev_color = (100, 100, 100) if not prev_enabled else (70, 130, 180)
    pygame.draw.rect(shop_surface, prev_color, prev_btn)
    pygame.draw.rect(shop_surface, WHITE, prev_btn, 2)

    prev_text = font_small.render("上一页", True, WHITE if prev_enabled else (150, 150, 150))
    prev_text_x = prev_btn.centerx - prev_text.get_width() // 2
    prev_text_y = prev_btn.centery - prev_text.get_height() // 2
    shop_surface.blit(prev_text, (prev_text_x, prev_text_y))

    # 页数显示
    page_info = font_small.render(f"{shop_manager.current_page + 1}/{shop_manager.total_pages}", True, WHITE)
    page_info_x = BASE_WIDTH // 2 - page_info.get_width() // 2
    shop_surface.blit(page_info, (page_info_x, page_y + 10))

    # 下一页按钮
    next_btn = pygame.Rect(BASE_WIDTH // 2 + 40, page_y, 80, 35)
    next_enabled = shop_manager.can_next_page()
    next_color = (100, 100, 100) if not next_enabled else (70, 130, 180)
    pygame.draw.rect(shop_surface, next_color, next_btn)
    pygame.draw.rect(shop_surface, WHITE, next_btn, 2)

    next_text = font_small.render("下一页", True, WHITE if next_enabled else (150, 150, 150))
    next_text_x = next_btn.centerx - next_text.get_width() // 2
    next_text_y = next_btn.centery - next_text.get_height() // 2
    shop_surface.blit(next_text, (next_text_x, next_text_y))

    # 将整个商店表面绘制到主表面，应用水平偏移
    surface.blit(shop_surface, (page_offset_x, 0))

    # 调整按钮位置（考虑页面偏移）
    adjusted_back_btn = pygame.Rect(back_btn.x + page_offset_x, back_btn.y, back_btn.width, back_btn.height)
    adjusted_prev_btn = pygame.Rect(prev_btn.x + page_offset_x, prev_btn.y, prev_btn.width,
                                    prev_btn.height) if prev_enabled else None
    adjusted_next_btn = pygame.Rect(next_btn.x + page_offset_x, next_btn.y, next_btn.width,
                                    next_btn.height) if next_enabled else None

    return adjusted_back_btn, item_rects, adjusted_prev_btn, adjusted_next_btn


def draw_insufficient_coins_dialog(surface, item_info, current_coins, font_large=None, font_medium=None,
                                   font_small=None):
    """绘制金币不足对话框dan"""
    if not item_info:
        return None, None

    # 半透明黑底
    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 对话框尺寸和位置
    dialog_width = 400
    dialog_height = 250
    dialog = pygame.Rect(
        (BASE_WIDTH - dialog_width) // 2,
        (BASE_HEIGHT - dialog_height) // 2,
        dialog_width, dialog_height
    )

    # 绘制对话框背景
    pygame.draw.rect(surface, (60, 60, 60), dialog)
    pygame.draw.rect(surface, (255, 100, 100), dialog, 4)  # 红色边框表示警告dan

    # 标题
    title = font_large.render("金币不足", True, (255, 100, 100))
    surface.blit(title, title.get_rect(centerx=dialog.centerx, top=dialog.top + 20))

    # 商品信息
    item_name = item_info.get('name', '未知商品')
    item_price = item_info.get('price', 0)

    # 商品名称
    name_text = font_medium.render(f"商品: {item_name}", True, WHITE)
    surface.blit(name_text, name_text.get_rect(centerx=dialog.centerx, top=dialog.top + 77))

    # 当前金币
    current_text = font_medium.render(f"当前: {current_coins} 金币", True, WHITE)
    surface.blit(current_text, current_text.get_rect(centerx=dialog.centerx, top=dialog.top + 110))

    # 确认按钮
    confirm_btn = pygame.Rect(dialog.centerx - 60, dialog.bottom - 60, 120, 40)
    pygame.draw.rect(surface, (100, 100, 100), confirm_btn)
    pygame.draw.rect(surface, WHITE, confirm_btn, 2)

    confirm_text = font_medium.render("确认", True, WHITE)
    surface.blit(confirm_text, confirm_text.get_rect(center=confirm_btn.center))

    return confirm_btn


def wrap_text_chinese(text, max_chars_per_line=11):
    """
    中文文字换行函数 - 按字符数量换行
    Args:
        text: 要换行的文字
        max_chars_per_line: 每行最大字符数（默认11个中文字符）
    Returns:
        lines: 换行后的文字列表
    """
    lines = []
    current_line = ""

    for char in text:
        # 检查添加当前字符后是否超过每行字符限制
        if len(current_line) >= max_chars_per_line:
            # 如果当前行不为空，保存当前行并开始新行
            if current_line:
                lines.append(current_line)
                current_line = char
            else:
                # 单个字符就超长了（不太可能发生），强制换行
                lines.append(char)
                current_line = ""
        else:
            current_line += char

    # 添加最后一行
    if current_line:
        lines.append(current_line)

    return lines


def draw_codex_detail_page(surface, detail_type, selected_index, font_large, font_medium, font_small, font_tiny,
                           scaled_images=None, state_manager=None):
    """
    绘制详细图鉴页面（修复版本 - 支持中文按字符数换行）

    Args:
        surface: 绘制表面植物选择
        detail_type: "plants" 或 "zombies"
        selected_index: 当前选中的项目索引
        font_large/medium/small: 字体
        scaled_images: 缩放后的图像字典
        state_manager: 状态管理器

    Returns:
        (back_btn, grid_rects): 返回按钮和网格矩形列表
    """

    # 清除背景（深蓝紫色渐变）
    for y in range(BASE_HEIGHT):
        ratio = y / BASE_HEIGHT
        r = int(20 + (40 - 20) * ratio)
        g = int(30 + (60 - 30) * ratio)
        b = int(80 + (120 - 80) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (BASE_WIDTH, y))

    # 绘制返回按钮
    back_btn = pygame.Rect(20, 20, 100, 40)
    pygame.draw.rect(surface, RED, back_btn)
    back_text = font_medium.render("返回", True, WHITE)
    surface.blit(back_text, (back_btn.centerx - back_text.get_width() // 2,
                             back_btn.centery - back_text.get_height() // 2))

    # 绘制标题
    title_text = "植物图鉴" if detail_type == "plants" else "僵尸图鉴"
    title = font_large.render(title_text, True, WHITE)
    title_x = (BASE_WIDTH - title.get_width()) // 2
    title_y = 30
    surface.blit(title, (title_x, title_y))

    # 定义数据
    if detail_type == "plants":
        codex_data = get_plants_codex_data()
    else:
        codex_data = get_zombies_codex_data()

    # 左侧网格参数
    grid_cols = 6
    grid_rows = 5
    cell_size = 80
    cell_spacing = 8

    grid_start_x = 50
    grid_start_y = 120

    total_grid_width = grid_cols * cell_size + (grid_cols - 1) * cell_spacing
    total_grid_height = grid_rows * cell_size + (grid_rows - 1) * cell_spacing

    # 绘制网格背景板
    grid_bg = pygame.Rect(grid_start_x - 15, grid_start_y - 15,
                          total_grid_width + 30, total_grid_height + 30)
    pygame.draw.rect(surface, (40, 40, 60, 200), grid_bg)
    pygame.draw.rect(surface, (100, 100, 150), grid_bg, 3)

    # 绘制左侧网格
    grid_rects = []
    max_items = grid_cols * grid_rows

    for row in range(grid_rows):
        for col in range(grid_cols):
            index = row * grid_cols + col
            if index >= len(codex_data):
                break  # 超出数据范围就停止

            cell_x = grid_start_x + col * (cell_size + cell_spacing)
            cell_y = grid_start_y + row * (cell_size + cell_spacing)
            cell_rect = pygame.Rect(cell_x, cell_y, cell_size, cell_size)

            item_data = codex_data[index]

            # 检查是否选中或悬浮
            is_selected = (index == selected_index)
            is_hovered = (state_manager and
                          state_manager.is_button_hovered(f"grid_{index}", "codex_detail"))

            # 绘制单元格背景
            if is_selected:
                cell_color = (100, 150, 100)  # 选中时的绿色
            elif is_hovered:
                cell_color = (80, 120, 80)  # 悬浮时的浅绿色
            else:
                cell_color = (60, 60, 80)  # 默认颜色

            pygame.draw.rect(surface, cell_color, cell_rect)
            pygame.draw.rect(surface, (150, 150, 200), cell_rect, 2)

            # 绘制图标
            if scaled_images and item_data.get('icon_key') in scaled_images:
                icon_img = scaled_images[item_data['icon_key']]
                # 缩放到适合单元格的大小
                icon_scaled = pygame.transform.scale(icon_img, (cell_size - 10, cell_size - 10))
                icon_x = cell_x + 5
                icon_y = cell_y + 5
                surface.blit(icon_scaled, (icon_x, icon_y))
            else:
                # 绘制默认图标（彩色矩形）
                default_color = item_data.get('color', (150, 150, 150))
                icon_rect = pygame.Rect(cell_x + 10, cell_y + 10, cell_size - 20, cell_size - 20)
                pygame.draw.rect(surface, default_color, icon_rect)
                pygame.draw.rect(surface, WHITE, icon_rect, 1)

                # 在默认图标中绘制名称首字母
                if item_data.get('name'):
                    first_char = item_data['name'][0]
                    char_text = font_medium.render(first_char, True, WHITE)
                    char_x = icon_rect.centerx - char_text.get_width() // 2
                    char_y = icon_rect.centery - char_text.get_height() // 2
                    surface.blit(char_text, (char_x, char_y))

            grid_rects.append((cell_rect, item_data))

    # 右侧展示区域 - 与网格顶部对齐
    display_start_x = grid_start_x + total_grid_width + 40
    display_width = BASE_WIDTH - display_start_x - 30
    display_start_y = grid_start_y  # 修改：与网格起始Y位置对齐
    display_height = 500

    # 绘制展示区域背景
    display_bg = pygame.Rect(display_start_x, display_start_y, display_width, display_height)
    pygame.draw.rect(surface, (50, 50, 70, 220), display_bg)
    pygame.draw.rect(surface, (120, 120, 180), display_bg, 3)

    # 获取当前选中的项目数据
    if 0 <= selected_index < len(codex_data):
        selected_item = codex_data[selected_index]

        # 绘制项目名称 - 使用较小字体，位置向上移动
        name_text = font_medium.render(selected_item.get('name', '未知'), True, WHITE)
        name_x = display_start_x + (display_width - name_text.get_width()) // 2
        name_y = display_start_y + 10  # 修改：从20改为10，向上移动
        surface.blit(name_text, (name_x, name_y))

        # 绘制大图区域
        large_img_y = name_y + 50
        large_img_height = 200
        large_img_rect = pygame.Rect(display_start_x + 20, large_img_y,
                                     display_width - 40, large_img_height)
        pygame.draw.rect(surface, (30, 30, 50), large_img_rect)
        pygame.draw.rect(surface, (100, 100, 150), large_img_rect, 2)

        # 绘制大图
        if scaled_images and selected_item.get('large_icon_key') in scaled_images:
            large_img = scaled_images[selected_item['large_icon_key']]
            # 缩放到适合区域的大小，保持宽高比
            img_width, img_height = large_img.get_size()
            scale_factor = min((large_img_rect.width - 20) / img_width,
                               (large_img_rect.height - 20) / img_height)
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            large_img_scaled = pygame.transform.scale(large_img, (new_width, new_height))
            img_x = large_img_rect.centerx - new_width // 2
            img_y = large_img_rect.centery - new_height // 2
            surface.blit(large_img_scaled, (img_x, img_y))
        else:
            # 绘制默认大图标
            default_color = selected_item.get('color', (150, 150, 150))
            default_large_rect = pygame.Rect(large_img_rect.centerx - 80, large_img_rect.centery - 80,
                                             160, 160)
            pygame.draw.rect(surface, default_color, default_large_rect)
            pygame.draw.rect(surface, WHITE, default_large_rect, 3)

            # 绘制大号名称首字母
            if selected_item.get('name'):
                first_char = selected_item['name'][0]
                char_text = font_large.render(first_char, True, WHITE)
                char_x = default_large_rect.centerx - char_text.get_width() // 2
                char_y = default_large_rect.centery - char_text.get_height() // 2
                surface.blit(char_text, (char_x, char_y))

        # 绘制描述区域
        desc_y = large_img_y + large_img_height + 20
        desc_height = display_height - (desc_y - display_start_y) - 20
        desc_rect = pygame.Rect(display_start_x + 20, desc_y, display_width - 40, desc_height)
        pygame.draw.rect(surface, (20, 20, 40), desc_rect)
        pygame.draw.rect(surface, (80, 80, 120), desc_rect, 2)

        # 绘制描述文字标题 - 使用小字体
        desc_title = font_small.render("描述:", True, WHITE)
        surface.blit(desc_title, (desc_rect.x + 15, desc_rect.y + 15))

        # 绘制描述内容 - 使用按字符数换行（关键修改）
        desc_text = selected_item.get('description', '详细描述待添加...')

        # 使用新的中文换行函数
        wrapped_lines = wrap_text_chinese(desc_text, max_chars_per_line=11)

        # 渲染每一行文字
        line_height = font_tiny.get_height() + 5  # 行间距5像素
        text_start_y = desc_rect.y + 45  # 在标题下方开始

        for i, line in enumerate(wrapped_lines):
            line_y = text_start_y + i * line_height

            # 检查是否超出描述区域
            if line_y + line_height > desc_rect.bottom - 15:
                # 如果超出了，显示省略号
                if i > 0:  # 至少显示了一行
                    ellipsis = font_tiny.render("...", True, (200, 200, 200))
                    prev_line_y = text_start_y + (i - 1) * line_height
                    # 在上一行末尾添加省略号
                    prev_line_text = wrapped_lines[i - 1]
                    prev_line_surface = font_tiny.render(prev_line_text, True, (200, 200, 200))
                    ellipsis_x = desc_rect.x + 15 + prev_line_surface.get_width() + 5
                    surface.blit(ellipsis, (ellipsis_x, prev_line_y))
                break

            # 渲染当前行
            line_surface = font_tiny.render(line, True, (200, 200, 200))
            surface.blit(line_surface, (desc_rect.x + 15, line_y))

    return back_btn, grid_rects

def get_plants_codex_data():
        """获取植物图鉴数据"""
        return [
            {
                'name': '豌豆射手',
                'icon_key': 'pea_shooter_60',
                'large_icon_key': 'pea_shooter_img',
                'color': (100, 200, 100),
                'description': '基础攻击植物，发射豌豆攻击僵尸。攻击力适中，是防线的前期火力来源。'
            },
            {
                'name': '向日葵',
                'icon_key': 'sunflower_60',
                'large_icon_key': 'sunflower_img',
                'color': (255, 255, 100),
                'description': '产生阳光的植物，是经济的基础。定期产生阳光资源，用于种植其他植物。'
            },
            {
                'name': '坚果墙',
                'icon_key': 'wall_nut_60',
                'large_icon_key': 'wall_nut_img',
                'color': (139, 69, 19),
                'description': '防御植物，可以阻挡僵尸前进。拥有较高的生命值，能够承受大量伤害。'
            },
            {
                'name': '西瓜投手',
                'icon_key': 'watermelon_60',
                'large_icon_key': 'watermelon_img',
                'color': (255, 100, 100),
                'description': '强力攻击植物，投掷西瓜造成范围伤害。攻击力很高，能对付强敌。'
            },
            {
                'name': '猫尾草',
                'icon_key': 'cattail_60',
                'large_icon_key': 'cattail_img',
                'color': (100, 255, 100),
                'description': '水陆两生植物，可以攻击任意路线的僵尸。射程很远，攻击灵活多变。'
            },
            {
                'name': '樱桃炸弹',
                'icon_key': 'cherry_bomb_60',
                'large_icon_key': 'cherry_bomb_img',
                'color': (255, 50, 50),
                'description': '一次性爆炸植物，造成大范围伤害。能够瞬间清除大片僵尸群。'
            },
            {
                'name': '黄瓜',
                'icon_key': 'cucumber_60',
                'large_icon_key': 'cucumber_img',
                'color': (100, 200, 100),
                'description': '特殊攻击植物，使僵尸产生生理反应。能够眩晕并令多个敌人死亡。'
            },
            {
                'name': '蒲公英',
                'icon_key': 'dandelion_60',
                'large_icon_key': 'dandelion_img',
                'color': (255, 255, 150),
                'description': '像霰弹枪，种子可以飞到其他位置。攻击模式特殊，覆盖面广。'
            },
            {
                'name': '闪电花',
                'icon_key': 'lightning_flower_60',
                'large_icon_key': 'lightning_flower_img',
                'color': (255, 255, 100),
                'description': '电系攻击植物，发射闪电攻击僵尸。具有连锁闪电的特殊效果。'
            },
            {
                'name': '冰仙人掌',
                'icon_key': 'ice_cactus_60',
                'large_icon_key': 'ice_cactus_img',
                'color': (100, 200, 255),
                'description': '冰系攻击植物，可以冻缓僵尸移动速度。攻击附带凝速效果。'
            },
            {
                'name': '阳光菇',
                'icon_key': 'sun_shroom_60',
                'large_icon_key': 'sun_shroom_img',
                'color': (100, 200, 255),
                'description': '每6秒产生25阳光，暗夜关卡的首选'
            },
            {
                'name': '月亮花',
                'icon_key': 'moon_flower_60',
                'large_icon_key': 'moon_flower_img',
                'color': (100, 200, 255),
                'description': '发射小月亮子弹。场上每增加一个月亮花，所有植物的攻击速度提高10%，最高提高50%'
            },
            {
                'name': '地刺',
                'icon_key': 'luker_60',
                'large_icon_key': 'luker_img',
                'color': (100, 200, 255),
                'description': '无视僵尸防具，可秒杀所有正在自己身上的车子类僵尸'
            },
            {
                'name': '迷幻投手',
                'icon_key': 'psychedelic_pitcher_60',
                'large_icon_key': 'psychedelic_pitcher_img',
                'color': (100, 200, 255),
                'description': '魅惑僵尸使其暂时为你作战'
            }

        ]

def get_zombies_codex_data():
    """获取僵尸图鉴数据"""
    return [
        {
            'name': '普通僵尸',
            'icon_key': 'zombie_60',
            'large_icon_key': 'zombie_img',
            'color': (150, 150, 150),
            'description': '最基础的僵尸，移动缓慢但数量众多。生命值较低，容易被消灭。'
        },

        {
            'name': '巨人僵尸',
            'icon_key': 'giant_zombie_60',
            'large_icon_key': 'giant_zombie_img',
            'color': (100, 100, 200),
            'description': '体型巨大的僵尸，生命值和攻击力都很高。是强大的精英敌人。'
        },
        {
            'name': '铁门僵尸',
            'icon_key': 'armored_zombie_60',
            'large_icon_key': 'armored_zombie_img',
            'color': (150, 100, 50),
            'description': '身穿装甲的僵尸，具有特殊防护能力。对某些攻击有抗性。'
        },
        {
            'name': '爆炸僵尸',
            'icon_key': 'exploding_zombie_60',
            'large_icon_key': 'exploding_zombie_img',
            'color': (255, 80, 80),
            'description': '危险的红色僵尸，死亡时会发生剧烈爆炸。爆炸会对3x3范围内的所有植物造成巨大伤害'
        },
        {
            'name': '冰车僵尸',
            'icon_key': 'ice_car_zombie_60',
            'large_icon_key': 'ice_car_zombie_img',
            'color': (255, 80, 80),
            'description': '碾压一切非地刺类植物，身后留下不可种植植物的冰道'
        },
    ]


def draw_purchase_confirm_dialog(surface, item, current_coins, font_large=None, font_medium=None, font_small=None):
    """绘制购买确认对话框"""
    if not item:
        return None, None

    # 半透明背景
    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 对话框尺寸和位置
    dialog_width = 450
    dialog_height = 300
    dialog = pygame.Rect(
        (BASE_WIDTH - dialog_width) // 2,
        (BASE_HEIGHT - dialog_height) // 2,
        dialog_width, dialog_height
    )

    # 绘制对话框背景
    pygame.draw.rect(surface, (60, 60, 60), dialog)
    pygame.draw.rect(surface, (100, 150, 255), dialog, 4)  # 蓝色边框

    # 标题
    title = font_large.render("确认购买", True, WHITE)
    surface.blit(title, title.get_rect(centerx=dialog.centerx, top=dialog.top + 20))

    # 商品信息
    item_name = item.get('name', '未知商品')
    item_price = item.get('price', 0)
    item_desc = item.get('description', '')

    # 商品名称
    name_text = font_medium.render(f"商品: {item_name}", True, WHITE)
    surface.blit(name_text, name_text.get_rect(centerx=dialog.centerx, top=dialog.top + 70))

    # 商品价格
    price_color = WHITE if current_coins >= item_price else RED
    price_text = font_medium.render(f"价格: {item_price} 金币", True, price_color)
    surface.blit(price_text, price_text.get_rect(centerx=dialog.centerx, top=dialog.top + 105))

    # 当前金币
    coins_text = font_medium.render(f"当前: {current_coins} 金币", True, YELLOW)
    surface.blit(coins_text, coins_text.get_rect(centerx=dialog.centerx, top=dialog.top + 140))

    # 商品描述（使用中文换行函数）
    if item_desc:
        desc_lines = wrap_text_chinese(item_desc, max_chars_per_line=20)
        desc_y = dialog.top + 175
        for i, line in enumerate(desc_lines[:2]):  # 最多显示2行
            desc_text = font_small.render(line, True, (200, 200, 200))
            surface.blit(desc_text, desc_text.get_rect(centerx=dialog.centerx, top=desc_y))
            desc_y += 25

    # 检查金币是否足够
    can_afford = current_coins >= item_price

    # 按钮
    button_y = dialog.bottom - 60
    button_width = 120
    button_height = 40
    button_spacing = 40

    # 确认按钮（金币足够时才可点击）
    confirm_btn = pygame.Rect(
        dialog.centerx - button_width - button_spacing // 2,
        button_y,
        button_width,
        button_height
    )

    if can_afford:
        pygame.draw.rect(surface, (0, 150, 0), confirm_btn)
        confirm_text_color = WHITE
    else:
        pygame.draw.rect(surface, (100, 100, 100), confirm_btn)
        confirm_text_color = (150, 150, 150)

    pygame.draw.rect(surface, WHITE, confirm_btn, 2)
    confirm_text = font_medium.render("确认", True, confirm_text_color)
    surface.blit(confirm_text, confirm_text.get_rect(center=confirm_btn.center))

    # 取消按钮
    cancel_btn = pygame.Rect(
        dialog.centerx + button_spacing // 2,
        button_y,
        button_width,
        button_height
    )

    pygame.draw.rect(surface, (150, 0, 0), cancel_btn)
    pygame.draw.rect(surface, WHITE, cancel_btn, 2)
    cancel_text = font_medium.render("取消", True, WHITE)
    surface.blit(cancel_text, cancel_text.get_rect(center=cancel_btn.center))

    # 如果金币不足，确认按钮不可点击
    if not can_afford:
        confirm_btn = None

    return confirm_btn, cancel_btn