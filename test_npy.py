import numpy as np
from typing import Dict, List, Tuple, Optional

def parse_start_goal_pairs(file_path: str, index: Optional[int] = None) -> Dict:
    """
    解析起点-目标点对文件
    
    参数:
        file_path: .npy 文件路径
        index: 可选，如果指定则只返回第 index 个点对，否则返回所有点对
    
    返回:
        字典包含以下键:
        - 'data': numpy 数组，形状为 (N, 5)，N 为点对数量
        - 'num_pairs': 点对总数
        - 'start_points': 起点数组，形状为 (N, 2) 或 (2,) 如果指定了 index
        - 'goal_points': 目标点数组，形状为 (N, 2) 或 (2,) 如果指定了 index
        - 'orientations': 初始朝向数组，形状为 (N,) 或标量如果指定了 index
        - 'pair': 如果指定了 index，返回该点对的详细信息字典
    """
    # 加载 numpy 文件
    data = np.load(file_path)
    
    # 验证数据形状
    if len(data.shape) != 2 or data.shape[1] != 5:
        raise ValueError(f"文件格式错误: 期望形状为 (N, 5)，实际为 {data.shape}")
    
    num_pairs = data.shape[0]
    
    # 提取起点、目标点和朝向
    start_points = data[:, :2]  # [start_x, start_y]
    goal_points = data[:, 2:4]   # [goal_x, goal_y]
    orientations = data[:, 4]    # orientation
    
    result = {
        'data': data,
        'num_pairs': num_pairs,
        'start_points': start_points,
        'goal_points': goal_points,
        'orientations': orientations
    }
    
    # 如果指定了索引，返回单个点对的详细信息
    if index is not None:
        if index < 0 or index >= num_pairs:
            raise IndexError(f"索引 {index} 超出范围 [0, {num_pairs-1}]")
        
        result['pair'] = {
            'index': index,
            'start_point': start_points[index],
            'goal_point': goal_points[index],
            'orientation': orientations[index],
            'start_x': start_points[index][0],
            'start_y': start_points[index][1],
            'goal_x': goal_points[index][0],
            'goal_y': goal_points[index][1],
        }
    
    return result


def print_start_goal_pairs_info(file_path: str, max_display: int = 10):
    """
    打印起点-目标点对文件的详细信息
    
    参数:
        file_path: .npy 文件路径
        max_display: 最多显示的点对数量
    """
    result = parse_start_goal_pairs(file_path)
    
    print(f"文件路径: {file_path}")
    print(f"点对总数: {result['num_pairs']}")
    print(f"数据形状: {result['data'].shape}")
    print(f"\n前 {min(max_display, result['num_pairs'])} 个点对:")
    print("-" * 80)
    print(f"{'索引':<6} {'起点 (x, y)':<20} {'目标点 (x, y)':<20} {'朝向':<10}")
    print("-" * 80)
    
    for i in range(min(max_display, result['num_pairs'])):
        start = result['start_points'][i]
        goal = result['goal_points'][i]
        orient = result['orientations'][i]
        print(f"{i:<6} ({start[0]:>7.3f}, {start[1]:>7.3f})  "
              f"({goal[0]:>7.3f}, {goal[1]:>7.3f})  {orient:>8.3f}")
    
    if result['num_pairs'] > max_display:
        print(f"\n... 还有 {result['num_pairs'] - max_display} 个点对未显示")


# 使用示例
if __name__ == "__main__":
    # 示例 1: 解析整个文件
    file_path = "./asset_scenes/cluttered_easy/easy_0/pointgoal_start_goal_pairs.npy"
    
    # 打印文件信息
    print_start_goal_pairs_info(file_path, max_display=5)
    
    # 示例 2: 获取所有点对
    result = parse_start_goal_pairs(file_path)
    print(f"\n所有起点坐标范围:")
    print(f"  X: [{result['start_points'][:, 0].min():.3f}, {result['start_points'][:, 0].max():.3f}]")
    print(f"  Y: [{result['start_points'][:, 1].min():.3f}, {result['start_points'][:, 1].max():.3f}]")
    
    # 示例 3: 获取特定索引的点对
    pair_info = parse_start_goal_pairs(file_path, index=0)
    print(f"\n第 0 个点对详情:")
    print(f"  起点: ({pair_info['pair']['start_x']:.3f}, {pair_info['pair']['start_y']:.3f})")
    print(f"  目标: ({pair_info['pair']['goal_x']:.3f}, {pair_info['pair']['goal_y']:.3f})")
    print(f"  朝向: {pair_info['pair']['orientation']:.3f}")