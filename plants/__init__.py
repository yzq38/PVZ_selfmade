"""
植物模块 - 统一导出所有植物类
"""

# 导入植物注册系统
from .plant_registry import plant_registry

# 导入基础类
from .base_plant import BasePlant
from .shooter_base import ShooterPlant

# 导入粒子效果
from .particles import (
    ExplosionParticle,
    CucumberExplosionParticle,
    CucumberSprayParticle
)

# 导入所有植物类
from .sunflower import Sunflower
from .shooter import Shooter
from .wall_nut import WallNut
from .cherry_bomb import CherryBomb
from .cucumber import Cucumber
from .melon_pult import MelonPult
from .cattail import Cattail
from .dandelion import Dandelion
from .ice_cactus import IceCactus
from .lightning_flower import LightningFlower
from .sun_shroom import SunShroom
from .moon_flower import MoonFlower
from .luker import Luker
from .psychedelic_pitcher import PsychedelicPitcher




# 注册所有植物类到注册表
plant_registry.register(Sunflower)
plant_registry.register(Shooter)
plant_registry.register(WallNut)
plant_registry.register(CherryBomb)
plant_registry.register(Cucumber)
plant_registry.register(MelonPult)
plant_registry.register(Cattail)
plant_registry.register(Dandelion)
plant_registry.register(IceCactus)
plant_registry.register(LightningFlower)
plant_registry.register(SunShroom)
plant_registry.register(MoonFlower)
plant_registry.register(Luker)
plant_registry.register(PsychedelicPitcher)


# 植物工厂函数 - 保持向后兼容
def Plant(row, col, plant_type=None, constants=None, images=None, level_manager=None):
    """
    植物工厂函数 - 根据类型创建对应的植物实例
    保持与原代码的兼容性
    """
    # 优先从注册表获取植物类
    plant_class = plant_registry.get_plant_class(plant_type)

    if plant_class:
        # 使用注册的植物类创建实例
        return plant_class(row, col, constants, images, level_manager)

    # 如果注册表中没有，使用原来的逻辑（向后兼容）
    if plant_type == "sunflower":
        return Sunflower(row, col, constants, images, level_manager)
    elif plant_type == "shooter":
        return Shooter(row, col, constants, images, level_manager)
    elif plant_type == "wall_nut":
        return WallNut(row, col, constants, images, level_manager)
    elif plant_type == "cherry_bomb":
        return CherryBomb(row, col, constants, images, level_manager)
    elif plant_type == "cucumber":
        return Cucumber(row, col, constants, images, level_manager)
    elif plant_type == "melon_pult":
        return MelonPult(row, col, constants, images, level_manager)
    elif plant_type == "cattail":
        return Cattail(row, col, constants, images, level_manager)
    elif plant_type == "dandelion":
        return Dandelion(row, col, constants, images, level_manager)
    elif plant_type == "ice_cactus":
        return IceCactus(row, col, constants, images, level_manager)
    elif plant_type == "lightning_flower":
        return LightningFlower(row, col, constants, images, level_manager)
    elif plant_type == "sun_shroom":
        return SunShroom(row, col, constants, images, level_manager)
    elif plant_type == "luker":
        return Luker(row, col, constants, images, level_manager)
    elif plant_type == "psychedelic_pitcher":
        return PsychedelicPitcher(row, col, constants, images, level_manager)
    else:
        # 默认返回基础植物
        return BasePlant(row, col, plant_type, constants, images, level_manager)


# 导出所有需要的类和函数
__all__ = [
    # 注册系统
    'plant_registry',

    # 基础类
    'BasePlant',
    'ShooterPlant',

    # 粒子效果
    'ExplosionParticle',
    'CucumberExplosionParticle',
    'CucumberSprayParticle',

    # 植物类
    'Sunflower',
    'Shooter',
    'WallNut',
    'CherryBomb',
    'Cucumber',
    'MelonPult',
    'Cattail',
    'Dandelion',
    'IceCactus',
    'LightningFlower',
    'SunShroom',
    'MoonFlower',
    'Luker',
    'PsychedelicPitcher',

    # 工厂函数
    'Plant',
]