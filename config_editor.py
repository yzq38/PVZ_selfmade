"""
简化版关卡配置编辑器 - 专注于基础配置，特性由代码管理
运行方式：python config_editor.py
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import copy

# 导入特性管理器
try:
    from core.features_manager import features_manager
except ImportError:
    print("警告：无法导入特性管理器，特性功能将不可用")
    features_manager = None


class SimplifiedLevelConfigEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("植物大战僵尸 - 简化配置编辑器")
        self.root.geometry("800x600")

        # 配置数据
        self.config_file = "database/levels.json"
        self.config_data = None
        self.current_level = None
        self.unsaved_changes = False

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="新建配置", command=self.new_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="打开配置", command=self.open_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="另存为", command=self.save_as_config).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Button(toolbar, text="添加关卡", command=self.add_level).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="复制关卡", command=self.copy_level).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="删除关卡", command=self.delete_level).pack(side=tk.LEFT, padx=(0, 5))

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧关卡列表
        left_frame = ttk.LabelFrame(content_frame, text="关卡列表")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=(0, 5))

        self.level_listbox = tk.Listbox(left_frame, width=20)
        self.level_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.level_listbox.bind('<<ListboxSelect>>', self.on_level_select)

        # 右侧编辑区域
        right_frame = ttk.LabelFrame(content_frame, text="关卡编辑")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.setup_edit_form(right_frame)

    def setup_edit_form(self, parent):
        """设置编辑表单"""
        # 基本信息
        basic_frame = ttk.LabelFrame(parent, text="基本信息")
        basic_frame.pack(fill=tk.X, padx=5, pady=5)

        # 关卡名称
        ttk.Label(basic_frame, text="关卡名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(basic_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
        self.name_var.trace('w', self.on_change)

        basic_frame.columnconfigure(1, weight=1)

        # 游戏参数
        params_frame = ttk.LabelFrame(parent, text="游戏参数")
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        # 第一行：波次数、初始阳光
        ttk.Label(params_frame, text="波次数:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_waves_var = tk.IntVar()
        ttk.Spinbox(params_frame, from_=1, to=20, textvariable=self.max_waves_var, width=10,
                    command=self.on_change).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(params_frame, text="初始阳光:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=2)
        self.initial_sun_var = tk.IntVar()
        ttk.Spinbox(params_frame, from_=0, to=1000, increment=25, textvariable=self.initial_sun_var, width=10,
                    command=self.on_change).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        # 僵尸参数
        zombie_frame = ttk.LabelFrame(parent, text="僵尸参数")
        zombie_frame.pack(fill=tk.X, padx=5, pady=5)

        # 铁门概率
        ttk.Label(zombie_frame, text="铁门概率:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.armor_prob_var = tk.DoubleVar()
        armor_scale = tk.Scale(zombie_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                               variable=self.armor_prob_var, command=self.on_change)
        armor_scale.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
        self.armor_label = ttk.Label(zombie_frame, text="0%")
        self.armor_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)

        # 快速倍率
        ttk.Label(zombie_frame, text="快速倍率:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.fast_mult_var = tk.DoubleVar()
        fast_scale = tk.Scale(zombie_frame, from_=1, to=5, resolution=0.1, orient=tk.HORIZONTAL,
                              variable=self.fast_mult_var, command=self.on_change)
        fast_scale.grid(row=1, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
        self.fast_label = ttk.Label(zombie_frame, text="1.0x")
        self.fast_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)

        zombie_frame.columnconfigure(1, weight=1)

        # 特性管理（只读显示）
        if features_manager:
            features_frame = ttk.LabelFrame(parent, text="关卡特性（由代码自动管理）")
            features_frame.pack(fill=tk.X, padx=5, pady=5)

            # 特性显示区域
            self.features_text = tk.Text(features_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
            features_scroll = ttk.Scrollbar(features_frame, orient="vertical", command=self.features_text.yview)
            self.features_text.configure(yscrollcommand=features_scroll.set)

            self.features_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            features_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            # 说明文本
            info_label = ttk.Label(features_frame,
                                   text="特性由features_manager.py自动管理，编辑器仅显示不可修改",
                                   foreground="gray")
            info_label.pack(fill=tk.X, padx=5, pady=(0, 5))

        # 预览区域
        preview_frame = ttk.LabelFrame(parent, text="JSON预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_text = tk.Text(preview_frame, height=10, state=tk.DISABLED)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定变量变化事件
        for var in [self.armor_prob_var, self.fast_mult_var]:
            var.trace('w', self.on_scale_change)

    def on_scale_change(self, *args):
        """滑块值变化处理"""
        self.armor_label.config(text=f"{self.armor_prob_var.get():.0%}")
        self.fast_label.config(text=f"{self.fast_mult_var.get():.1f}x")
        self.on_change()

    def on_change(self, *args):
        """数据变化处理"""
        self.unsaved_changes = True
        self.update_status("有未保存的更改")
        self.update_preview()

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                self.update_level_list()
                self.update_status(f"已加载配置文件: {self.config_file}")
            else:
                self.create_default_config()
                self.update_status("创建了默认配置")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
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
            "levels": {}
        }
        self.update_level_list()

    def update_level_list(self):
        """更新关卡列表"""
        self.level_listbox.delete(0, tk.END)
        if self.config_data and "levels" in self.config_data:
            for level_num in sorted(self.config_data["levels"].keys(), key=int):
                level_config = self.config_data["levels"][level_num]
                level_name = level_config.get("name", f"第{level_num}关")
                self.level_listbox.insert(tk.END, f"{level_num}: {level_name}")

    def on_level_select(self, event=None):
        """关卡选择事件"""
        selection = self.level_listbox.curselection()
        if selection:
            level_text = self.level_listbox.get(selection[0])
            level_num = level_text.split(":")[0]
            self.load_level_data(level_num)

    def load_level_data(self, level_num):
        """加载关卡数据到编辑表单"""
        if not self.config_data or level_num not in self.config_data["levels"]:
            return

        self.current_level = level_num
        level_config = self.config_data["levels"][level_num]

        # 加载基本信息
        self.name_var.set(level_config.get("name", ""))

        # 加载游戏参数
        self.max_waves_var.set(level_config.get("max_waves", 5))
        self.initial_sun_var.set(level_config.get("initial_sun", 100))

        # 加载僵尸参数
        self.armor_prob_var.set(level_config.get("zombie_armor_prob", 0.3))
        self.fast_mult_var.set(level_config.get("fast_zombie_multiplier", 2.5))

        # 更新特性显示
        if features_manager:
            self.update_features_display(level_num)

        self.update_preview()
        self.on_scale_change()

    def update_features_display(self, level_num):
        """更新特性显示区域"""
        if not features_manager:
            return

        try:
            level_int = int(level_num)
            recommended_features = features_manager.get_recommended_features_for_level(level_int)

            self.features_text.config(state=tk.NORMAL)
            self.features_text.delete(1.0, tk.END)

            if recommended_features:
                self.features_text.insert(tk.END, f"关卡{level_num}推荐特性：\n\n")
                for feature_id in recommended_features:
                    description = features_manager.get_feature_description_text(feature_id)
                    self.features_text.insert(tk.END, f"• {description}\n")
            else:
                self.features_text.insert(tk.END, f"关卡{level_num}无特殊特性")

            self.features_text.config(state=tk.DISABLED)
        except (ValueError, TypeError):
            pass

    def save_current_level(self):
        """保存当前编辑的关卡"""
        if not self.current_level:
            return

        level_config = {
            "name": self.name_var.get(),
            "max_waves": self.max_waves_var.get(),
            "initial_sun": self.initial_sun_var.get(),
            "zombie_armor_prob": self.armor_prob_var.get(),
            "fast_zombie_multiplier": self.fast_mult_var.get()
        }



        self.config_data["levels"][self.current_level] = level_config

    def update_preview(self):
        """更新JSON预览"""
        if self.current_level:
            self.save_current_level()
            level_config = self.config_data["levels"][self.current_level]

            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, json.dumps(level_config, indent=2, ensure_ascii=False))
            self.preview_text.config(state=tk.DISABLED)

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.after(5000, lambda: self.status_var.set("准备就绪"))

    def new_config(self):
        """新建配置"""
        if self.unsaved_changes:
            if not messagebox.askyesno("确认", "当前有未保存的更改，是否继续？"):
                return
        self.create_default_config()
        self.config_file = "untitled.json"
        self.unsaved_changes = False
        self.update_status("已创建新配置")

    def open_config(self):
        """打开配置文件"""
        if self.unsaved_changes:
            if not messagebox.askyesno("确认", "当前有未保存的更改，是否继续？"):
                return
        file_path = filedialog.askopenfilename(
            title="打开配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.config_file = file_path
            self.load_config()
            self.unsaved_changes = False

    def save_config(self):
        """保存配置文件"""
        try:
            if self.current_level:
                self.save_current_level()

            self.config_data["metadata"]["last_modified"] = datetime.now().isoformat()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)

            self.unsaved_changes = False
            self.update_status(f"已保存配置到: {self.config_file}")
            messagebox.showinfo("成功", "配置文件保存成功！")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {e}")

    def save_as_config(self):
        """另存为配置文件"""
        file_path = filedialog.asksaveasfilename(
            title="另存为配置文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.config_file = file_path
            self.save_config()

    def add_level(self):
        """添加新关卡"""
        existing_levels = [int(k) for k in self.config_data["levels"].keys()]
        new_level_num = 1 if not existing_levels else max(existing_levels) + 1

        default_config = self.config_data["default_config"].copy()
        default_config["name"] = f"{new_level_num}.新关卡"

        self.config_data["levels"][str(new_level_num)] = default_config
        self.update_level_list()
        self.unsaved_changes = True
        self.update_status(f"已添加关卡 {new_level_num}")

        # 自动选择新关卡
        for i in range(self.level_listbox.size()):
            if self.level_listbox.get(i).startswith(str(new_level_num) + ":"):
                self.level_listbox.selection_set(i)
                self.load_level_data(str(new_level_num))
                break

    def copy_level(self):
        """复制当前关卡"""
        if not self.current_level:
            messagebox.showwarning("警告", "请先选择要复制的关卡")
            return

        self.save_current_level()
        existing_levels = [int(k) for k in self.config_data["levels"].keys()]
        new_level_num = max(existing_levels) + 1

        source_config = copy.deepcopy(self.config_data["levels"][self.current_level])
        source_config["name"] = f"{new_level_num}.{source_config['name']}的副本"

        self.config_data["levels"][str(new_level_num)] = source_config
        self.update_level_list()
        self.unsaved_changes = True
        self.update_status(f"已复制关卡到第 {new_level_num} 关")

    def delete_level(self):
        """删除当前关卡"""
        if not self.current_level:
            messagebox.showwarning("警告", "请先选择要删除的关卡")
            return

        if messagebox.askyesno("确认删除", f"确定要删除第 {self.current_level} 关吗？"):
            del self.config_data["levels"][self.current_level]
            self.current_level = None
            self.update_level_list()
            self.unsaved_changes = True
            self.update_status("已删除关卡")
            self.clear_form()

    def clear_form(self):
        """清空编辑表单"""
        self.name_var.set("")
        self.max_waves_var.set(5)
        self.initial_sun_var.set(100)
        self.armor_prob_var.set(0.3)
        self.fast_mult_var.set(2.5)

        if features_manager:
            self.features_text.config(state=tk.NORMAL)
            self.features_text.delete(1.0, tk.END)
            self.features_text.config(state=tk.DISABLED)

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)

    def run(self):
        """运行编辑器"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """窗口关闭事件"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel("确认退出", "有未保存的更改，是否保存后退出？")
            if result is True:  # 保存后退出
                self.save_config()
                self.root.destroy()
            elif result is False:  # 不保存直接退出
                self.root.destroy()
            # None 表示取消，不做任何操作特性管理
        else:
            self.root.destroy()


def main():
    """主函数"""
    editor = SimplifiedLevelConfigEditor()
    editor.run()


if __name__ == "__main__":
    main()