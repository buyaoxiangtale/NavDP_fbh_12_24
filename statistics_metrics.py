#!/usr/bin/env python3
"""
统计 pointgoal_navdp_scene_1231 目录下所有场景的评估指标
计算：SR (Success Rate), SPL (Success weighted by Path Length), 平均路径长度
"""

import os
import csv
import argparse
import numpy as np
from pathlib import Path

def load_metrics(csv_path):
    """
    加载 metric.csv 文件
    
    返回: (success_list, spl_list, distance_list)
    """
    success_list = []
    spl_list = []
    distance_list = []
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                success = float(row['success'])
                spl = float(row['spl'])
                distance = float(row['distance'])
                
                success_list.append(success)
                spl_list.append(spl)
                distance_list.append(distance)
    except Exception as e:
        print(f"[WARNING] 无法读取 {csv_path}: {e}")
        return None, None, None
    
    return success_list, spl_list, distance_list

def calculate_path_length(success, spl, euclidean_distance):
    """
    从 success, spl, distance 计算实际路径长度
    
    根据公式：spl = min(euclidean / trajectory_length, 1) * success
    
    如果 success = 1:
        - 如果 spl < 1: trajectory_length = euclidean / spl
        - 如果 spl = 1: trajectory_length <= euclidean (取 euclidean 作为下界)
    如果 success = 0:
        - spl = 0，无法准确计算路径长度
    """
    if success > 0.5:  # 成功
        if spl > 0 and spl < 1:
            return euclidean_distance / spl
        elif spl >= 1:
            # spl = 1 表示路径长度 <= 欧氏距离，取欧氏距离作为估计
            return euclidean_distance
        else:
            return None
    else:  # 失败
        # 失败时无法准确计算，返回 None
        return None

def calculate_statistics(success_list, spl_list, distance_list):
    """
    计算统计指标
    
    返回: (sr, avg_spl, avg_path_length, avg_distance)
    """
    if not success_list or len(success_list) == 0:
        return None, None, None, None
    
    success_array = np.array(success_list)
    spl_array = np.array(spl_list)
    distance_array = np.array(distance_list)
    
    # SR (Success Rate) - 成功率
    sr = np.mean(success_array)
    
    # 平均 SPL
    avg_spl = np.mean(spl_array)
    
    # 平均欧氏距离
    avg_distance = np.mean(distance_array)
    
    # 计算平均路径长度（只计算成功的 episode）
    path_lengths = []
    for i in range(len(success_list)):
        path_len = calculate_path_length(success_list[i], spl_list[i], distance_list[i])
        if path_len is not None:
            path_lengths.append(path_len)
    
    avg_path_length = np.mean(path_lengths) if path_lengths else None
    
    return sr, avg_spl, avg_path_length, avg_distance

def process_directory(root_dir):
    """
    处理目录下所有场景的 metric.csv 文件
    
    返回: 统计结果字典
    """
    results = {}
    
    root_path = Path(root_dir)
    if not root_path.exists():
        print(f"[ERROR] 目录不存在: {root_dir}")
        return results
    
    # 遍历所有子目录
    scene_dirs = sorted([d for d in root_path.iterdir() if d.is_dir()])
    
    print("="*100)
    print(f"处理目录: {root_dir}")
    print(f"找到 {len(scene_dirs)} 个场景目录")
    print("="*100)
    
    for scene_dir in scene_dirs:
        scene_name = scene_dir.name
        metric_file = scene_dir / "metric.csv"
        
        if not metric_file.exists():
            print(f"[WARNING] {scene_name}: 未找到 metric.csv")
            continue
        
        # 加载指标
        success_list, spl_list, distance_list = load_metrics(metric_file)
        
        if success_list is None:
            continue
        
        # 计算统计指标
        sr, avg_spl, avg_path_length, avg_distance = calculate_statistics(
            success_list, spl_list, distance_list
        )
        
        results[scene_name] = {
            'sr': sr,
            'avg_spl': avg_spl,
            'avg_path_length': avg_path_length,
            'avg_distance': avg_distance,
            'num_episodes': len(success_list),
            'num_success': int(np.sum(success_list))
        }
        
        print(f"\n场景: {scene_name}")
        print(f"  Episode 数量: {len(success_list)}")
        print(f"  成功次数: {results[scene_name]['num_success']}")
        print(f"  SR (成功率): {sr:.4f} ({sr*100:.2f}%)")
        print(f"  平均 SPL: {avg_spl:.4f}")
        if avg_path_length is not None:
            print(f"  平均路径长度: {avg_path_length:.4f} m")
        print(f"  平均欧氏距离: {avg_distance:.4f} m")
    
    return results

def calculate_overall_statistics(results):
    """
    计算总体统计指标（考虑所有 episode 的加权平均）
    
    返回: 汇总统计字典
    """
    if not results:
        return None
    
    # 收集所有 episode 的数据（用于加权计算）
    all_successes = []
    all_spls = []
    all_path_lengths = []
    all_distances = []
    
    # 按场景统计
    total_episodes = 0
    total_success = 0
    
    for scene_name, stats in results.items():
        # 需要重新加载每个场景的详细数据来计算加权平均
        # 这里我们使用场景级别的统计
        total_episodes += stats['num_episodes']
        total_success += stats['num_success']
    
    # 方法1：场景级别的平均（每个场景权重相等）
    all_sr = [r['sr'] for r in results.values()]
    all_spl = [r['avg_spl'] for r in results.values()]
    all_path_lengths_scene = [r['avg_path_length'] for r in results.values() if r['avg_path_length'] is not None]
    all_distances_scene = [r['avg_distance'] for r in results.values()]
    
    # 方法2：Episode 级别的加权平均（按 episode 数量加权）
    weighted_sr = 0
    weighted_spl = 0
    weighted_path_length = 0
    weighted_distance = 0
    total_weight = 0
    total_path_weight = 0
    
    for scene_name, stats in results.items():
        weight = stats['num_episodes']
        weighted_sr += stats['sr'] * weight
        weighted_spl += stats['avg_spl'] * weight
        weighted_distance += stats['avg_distance'] * weight
        total_weight += weight
        
        if stats['avg_path_length'] is not None:
            # 只计算有路径长度的场景
            path_weight = stats['num_episodes']
            weighted_path_length += stats['avg_path_length'] * path_weight
            total_path_weight += path_weight
    
    # 计算加权平均
    overall_sr_weighted = weighted_sr / total_weight if total_weight > 0 else 0
    overall_spl_weighted = weighted_spl / total_weight if total_weight > 0 else 0
    overall_distance_weighted = weighted_distance / total_weight if total_weight > 0 else 0
    overall_path_length_weighted = weighted_path_length / total_path_weight if total_path_weight > 0 else None
    
    # 计算总体成功率（所有 episode 的成功率）
    overall_sr_episode = total_success / total_episodes if total_episodes > 0 else 0
    
    summary = {
        'total_scenes': len(results),
        'total_episodes': total_episodes,
        'total_success': total_success,
        'overall_sr_episode': overall_sr_episode,  # Episode 级别的总体成功率
        'overall_sr_scene_avg': np.mean(all_sr),  # 场景级别的平均成功率
        'overall_sr_scene_weighted': overall_sr_weighted,  # 场景级别的加权平均成功率
        'overall_spl_scene_avg': np.mean(all_spl),  # 场景级别的平均 SPL
        'overall_spl_scene_weighted': overall_spl_weighted,  # 场景级别的加权平均 SPL
        'overall_path_length_scene_avg': np.mean(all_path_lengths_scene) if all_path_lengths_scene else None,
        'overall_path_length_scene_weighted': overall_path_length_weighted,
        'overall_distance_scene_avg': np.mean(all_distances_scene),
        'overall_distance_scene_weighted': overall_distance_weighted
    }
    
    return summary

def print_summary(results):
    """
    打印汇总统计
    """
    if not results:
        print("\n[ERROR] 没有找到任何结果")
        return None
    
    print("\n" + "="*100)
    print("总体汇总统计")
    print("="*100)
    
    # 计算总体统计
    summary = calculate_overall_statistics(results)
    
    if summary is None:
        return None
    
    print(f"\n【基本统计】")
    print(f"  总场景数: {summary['total_scenes']}")
    print(f"  总 Episode 数: {summary['total_episodes']}")
    print(f"  总成功次数: {summary['total_success']}")
    
    print(f"\n【成功率 (SR)】")
    print(f"  Episode 级别总体 SR: {summary['overall_sr_episode']:.4f} ({summary['overall_sr_episode']*100:.2f}%)")
    print(f"  场景级别平均 SR: {summary['overall_sr_scene_avg']:.4f} ({summary['overall_sr_scene_avg']*100:.2f}%)")
    print(f"  场景级别加权平均 SR: {summary['overall_sr_scene_weighted']:.4f} ({summary['overall_sr_scene_weighted']*100:.2f}%)")
    
    print(f"\n【SPL (Success weighted by Path Length)】")
    print(f"  场景级别平均 SPL: {summary['overall_spl_scene_avg']:.4f}")
    print(f"  场景级别加权平均 SPL: {summary['overall_spl_scene_weighted']:.4f}")
    
    print(f"\n【路径长度】")
    if summary['overall_path_length_scene_avg'] is not None:
        print(f"  场景级别平均路径长度: {summary['overall_path_length_scene_avg']:.4f} m")
    if summary['overall_path_length_scene_weighted'] is not None:
        print(f"  场景级别加权平均路径长度: {summary['overall_path_length_scene_weighted']:.4f} m")
    
    print(f"\n【欧氏距离】")
    print(f"  场景级别平均欧氏距离: {summary['overall_distance_scene_avg']:.4f} m")
    print(f"  场景级别加权平均欧氏距离: {summary['overall_distance_scene_weighted']:.4f} m")
    
    # 打印详细表格
    print("\n" + "="*100)
    print("详细结果表格")
    print("="*100)
    print(f"{'场景名称':<60} {'SR':<10} {'平均SPL':<12} {'平均路径长度':<15} {'Episodes':<10}")
    print("-"*100)
    
    for scene_name, stats in sorted(results.items()):
        path_len_str = f"{stats['avg_path_length']:.4f}" if stats['avg_path_length'] is not None else "N/A"
        print(f"{scene_name:<60} {stats['sr']:<10.4f} {stats['avg_spl']:<12.4f} {path_len_str:<15} {stats['num_episodes']:<10}")
    
    return summary

def save_results(results, output_file):
    """
    保存结果到 CSV 文件
    """
    if not results:
        return
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['场景名称', 'SR', '平均SPL', '平均路径长度(m)', '平均欧氏距离(m)', 'Episode数', '成功次数'])
        
        # 写入数据
        for scene_name, stats in sorted(results.items()):
            path_len = stats['avg_path_length'] if stats['avg_path_length'] is not None else ''
            writer.writerow([
                scene_name,
                f"{stats['sr']:.6f}",
                f"{stats['avg_spl']:.6f}",
                f"{path_len:.6f}" if path_len != '' else '',
                f"{stats['avg_distance']:.6f}",
                stats['num_episodes'],
                stats['num_success']
            ])
    
    print(f"\n[INFO] 详细结果已保存到: {output_path.absolute()}")

def save_summary(summary, output_file):
    """
    保存汇总统计到 CSV 文件
    """
    if summary is None:
        return
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['指标', '值', '说明'])
        
        # 写入汇总数据
        writer.writerow(['总场景数', summary['total_scenes'], '测试的场景总数'])
        writer.writerow(['总Episode数', summary['total_episodes'], '所有场景的episode总数'])
        writer.writerow(['总成功次数', summary['total_success'], '所有场景的成功episode总数'])
        writer.writerow(['', '', ''])
        writer.writerow(['Episode级别总体SR', f"{summary['overall_sr_episode']:.6f}", 
                        f"总体成功率 = 总成功次数 / 总Episode数 ({summary['overall_sr_episode']*100:.2f}%)"])
        writer.writerow(['场景级别平均SR', f"{summary['overall_sr_scene_avg']:.6f}",
                        f"所有场景成功率的平均值 ({summary['overall_sr_scene_avg']*100:.2f}%)"])
        writer.writerow(['场景级别加权平均SR', f"{summary['overall_sr_scene_weighted']:.6f}",
                        f"按episode数量加权的场景成功率平均值 ({summary['overall_sr_scene_weighted']*100:.2f}%)"])
        writer.writerow(['', '', ''])
        writer.writerow(['场景级别平均SPL', f"{summary['overall_spl_scene_avg']:.6f}",
                        '所有场景平均SPL的算术平均值'])
        writer.writerow(['场景级别加权平均SPL', f"{summary['overall_spl_scene_weighted']:.6f}",
                        '按episode数量加权的场景平均SPL'])
        writer.writerow(['', '', ''])
        if summary['overall_path_length_scene_avg'] is not None:
            writer.writerow(['场景级别平均路径长度', f"{summary['overall_path_length_scene_avg']:.6f}",
                            '所有场景平均路径长度的算术平均值 (m)'])
        if summary['overall_path_length_scene_weighted'] is not None:
            writer.writerow(['场景级别加权平均路径长度', f"{summary['overall_path_length_scene_weighted']:.6f}",
                            '按episode数量加权的场景平均路径长度 (m)'])
        writer.writerow(['', '', ''])
        writer.writerow(['场景级别平均欧氏距离', f"{summary['overall_distance_scene_avg']:.6f}",
                        '所有场景平均欧氏距离的算术平均值 (m)'])
        writer.writerow(['场景级别加权平均欧氏距离', f"{summary['overall_distance_scene_weighted']:.6f}",
                        '按episode数量加权的场景平均欧氏距离 (m)'])
    
    print(f"[INFO] 汇总统计已保存到: {output_path.absolute()}")

def main():
    parser = argparse.ArgumentParser(description="统计评估指标")
    parser.add_argument("--root_dir", type=str,
                       default="./pointgoal_navdp_scene_1231",
                       help="结果目录路径")
    parser.add_argument("--output", type=str,
                       default="./statistics_results.csv",
                       help="输出 CSV 文件路径")
    
    args = parser.parse_args()
    
    # 处理目录
    results = process_directory(args.root_dir)
    
    # 打印汇总
    summary = print_summary(results)
    
    # 保存详细结果
    if results:
        save_results(results, args.output)
        
        # 保存汇总统计
        if summary is not None:
            summary_file = str(Path(args.output).with_name(Path(args.output).stem + "_summary.csv"))
            save_summary(summary, summary_file)

if __name__ == "__main__":
    main()



# python statistics_metrics.py \
#     --root_dir ./pointgoal_navdp_scene_1231 \
#     --output ./statistics_results.csv

# python statistics_metrics.py \
#     --root_dir ./pointgoal_iplanner_scene_1231 \
#     --output ./statistics_iplanner_results.csv