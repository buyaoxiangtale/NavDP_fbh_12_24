#!/usr/bin/env python3
"""
将 goal_pairs 文件夹中的 .npy 文件复制到对应的场景子文件夹中

匹配规则：
- 场景子文件夹名：Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726
- 对应的 .npy 文件：Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726_pointgoal_pairs.npy
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

def find_matching_npy(scene_name: str, npy_files: List[Path]) -> Path:
    """
    根据场景名称查找匹配的 .npy 文件
    
    参数:
        scene_name: 场景文件夹名称
        npy_files: .npy 文件列表
    
    返回:
        匹配的 .npy 文件路径，如果未找到返回 None
    """
    # 尝试多种匹配方式
    # 1. 精确匹配：场景名 + "_pointgoal_pairs.npy"
    target_name_1 = f"{scene_name}_pointgoal_pairs.npy"
    
    # 2. 如果场景名包含时间戳，可能 .npy 文件名略有不同
    # 例如：场景名可能是 "Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726"
    # .npy 文件名可能是 "Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726_pointgoal_pairs.npy"
    
    for npy_file in npy_files:
        npy_name = npy_file.name
        
        # 精确匹配
        if npy_name == target_name_1:
            return npy_file
        
        # 前缀匹配：检查 .npy 文件名是否以场景名开头
        # 例如：场景名 "Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726"
        # .npy 文件名 "Alkylation_of_Ethyl_Acetoacetate_with_Bis_4-fluoro_20251229_003726_pointgoal_pairs.npy"
        if npy_name.startswith(scene_name + "_"):
            return npy_file
        
        # 反向匹配：检查场景名是否在 .npy 文件名中
        # 去掉 .npy 后缀和可能的 _pointgoal_pairs 后缀
        npy_base = npy_name.replace("_pointgoal_pairs.npy", "").replace(".npy", "")
        if scene_name == npy_base or scene_name in npy_base:
            return npy_file
    
    return None

def copy_npy_to_scenes(scene_root_dir: str, npy_source_dir: str, dry_run: bool = False):
    """
    将 .npy 文件复制到对应的场景子文件夹中
    
    参数:
        scene_root_dir: 场景根目录（例如：scene_1231）
        npy_source_dir: .npy 文件源目录（例如：test_yaml_data/goal_pairs）
        dry_run: 如果为 True，只显示将要执行的操作，不实际复制
    """
    scene_root = Path(scene_root_dir)
    npy_source = Path(npy_source_dir)
    
    # 验证目录存在
    if not scene_root.exists():
        raise ValueError(f"场景根目录不存在: {scene_root}")
    
    if not scene_root.is_dir():
        raise ValueError(f"场景根目录不是文件夹: {scene_root}")
    
    if not npy_source.exists():
        raise ValueError(f".npy 源目录不存在: {npy_source}")
    
    if not npy_source.is_dir():
        raise ValueError(f".npy 源目录不是文件夹: {npy_source}")
    
    # 获取所有 .npy 文件
    npy_files = list(npy_source.glob("*.npy"))
    
    if len(npy_files) == 0:
        print(f"[WARNING] 在 {npy_source} 中没有找到 .npy 文件")
        return
    
    print(f"[INFO] 找到 {len(npy_files)} 个 .npy 文件")
    print(f"[INFO] 场景根目录: {scene_root}")
    print(f"[INFO] .npy 源目录: {npy_source}")
    print("=" * 80)
    
    # 获取所有场景子文件夹
    scene_dirs = [d for d in scene_root.iterdir() if d.is_dir()]
    
    if len(scene_dirs) == 0:
        print(f"[WARNING] 在 {scene_root} 中没有找到子文件夹")
        return
    
    print(f"[INFO] 找到 {len(scene_dirs)} 个场景子文件夹")
    print("=" * 80)
    
    results = {
        'total': len(scene_dirs),
        'copied': 0,
        'not_found': 0,
        'already_exists': 0,
        'errors': 0,
        'details': []
    }
    
    # 处理每个场景文件夹
    for scene_dir in sorted(scene_dirs):
        scene_name = scene_dir.name
        print(f"\n[INFO] 处理场景: {scene_name}")
        
        # 查找匹配的 .npy 文件
        matching_npy = find_matching_npy(scene_name, npy_files)
        
        if matching_npy is None:
            print(f"  -> [WARNING] 未找到匹配的 .npy 文件")
            results['not_found'] += 1
            results['details'].append({
                'scene': scene_name,
                'status': 'not_found',
                'npy_file': None
            })
            continue
        
        # 目标文件路径
        target_npy = scene_dir / matching_npy.name
        
        # 检查文件是否已存在
        if target_npy.exists():
            print(f"  -> [SKIP] 文件已存在: {target_npy.name}")
            results['already_exists'] += 1
            results['details'].append({
                'scene': scene_name,
                'status': 'already_exists',
                'npy_file': matching_npy.name,
                'target': str(target_npy)
            })
            continue
        
        # 复制文件
        try:
            if dry_run:
                print(f"  -> [DRY-RUN] 将复制: {matching_npy.name}")
                print(f"     从: {matching_npy}")
                print(f"     到: {target_npy}")
            else:
                shutil.copy2(matching_npy, target_npy)
                print(f"  -> [SUCCESS] 已复制: {matching_npy.name}")
                print(f"     到: {target_npy}")
            
            results['copied'] += 1
            results['details'].append({
                'scene': scene_name,
                'status': 'copied',
                'npy_file': matching_npy.name,
                'target': str(target_npy)
            })
        
        except Exception as e:
            print(f"  -> [ERROR] 复制失败: {e}")
            results['errors'] += 1
            results['details'].append({
                'scene': scene_name,
                'status': 'error',
                'npy_file': matching_npy.name,
                'error': str(e)
            })
    
    # 打印总结
    print("\n" + "=" * 80)
    print("处理总结")
    print("=" * 80)
    print(f"总场景数: {results['total']}")
    print(f"成功复制: {results['copied']}")
    print(f"文件已存在: {results['already_exists']}")
    print(f"未找到匹配: {results['not_found']}")
    print(f"错误: {results['errors']}")
    print("=" * 80)
    
    # 显示未找到的场景
    if results['not_found'] > 0:
        print("\n未找到匹配 .npy 文件的场景:")
        print("-" * 80)
        for detail in results['details']:
            if detail['status'] == 'not_found':
                print(f"  - {detail['scene']}")
        print("-" * 80)
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description="将 goal_pairs 文件夹中的 .npy 文件复制到对应的场景子文件夹中"
    )
    parser.add_argument(
        "--scene_root",
        type=str,
        required=True,
        help="场景根目录路径（例如：scene_1231）"
    )
    parser.add_argument(
        "--npy_source",
        type=str,
        default="test_yaml_data/goal_pairs",
        help=".npy 文件源目录路径（默认：test_yaml_data/goal_pairs）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要执行的操作，不实际复制文件"
    )
    
    args = parser.parse_args()
    
    try:
        results = copy_npy_to_scenes(
            args.scene_root,
            args.npy_source,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            print("\n[INFO] 这是预览模式（dry-run），没有实际复制文件")
            print("[INFO] 去掉 --dry-run 参数来实际执行复制操作")
        
        return 0
    
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

