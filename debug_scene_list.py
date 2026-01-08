#!/usr/bin/env python3
"""
独立的场景列表调试脚本
在 Isaac Sim 启动前运行，避免输出被覆盖
"""

import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", type=str, default="/home/ubuntu/fengbh/NavDP/fbh_test_scene")
parser.add_argument("--scene_index", type=int, default=2)
args = parser.parse_args()

print("="*80)
print("[DEBUG] Command line arguments:")
print(f"  --scene_dir: {args.scene_dir}")
print(f"  --scene_index: {args.scene_index}")
print("="*80)

# 列出所有场景（使用 sorted 确保字母顺序）
available_scenes = sorted(os.listdir(args.scene_dir))
print(f"[DEBUG] Available scenes in directory: {len(available_scenes)} total")
print("[DEBUG] Scene list (SORTED alphabetical order):")
for i, scene in enumerate(available_scenes):
    marker = " <-- SELECTED" if i == args.scene_index else ""
    print(f"  [{i}] {scene}{marker}")

# 验证索引
if args.scene_index >= len(available_scenes):
    print(f"\n[ERROR] scene_index {args.scene_index} is out of range!")
    print(f"[ERROR] Available indices: 0 to {len(available_scenes)-1}")
    exit(1)

# 显示选中的场景
selected_scene = available_scenes[args.scene_index]
print(f"\n[DEBUG] Selected scene: {selected_scene}")
print(f"[DEBUG] Full scene path: {os.path.join(args.scene_dir, selected_scene)}")
print("="*80)

# 预期的保存目录
scene_dir_name = args.scene_dir.split("/")[-1]
save_dir = f"./pointgoal_navdp_{scene_dir_name}/{selected_scene}/"
print(f"[DEBUG] Expected save_dir: {save_dir}")
print(f"[DEBUG] Full save path: {os.path.abspath(save_dir)}")
print("="*80)

