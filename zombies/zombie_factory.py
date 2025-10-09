"""
僵尸工厂类 - 用于创建不同类型的僵尸
"""
from .normal_zombie import NormalZombie
from .giant_zombie import GiantZombie
from .exploding_zombie import ExplodingZombie
from .ice_car_zombie import IceCarZombie


class ZombieFactory:
    """僵尸工厂类 - 为了保持向后兼容性"""

    @staticmethod
    def create_zombie(row, zombie_type="normal", **kwargs):
        """
        创建指定类型的僵尸

        Args:
            row: 僵尸所在行
            zombie_type: 僵尸类型 ("normal", "giant" 或 "exploding")
            **kwargs: 其他僵尸参数

        Returns:
            相应类型的僵尸实例
        """
        if zombie_type == "giant":
            return GiantZombie(row, **kwargs)
        elif zombie_type == "exploding":
            return ExplodingZombie(row, **kwargs)
        elif zombie_type == "normal":
            return NormalZombie(row, **kwargs)
        elif zombie_type == "ice_car":
            return IceCarZombie(row, **kwargs)
        else:
            # 默认创建普通僵尸
            return NormalZombie(row, **kwargs)

    def __new__(cls, row, has_armor_prob=0.3, is_fast=False, wave_mode=False,
                fast_multiplier=2.5, constants=None, sounds=None, images=None,
                level_settings=None, zombie_type="normal"):
        """
        为了保持向后兼容性，当直接调用 Zombie() 时创建相应的僵尸
        这样原有的 Zombie(...) 调用方式仍然可以工作
        """
        return cls.create_zombie(
            row=row,
            zombie_type=zombie_type,
            has_armor_prob=has_armor_prob,
            is_fast=is_fast,
            wave_mode=wave_mode,
            fast_multiplier=fast_multiplier,
            constants=constants,
            sounds=sounds,
            images=images,
            level_settings=level_settings
        )


def create_zombie(row, zombie_type="normal", **kwargs):
    """
    便捷函数：创建指定类型的僵尸

    Args:
        row: 僵尸所在行
        zombie_type: 僵尸类型 ("normal", "giant" 或 "exploding")
        **kwargs: 其他僵尸参数

    Returns:
        相应类型的僵尸实例

    Example:
        # 创建普通僵尸
        zombie1 = create_zombie(0, "normal", has_armor_prob=0.5)

        # 创建巨人僵尸
        zombie2 = create_zombie(1, "giant", is_fast=True)

        # 创建爆炸僵尸
        zombie3 = create_zombie(2, "exploding", wave_mode=True)
    """
    return ZombieFactory.create_zombie(row, zombie_type, **kwargs)