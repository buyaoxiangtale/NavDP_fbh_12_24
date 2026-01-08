#!/bin/bash
# 批量测试多个场景

SCENE_DIR="/home/ubuntu/fengbh/NavDP/scene_1231"
NUM_ENVS=1
# NUM_EPISODES 将从 .npy 文件自动计算（数据条数 * 3）
PORT=9222
SPEED=0.5
STOP_THRESHOLD=-0.3

# 要测试的场景索引（从调试输出中获取）
SCENE_INDICES=(0 1 2 3 4 5 6 7 8 9 10 11 12)

echo "======================================"
echo "Batch Scene Testing"
echo "======================================"
echo "Scene directory: $SCENE_DIR"
echo "Scenes to test: ${SCENE_INDICES[@]}"
echo "Episodes per scene: $NUM_EPISODES"
echo "======================================"
echo ""

# 遍历所有场景
for scene_idx in "${SCENE_INDICES[@]}"; do
    echo ""
    echo "======================================"
    echo "Testing Scene Index: $scene_idx"
    echo "======================================"
    echo ""
    
    # 获取场景名称
    SCENE_NAME=$(python3 -c "
import os
scenes = sorted(os.listdir('$SCENE_DIR'))
if $scene_idx < len(scenes):
    print(scenes[$scene_idx])
else:
    print('')
")
    
    if [ -z "$SCENE_NAME" ]; then
        echo "[ERROR] Invalid scene index: $scene_idx"
        continue
    fi
    
    # 查找 .npy 文件并计算 num_episodes
    NPY_FILE="$SCENE_DIR/$SCENE_NAME/${SCENE_NAME}_pointgoal_pairs.npy"
    
    if [ -f "$NPY_FILE" ]; then
        # 从 .npy 文件计算 num_episodes = 数据条数 * 3
        NUM_EPISODES=$(python3 -c "
import numpy as np
try:
    data = np.load('$NPY_FILE')
    num_pairs = data.shape[0] if len(data.shape) > 0 else len(data)
    num_episodes = num_pairs * 3
    print(int(num_episodes))
except Exception as e:
    print(10)  # 默认值
")
        echo "[INFO] 从 .npy 文件计算 num_episodes: $NUM_EPISODES"
    else
        # 如果找不到 .npy 文件，使用默认值
        NUM_EPISODES=10
        echo "[WARNING] 未找到 .npy 文件，使用默认 num_episodes: $NUM_EPISODES"
    fi
    
    # 运行测试
    python eval_pointgoal_wheeled.py \
        --scene_dir "$SCENE_DIR" \
        --scene_index "$scene_idx" \
        --num_envs "$NUM_ENVS" \
        --num_episodes "$NUM_EPISODES" \
        --speed "$SPEED" \
        --stop_threshold "$STOP_THRESHOLD" \
        --port "$PORT"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo "[ERROR] Scene $scene_idx failed with exit code $EXIT_CODE"
    else
        echo "[SUCCESS] Scene $scene_idx completed"
    fi
    
    echo ""
    sleep 2  # 短暂避免端口冲突
done

echo ""
echo "======================================"
echo "All scene tests completed!"
echo "======================================"

