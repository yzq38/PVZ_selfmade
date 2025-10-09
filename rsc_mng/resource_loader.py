"""
资源加载模块 - 处理图片和其他资源的加载
重构版本 - 路径更新到rsc_mng文件夹
"""
import os
import sys

import pygame


from core.constants import *


def load_image(name, size=None):
    """加载图片资源"""
    try:
        # 重构：更新图片文件路径到rsc_mng/images文件夹
        image = pygame.image.load(f"rsc_mng/images/{name}.png").convert_alpha()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except:
        print(f"无法加载图片: rsc_mng/images/{name}.png")
        # 创建一个占位符表面
        surf = pygame.Surface(size if size else (GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 128))  # 半透明洋红色作为占位符
        return surf


def load_all_images():
    """加载所有游戏图片资源"""
    try:
        images = {
            # 植物图片
            'pea_shooter_img': load_image("peashooter", (GRID_SIZE, GRID_SIZE)),
            'sunflower_img': load_image("sunflower", (GRID_SIZE, GRID_SIZE)),
            'watermelon_img': load_image("watermelon", (GRID_SIZE, GRID_SIZE)),
            'cattail_img': load_image("cattail", (GRID_SIZE, GRID_SIZE)),
            'wall_nut_img': load_image("wall_nut", (GRID_SIZE, GRID_SIZE)),
            'cherry_bomb_img': load_image("cherry_bomb", (GRID_SIZE, GRID_SIZE)),
            'cucumber_img': load_image("cucumber", (GRID_SIZE, GRID_SIZE)),
            'dandelion_img': load_image("dandelion", (GRID_SIZE, GRID_SIZE)),
            'lightning_flower_img': load_image("lightning_flower", (GRID_SIZE, GRID_SIZE)),
            'ice_cactus_img': load_image("ice_cactus", (GRID_SIZE, GRID_SIZE)),
            'sun_shroom_img':load_image("sun_shroom", (GRID_SIZE, GRID_SIZE)),
            'moon_flower_img':load_image("moon_flower", (GRID_SIZE, GRID_SIZE)),
            'luker_img':load_image("luker", (GRID_SIZE, GRID_SIZE)),
            'psychedelic_pitcher_img':load_image("psychedelic_pitcher", (GRID_SIZE, GRID_SIZE)),

            # 僵尸图片
            'zombie_img': load_image("zombie", (GRID_SIZE, GRID_SIZE)),
            'zombie_armor_img': load_image("zombie_armor", (GRID_SIZE, GRID_SIZE)),
            'giant_zombie_img': load_image("giant_zombie", (int(GRID_SIZE * 1.5), int(GRID_SIZE * 1.5))),
            'ice_car_zombie_img': load_image("ice_car_zombie", (int(GRID_SIZE * 1.3), int(GRID_SIZE * 1.3))),

            # 子弹图片
            'pea_img': load_image("pea", (20, 20)),
            'watermelon_bullet_img': load_image("watermelon_bullet", (20, 20)),
            'spike_img': load_image("spike", (24, 18)),
            'dandelion_seed_img': load_image("dandelion_seed", (24, 24)),
            'ice_bullet_img': load_image("ice_bullet", (24, 24)),
            'small_moon_img': load_image("small_moon", (22, 22)),
            'small_psychedelic_bullet_img': load_image("small_psychedelic_bullet", (20, 20)),

            # 防具图片
            'armor_img': load_image("armor", (GRID_SIZE - 10, GRID_SIZE - 10)),

            # 背景和UI元素
            'grid_bg_img': load_image("grid_bg", (GRID_SIZE, GRID_SIZE)),
            'card_bg_img': load_image("card_bg", (CARD_WIDTH, CARD_HEIGHT)),
            'shovel_img': load_image("shovel", (SHOVEL_WIDTH, SHOVEL_HEIGHT)),
            'hammer_img': load_image("hammer", (SHOVEL_WIDTH, SHOVEL_HEIGHT)),
            'settings_img': load_image("settings", (SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)),
            'ice_lane_img': load_image("ice_lane", (GRID_SIZE, GRID_SIZE)),

            # 主菜单背景
            'menu_bg_img': load_image("menu_bg", (BASE_WIDTH, BASE_HEIGHT)),
            'trophy_img': load_image("trophy", (60, 60)),
            #小推车
            'cart_img':load_image("cart",(35,35))
        }
        return images
    except Exception as e:
        print(f"加载图片时出错: {e}")
        # 返回空字典，游戏将使用颜色块作为占位符
        return {}


def get_images():
    """获取图片字典，供Plant、Zombie和Bullet类使用"""
    images = load_all_images()
    return {
        'pea_shooter_img': images.get('pea_shooter_img'),
        'sunflower_img': images.get('sunflower_img'),
        'watermelon_img': images.get('watermelon_img'),
        'cattail_img': images.get('cattail_img'),
        'zombie_img': images.get('zombie_img'),
        'armor_img': images.get('armor_img'),
        'pea_img': images.get('pea_img'),
        'watermelon_bullet_img': images.get('watermelon_bullet_img'),
        'spike_img': images.get('spike_img')  ,
        'wall_nut_img': images.get('wall_nut_img'),
        'cherry_bomb':images.get('cherry_bomb_img'),
        'cucumber': images.get('cucumber_img'),
        'dandelion': images.get('dandelion_img'),
        'dandelion_seed': images.get('dandelion_seed_img'),
        'hammer': images.get('hammer_img'),
        'lightning_flower': images.get('lightning_flower_img'),
        'ice_cactus': images.get('ice_cactus_img'),
        'ice_bullet': images.get('ice_bullet_img'),
        'sun_shroom_img': images.get('sun_shroom_img'),
        'moon_flower_img': images.get('moon_flower_img'),
        'small_moon_img': images.get('small_moon_img'),
        'luker_img': images.get('luker_img'),
        'psychedelic_pitcher_img': images.get('psychedelic_pitcher_img'),
        'small_psychedelic_bullet_img': images.get('small_psychedelic_bullet_img'),
    }


def preload_scaled_images():
    """预先加载所有需要缩放的图片，支持植物注册系统"""
    scaled_images = {}
    images = load_all_images()

    # 尝试导入植物注册系统
    try:
        from plants.plant_registry import plant_registry
        use_registry = True
    except ImportError:
        use_registry = False

    # 定义植物图片映射
    plant_image_map = {
        'shooter': ('pea_shooter_img', 'pea_shooter'),
        'sunflower': ('sunflower_img', 'sunflower'),
        'melon_pult': ('watermelon_img', 'watermelon'),
        'cattail': ('cattail_img', 'cattail'),
        'wall_nut': ('wall_nut_img', 'wall_nut'),
        'cherry_bomb': ('cherry_bomb_img', 'cherry_bomb'),
        'cucumber': ('cucumber_img', 'cucumber'),
        'dandelion': ('dandelion_img', 'dandelion'),
        'lightning_flower': ('lightning_flower_img', 'lightning_flower'),
        'ice_cactus': ('ice_cactus_img', 'ice_cactus'),
        'sun_shroom': ('sun_shroom_img', 'sun_shroom'),
        'moon_flower':('moon_flower_img','moon_flower'),
        'luker':('luker_img','luker'),
        'psychedelic_pitcher':('psychedelic_pitcher_img','psychedelic_pitcher'),

    }

    # 使用注册系统或手动方式加载植物图片
    if use_registry:
        # 从注册表获取所有植物类型
        for plant_type in plant_registry.get_all_plants():
            if plant_type in plant_image_map:
                img_key, img_name = plant_image_map[plant_type]
                if images.get(img_key):
                    # 获取植物期望的图标键名
                    icon_key = plant_registry.get_plant_icon_key(plant_type)

                    # 如果键名包含尺寸信息，提取并缩放
                    if '_60' in icon_key:
                        scaled_images[icon_key] = pygame.transform.scale(images[img_key], (60, 60))
                    else:
                        scaled_images[icon_key] = images[img_key]

                    # 同时保留原始大小
                    scaled_images[img_key] = images[img_key]
    else:
        # 后备方案：手动加载
        for plant_type, (img_key, img_name) in plant_image_map.items():
            if images.get(img_key):
                # 创建60x60版本
                scaled_images[f'{img_name}_60'] = pygame.transform.scale(images[img_key], (60, 60))
                # 保留原始版本
                scaled_images[img_key] = images[img_key]

    # 添加僵尸图像（用于僵尸图鉴）
    if images.get('zombie_img'):
        scaled_images['zombie_img'] = images['zombie_img']
        scaled_images['zombie_60'] = pygame.transform.scale(images['zombie_img'], (60, 60))

        # 新增：生成爆炸僵尸图片（基于普通僵尸 + 红色覆盖层）
        # 生成大尺寸爆炸僵尸图片（用于图鉴详细页面）
        exploding_zombie_img = images['zombie_img'].copy()
        red_overlay_large = pygame.Surface(exploding_zombie_img.get_size(), pygame.SRCALPHA)
        red_overlay_large.fill((255, 0, 0, 80))  # 半透明红色，透明度80
        exploding_zombie_img.blit(red_overlay_large, (0, 0))
        scaled_images['exploding_zombie_img'] = exploding_zombie_img

        # 生成60x60爆炸僵尸图标（用于图鉴网格）
        exploding_zombie_60 = pygame.transform.scale(images['zombie_img'], (60, 60))
        red_overlay_small = pygame.Surface((60, 60), pygame.SRCALPHA)
        red_overlay_small.fill((255, 0, 0, 80))  # 半透明红色，透明度80
        exploding_zombie_60.blit(red_overlay_small, (0, 0))
        scaled_images['exploding_zombie_60'] = exploding_zombie_60

        # 新增：生成铁门僵尸图片（基于普通僵尸 + 装甲图片）
        if images.get('armor_img'):
            # 生成大尺寸铁门僵尸图片（用于图鉴详细页面）
            armored_zombie_img = images['zombie_img'].copy()
            # 缩放装甲图片以适应僵尸大小
            armor_scaled = pygame.transform.scale(images['armor_img'],
                                                  (images['zombie_img'].get_width() - 10,
                                                   images['zombie_img'].get_height() - 10))
            # 将装甲图片叠加到僵尸图片上（稍微偏移以显示层次感）
            armor_x = 5
            armor_y = 5
            armored_zombie_img.blit(armor_scaled, (armor_x, armor_y))
            scaled_images['armored_zombie_img'] = armored_zombie_img

            # 生成60x60铁门僵尸图标（用于图鉴网格）
            armored_zombie_60 = pygame.transform.scale(images['zombie_img'], (60, 60))
            armor_scaled_small = pygame.transform.scale(images['armor_img'], (50, 50))
            armored_zombie_60.blit(armor_scaled_small, (5, 5))
            scaled_images['armored_zombie_60'] = armored_zombie_60
        else:
            # 如果没有装甲图片，使用默认的僵尸图片
            scaled_images['armored_zombie_img'] = images['zombie_img']
            scaled_images['armored_zombie_60'] = pygame.transform.scale(images['zombie_img'], (60, 60))

    if images.get('zombie_armor_img'):
        scaled_images['zombie_armor_img'] = images['zombie_armor_img']
        scaled_images['cone_zombie_60'] = pygame.transform.scale(images['zombie_armor_img'], (60, 60))
        scaled_images['cone_zombie_img'] = images['zombie_armor_img']

    if images.get('giant_zombie_img'):
        scaled_images['giant_zombie_img'] = images['giant_zombie_img']
        scaled_images['bucket_zombie_60'] = pygame.transform.scale(images['giant_zombie_img'], (60, 60))
        scaled_images['bucket_zombie_img'] = images['giant_zombie_img']
        scaled_images['fast_zombie_60'] = pygame.transform.scale(images['giant_zombie_img'], (60, 60))
        scaled_images['fast_zombie_img'] = images['giant_zombie_img']
        scaled_images['giant_zombie_60'] = pygame.transform.scale(images['giant_zombie_img'], (60, 60))
    if images.get('ice_car_zombie_img'):
        scaled_images['ice_car_zombie_img'] = images['ice_car_zombie_img']
        scaled_images['ice_car_zombie_60'] = pygame.transform.scale(images['ice_car_zombie_img'], (60, 60))

    if images.get('ice_lane_img'):
        scaled_images['ice_lane_img'] = images['ice_lane_img']
        scaled_images['ice_lane_60'] = pygame.transform.scale(images['ice_lane_img'], (60, 60))

    # 预缓存设置按钮图片
    if images.get('settings_img'):
        scaled_images['settings_50'] = pygame.transform.scale(images['settings_img'], (50, 50))

    # 预缓存西瓜子弹图片
    if images.get('watermelon_bullet_img'):
        scaled_images['watermelon_bullet_40'] = pygame.transform.scale(images['watermelon_bullet_img'], (40, 40))

    # 预缓存尖刺子弹图片
    if images.get('spike_img'):
        scaled_images['spike_24'] = pygame.transform.scale(images['spike_img'], (24, 24))
    if images.get('ice_bullet_img'):
        scaled_images['ice_bullet_24'] = pygame.transform.scale(images['ice_bullet_img'], (24, 24))
    if images.get('dandelion_seed_img'):
        scaled_images['dandelion_seed_24'] = pygame.transform.scale(images['dandelion_seed_img'], (24, 24))
    if images.get('cart_img'):
        scaled_images['cart_img'] = images['cart_img']  # 保持原始大小35x35
        scaled_images['cart_30'] = pygame.transform.scale(images['cart_img'], (35, 35))
    if images.get('hammer_img'):
        scaled_images['hammer_img'] = images['hammer_img']  # 添加原始大小的锤子图片
        scaled_images['hammer_80'] = pygame.transform.scale(images['hammer_img'], (80, 80))

    if images.get('card_bg_img'):
        scaled_images['card_bg_img'] = images['card_bg_img']  # 保持原始大小
        scaled_images['card_bg_50'] = pygame.transform.scale(images['card_bg_img'], (50, 50))  # 商店图标大小

    # 预缓存灰化版本的图片（用于冷却状态）
    original_keys = list(scaled_images.keys())
    for key in original_keys:
        img = scaled_images[key]
        if not key.endswith('_gray'):
            gray_surface = img.copy()
            gray_surface.fill((128, 128, 128), special_flags=pygame.BLEND_MULT)
            scaled_images[key + '_gray'] = gray_surface

    return scaled_images


def verify_plant_images(scaled_images):
    """验证所有植物图片是否正确加载"""
    try:
        from plants.plant_registry import plant_registry

        missing_images = []
        for plant_type in plant_registry.get_all_plants():
            icon_key = plant_registry.get_plant_icon_key(plant_type)
            if icon_key not in scaled_images:
                missing_images.append((plant_type, icon_key))

        if missing_images:
            print("警告：以下植物图片缺失:")
            for plant_type, icon_key in missing_images:
                print(f"  - {plant_type}: {icon_key}")
        else:
            print("所有植物图片加载成功")

        return len(missing_images) == 0
    except ImportError:
        return True  # 没有注册系统时跳过验证


def get_plant_image(scaled_images, plant_type, size=60):
    """获取植物图片的辅助函数"""
    try:
        from plants.plant_registry import plant_registry
        icon_key = plant_registry.get_plant_icon_key(plant_type)
    except ImportError:
        # 后备方案
        icon_key = f"{plant_type}_{size}"

    return scaled_images.get(icon_key)


def create_placeholder_image(size=(60, 60), color=(255, 0, 255, 128)):
    """创建占位符图片"""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)

    # 添加文字提示
    try:
        font = pygame.font.Font(None, 12)
        text = font.render("?", True, (255, 255, 255))
        text_rect = text.get_rect(center=(size[0] // 2, size[1] // 2))
        surf.blit(text, text_rect)
    except:
        pass

    return surf

def initialize_fonts():
    """改进的字体初始化函数"""
    chinese_fonts = [
        "Microsoft YaHei",
        "微软雅黑",
        "SimHei",
        "黑体",
        "Arial Unicode MS",
        "Noto Sans CJK SC",
        "DejaVu Sans",
    ]

    for font_name in chinese_fonts:
        try:
            test_font = pygame.font.SysFont(font_name, 24)
            test_surface = test_font.render("测试", True, (255, 255, 255))

            if test_surface.get_width() > 10:  # 渲染成功
                font_tiny = pygame.font.SysFont(font_name, 18)
                font_small = pygame.font.SysFont(font_name, 24)
                font_medium = pygame.font.SysFont(font_name, 32)
                font_large = pygame.font.SysFont(font_name, 48)
                print(f"成功加载中文字体: {font_name}")
                return font_small, font_medium, font_large, font_tiny
        except:
            continue

    # 字体加载失败的回退
    print("中文字体加载失败，使用默认字体")
    font_tiny = pygame.font.Font(None, 18)
    font_small = pygame.font.Font(None, 24)
    font_medium = pygame.font.Font(None, 32)
    font_large = pygame.font.Font(None, 48)
    return font_small, font_medium, font_large, font_tiny