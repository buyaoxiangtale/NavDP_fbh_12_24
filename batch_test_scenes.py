#!/usr/bin/env python3
"""
批量测试多个场景的 Python 版本
比 bash 脚本更灵活，支持更多配置
"""

import os
import sys
import subprocess
import argparse
import numpy as np
from datetime import datetime
from pathlib import Path

def get_num_episodes_from_npy(scene_dir, scene_name):
    """
    从场景目录中的 .npy 文件获取数据条数，并计算 num_episodes = 数据条数 * 3
    
    参数:
        scene_dir: 场景目录路径
        scene_name: 场景名称
    
    返回:
        num_episodes: 计算得到的 episode 数量，如果找不到文件则返回 None
    """
    scene_path = os.path.join(scene_dir, scene_name)
    
    # 查找 .npy 文件（可能是 pointgoal_pairs.npy 或其他格式）
    npy_files = list(Path(scene_path).glob("*.npy"))
    
    if not npy_files:
        # 尝试查找包含场景名称的 .npy 文件
        pattern = f"{scene_name}_pointgoal_pairs.npy"
        npy_file = os.path.join(scene_path, pattern)
        if os.path.exists(npy_file):
            npy_files = [Path(npy_file)]
        else:
            # 尝试查找任何 pointgoal_pairs.npy 文件
            pattern = "*pointgoal_pairs.npy"
            npy_files = list(Path(scene_path).glob(pattern))
    
    if not npy_files:
        return None
    
    # 使用第一个找到的 .npy 文件
    npy_file = npy_files[0]
    try:
        data = np.load(str(npy_file))
        # 获取数据条数（第一维的大小）
        num_pairs = data.shape[0] if len(data.shape) > 0 else len(data)
        num_episodes = num_pairs * 3
        return num_episodes
    except Exception as e:
        print(f"[WARNING] 无法读取 .npy 文件 {npy_file}: {e}")
        return None

def test_single_scene(scene_dir, scene_index, num_envs, num_episodes, speed, stop_threshold, port):
    """
    测试单个场景
    
    返回: (success, scene_name)
    """
    cmd = [
        "python", "eval_pointgoal_wheeled.py",
        "--scene_dir", scene_dir,
        "--scene_index", str(scene_index),
        "--num_envs", str(num_envs),
        "--num_episodes", str(num_episodes),
        "--speed", str(speed),
        "--stop_threshold", str(stop_threshold),
        "--port", str(port)
    ]
    
    print(f"\n{'='*80}")
    print(f"Testing: scene_index={scene_index}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 提取选中的场景名（从调试输出）
        scene_name = "unknown"
        for line in result.stdout.split('\n'):
            if 'Selected scene:' in line:
                scene_name = line.split('Selected scene:')[-1].strip()
                break
        
        return True, scene_name, result.stdout, result.stderr
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        print(f"[ERROR] Error output:\n{e.stderr}")
        return False, scene_name, e.stdout, e.stderr

def main():
    parser = argparse.ArgumentParser(description="批量测试多个场景")
    parser.add_argument("--scene_dir", type=str, 
                       default="/home/ubuntu/fengbh/NavDP/fbh_test_scene")
    parser.add_argument("--scene_indices", type=str, required=True,
                       help="场景索引列表，用逗号分隔，例如: 0,1,2")
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--num_episodes", type=int, default=None,
                       help="每个场景的测试回合数。如果未指定，将从 .npy 文件自动计算（数据条数 * 3）")
    parser.add_argument("--use_npy_episodes", action="store_true", default=True,
                       help="自动从 .npy 文件计算 num_episodes（默认启用）")
    parser.add_argument("--speed", type=float, default=0.5)
    parser.add_argument("--stop_threshold", type=float, default=-0.3)
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--dry-run", action="store_true",
                       help="只显示要运行的命令，不实际执行")
    
    args = parser.parse_args()
    
    # 解析场景索引
    scene_indices = [int(x.strip()) for x in args.scene_indices.split(',')]
    
    # 获取所有可用场景
    available_scenes = sorted(os.listdir(args.scene_dir))
    
    # 验证索引
    invalid_indices = [i for i in scene_indices if i >= len(available_scenes)]
    if invalid_indices:
        print(f"[WARNING] Invalid indices: {invalid_indices}")
        print(f"[WARNING] Max valid index is {len(available_scenes)-1}")
        scene_indices = [i for i in scene_indices if i < len(available_scenes)]
        if not scene_indices:
            print("[ERROR] No valid scene indices!")
            sys.exit(1)
    
    # 为每个场景计算 num_episodes（如果启用自动计算）
    scene_episodes = {}
    if args.use_npy_episodes:
        print("\n[INFO] 正在从 .npy 文件计算每个场景的 num_episodes...")
        for scene_index in scene_indices:
            scene_name = available_scenes[scene_index]
            num_episodes = get_num_episodes_from_npy(args.scene_dir, scene_name)
            if num_episodes is not None:
                scene_episodes[scene_index] = num_episodes
                print(f"  场景 {scene_name}: {num_episodes} episodes (从 .npy 文件计算)")
            else:
                # 如果找不到 .npy 文件，使用默认值或用户指定的值
                default_episodes = args.num_episodes if args.num_episodes is not None else 10
                scene_episodes[scene_index] = default_episodes
                print(f"  场景 {scene_name}: {default_episodes} episodes (使用默认值，未找到 .npy 文件)")
    
    # 显示测试计划
    print("\n" + "="*80)
    print("批量场景测试计划")
    print("="*80)
    print(f"场景目录: {args.scene_dir}")
    print(f"可用场景总数: {len(available_scenes)}")
    print(f"要测试的场景索引: {scene_indices}")
    print(f"场景名称: {[available_scenes[i] for i in scene_indices]}")
    if args.use_npy_episodes:
        print(f"\n每个场景的回合数（从 .npy 文件自动计算）:")
        for scene_index in scene_indices:
            scene_name = available_scenes[scene_index]
            episodes = scene_episodes.get(scene_index, args.num_episodes or 10)
            print(f"  [{scene_index}] {scene_name}: {episodes} episodes")
    else:
        default_episodes = args.num_episodes if args.num_episodes is not None else 10
        print(f"每个场景回合数: {default_episodes}")
    print(f"并行环境数: {args.num_envs}")
    print(f"机器人速度: {args.speed} m/s")
    print(f"停止阈值: {args.stop_threshold}")
    print(f"服务器端口: {args.port}")
    print("="*80)
    
    # 确认
    if not args.dry_run:
        input("\n按 Enter 开始测试，或 Ctrl+C 取消...")
    
    # 测试结果统计
    results = {
        'total': len(scene_indices),
        'success': 0,
        'failed': 0,
        'scenes': {}
    }
    
    # 测试每个场景
    start_time = datetime.now()
    
    for idx, scene_index in enumerate(scene_indices):
        scene_name = available_scenes[scene_index]
        
        # 获取该场景的 num_episodes
        if args.use_npy_episodes and scene_index in scene_episodes:
            num_episodes = scene_episodes[scene_index]
        else:
            num_episodes = args.num_episodes if args.num_episodes is not None else 10
        
        print(f"\n{'#'*80}")
        print(f"# 进度: {idx+1}/{len(scene_indices)} - 测试场景: {scene_name}")
        print(f"# 该场景的 num_episodes: {num_episodes}")
        print(f"{'#'*80}\n")
        
        # 测试场景
        success, actual_scene_name, stdout, stderr = test_single_scene(
            args.scene_dir,
            scene_index,
            args.num_envs,
            num_episodes,
            args.speed,
            args.stop_threshold,
            args.port
        )
        
        if success:
            results['success'] += 1
            print(f"[SUCCESS] 场景 {actual_scene_name} 测试完成")
        else:
            results['failed'] += 1
            print(f"[FAILED] 场景 {actual_scene_name} 测试失败")
        
        results['scenes'][scene_name] = {
            'index': scene_index,
            'success': success,
            'stdout': stdout,
            'stderr': stderr
        }
        
        # 短暂停
        if idx < len(scene_indices) - 1:
            print(f"\n[INFO] 等待 3 秒后测试下一个场景...")
            import time
            time.sleep(3)
    
    # 打印总结
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds() / 60  # 分钟
    
    print(f"\n{'='*80}")
    print("测试总结")
    print("="*80)
    print(f"总场景数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    print(f"成功率: {results['success']/results['total']*100:.1f}%")
    print(f"总用时: {total_duration:.1f} 分钟")
    print("="*80)
    
    # 详细结果
    print("\n各场景测试结果:")
    print("-"*80)
    for scene_name, scene_result in results['scenes'].items():
        status = "✓ 成功" if scene_result['success'] else "✗ 失败"
        print(f"{status}  {scene_name} (索引 {scene_result['index']})")
    print("-"*80)

if __name__ == "__main__":
    main()

