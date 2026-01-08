#!/usr/bin/env python3
"""
为 scene_1231 目录下所有子文件夹中的 USD 文件添加碰撞网格
"""

import os
import sys
from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf

def add_collision_to_mesh(prim):
    """
    为 Mesh prim 添加碰撞属性
    """
    if not prim.IsA(UsdGeom.Mesh):
        return False
    
    # 检查是否已经有 CollisionAPI
    collision_api = UsdPhysics.CollisionAPI(prim)
    if collision_api:
        # 如果已经有，检查是否需要更新
        return True
    
    # 添加 CollisionAPI
    collision_api = UsdPhysics.CollisionAPI.Apply(prim)
    if collision_api:
        # 设置碰撞属性
        collision_api.CreateCollisionEnabledAttr(True)
        return True
    
    return False

def ensure_scene_structure(stage):
    """
    确保 USD 文件有 /World/Scene 节点结构（TerrainImporter 需要）
    并在 /World/Scene 下创建一个包含所有 Mesh 的引用结构
    """
    created = False
    
    # 检查 /World 节点
    world_prim = stage.GetPrimAtPath("/World")
    if not world_prim.IsValid():
        world_prim = stage.DefinePrim("/World", "Xform")
        print(f"[INFO] 创建了 /World 节点")
        created = True
    
    # 检查 /World/Scene 节点
    scene_prim = stage.GetPrimAtPath("/World/Scene")
    if not scene_prim.IsValid():
        scene_prim = stage.DefinePrim("/World/Scene", "Xform")
        print(f"[INFO] 创建了 /World/Scene 节点")
        created = True
    
    # 检查 /World/Scene/terrain 节点
    terrain_prim = stage.GetPrimAtPath("/World/Scene/terrain")
    if not terrain_prim.IsValid():
        terrain_prim = stage.DefinePrim("/World/Scene/terrain", "Xform")
        print(f"[INFO] 创建了 /World/Scene/terrain 节点")
        created = True
        
        # 在 /World/Scene/terrain 下创建一个引用所有 Mesh 的节点
        # 使用 Xform 来组织所有有碰撞的 Mesh
        # 注意：我们不移动 Mesh，只是确保 /World/Scene 下有碰撞网格
        
        # 查找所有有碰撞的 Mesh，确保它们在 /World/Scene 的子树中
        # 实际上，TerrainImporter 会在整个 USD 文件中查找碰撞网格
        # 所以我们只需要确保 /World/Scene 存在即可
        pass
    
    return created

def add_collision_to_usd(usd_file_path, backup=True):
    """
    为 USD 文件中的所有 Mesh 添加碰撞属性
    
    Args:
        usd_file_path: USD 文件路径
        backup: 是否创建备份
    """
    if not os.path.exists(usd_file_path):
        print(f"[ERROR] 文件不存在: {usd_file_path}")
        return False
    
    print(f"\n处理文件: {usd_file_path}")
    
    # 创建备份
    if backup:
        backup_path = usd_file_path + ".backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(usd_file_path, backup_path)
            print(f"[INFO] 已创建备份: {backup_path}")
    
    # 打开 USD 文件
    try:
        stage = Usd.Stage.Open(usd_file_path)
        if not stage:
            print(f"[ERROR] 无法打开文件: {usd_file_path}")
            return False
    except Exception as e:
        print(f"[ERROR] 打开文件失败: {usd_file_path}, 错误: {e}")
        return False
    
    # 确保有 /World/Scene 结构
    scene_created = ensure_scene_structure(stage)
    
    # 统计信息
    mesh_count = 0
    collision_added = 0
    collision_existing = 0
    
    # 遍历所有 prim
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            mesh_count += 1
            # 检查是否已有碰撞
            existing_collision = UsdPhysics.CollisionAPI(prim)
            if existing_collision:
                collision_existing += 1
            else:
                # 添加碰撞
                if add_collision_to_mesh(prim):
                    collision_added += 1
    
    # 确保所有 Mesh 都有碰撞
    if collision_added > 0 or collision_existing < mesh_count:
        # 再次遍历，确保所有 Mesh 都有碰撞
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                collision_api = UsdPhysics.CollisionAPI(prim)
                if not collision_api:
                    add_collision_to_mesh(prim)
                    collision_added += 1
    
    # 保存修改（如果有任何更改，包括创建 Scene 结构）
    needs_save = collision_added > 0 or scene_created
    
    if needs_save:
        try:
            stage.GetRootLayer().Save()
            print(f"[SUCCESS] 已保存修改: {usd_file_path}")
            print(f"  - Mesh 总数: {mesh_count}")
            print(f"  - 已有碰撞: {collision_existing}")
            if collision_added > 0:
                print(f"  - 新添加碰撞: {collision_added}")
            if scene_created:
                print(f"  - 已创建 /World/Scene 结构")
            return True
        except Exception as e:
            print(f"[ERROR] 保存文件失败: {usd_file_path}, 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"[INFO] 所有 Mesh 已有碰撞属性，无需修改")
        print(f"  - Mesh 总数: {mesh_count}")
        print(f"  - 已有碰撞: {collision_existing}")
        return True

def process_directory(root_dir, pattern="*_room_isaacsim.usd"):
    """
    处理目录下所有匹配的 USD 文件
    
    Args:
        root_dir: 根目录路径
        pattern: 文件名模式（用于匹配）
    """
    import fnmatch
    
    processed = 0
    success = 0
    failed = 0
    
    print("="*80)
    print(f"开始处理目录: {root_dir}")
    print(f"文件模式: {pattern}")
    print("="*80)
    
    # 遍历所有子目录
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            # 匹配 USD 文件
            if fnmatch.fnmatch(file, pattern) or file.endswith('.usd'):
                usd_file_path = os.path.join(subdir, file)
                processed += 1
                
                if add_collision_to_usd(usd_file_path):
                    success += 1
                else:
                    failed += 1
    
    print("\n" + "="*80)
    print("处理完成")
    print("="*80)
    print(f"总文件数: {processed}")
    print(f"成功: {success}")
    print(f"失败: {failed}")
    print("="*80)
    
    return success, failed

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="为 USD 文件添加碰撞网格")
    parser.add_argument("--root_dir", type=str, 
                       default="/home/ubuntu/fengbh/NavDP/scene_1231",
                       help="根目录路径")
    parser.add_argument("--pattern", type=str,
                       default="*_room_isaacsim.usd",
                       help="文件名匹配模式")
    parser.add_argument("--no-backup", action="store_true",
                       help="不创建备份文件")
    parser.add_argument("--single-file", type=str,
                       help="只处理单个文件（用于测试）")
    
    args = parser.parse_args()
    
    if args.single_file:
        # 处理单个文件
        add_collision_to_usd(args.single_file, backup=not args.no_backup)
    else:
        # 处理整个目录
        process_directory(args.root_dir, args.pattern)

if __name__ == "__main__":
    main()

