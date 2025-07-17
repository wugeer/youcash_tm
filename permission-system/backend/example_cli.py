#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import argparse
import logging
import os
from app.utils.log_config import CompressedTimedRotatingFileHandler

# 配置日志
# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 创建日志格式器
formatter = logging.Formatter(
    '%(asctime)s - CLI - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# 创建压缩滚动文件处理器
log_file = os.path.join(log_dir, 'cli.log')
file_handler = CompressedTimedRotatingFileHandler(
    log_file,
    when='D',           # 每天滚动
    interval=1,         # 每1天
    backupCount=30,     # 保留30个备份
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# 配置日志记录器
logger = logging.getLogger("cli")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def main():
    """
    示例CLI脚本，用于处理权限同步操作
    接收一个JSON字符串作为参数，解析后执行相应的操作
    """
    logger.info("启动权限同步CLI脚本...")
    
    if len(sys.argv) < 2:
        logger.error("缺少参数，需要一个JSON字符串作为参数")
        sys.exit(1)
    
    try:
        # 解析传入的JSON参数
        logger.debug(f"参数内容: {sys.argv[1]}")
        payload = json.loads(sys.argv[1])
        action = payload.get("action", "")
        logger.info(f"解析到请求动作: {action}")
        
        # 根据action执行不同的操作
        if action == "sync_table_permissions":
            # 这里处理批量表权限同步通知
            records_count = payload.get("total", 0)
            logger.info(f"正在批量同步所有表权限，共{records_count}条记录...")
            logger.debug(f"表权限批量同步操作启动")
            
        elif action == "sync_single_table_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name:
                logger.error("缺少必要的db_name或table_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的单个表权限同步逻辑
            logger.info(f"正在同步表权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加单条同步的具体实现
            logger.debug(f"单条表权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}]")
            
        elif action == "sync_delete_table_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name:
                logger.error("缺少必要的db_name或table_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的表权限删除同步逻辑
            logger.info(f"正在同步删除表权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加删除同步的具体实现
            logger.debug(f"删除表权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}]")
            
        elif action == "sync_row_permissions":
            # 这里处理批量行权限同步通知
            records_count = payload.get("total", 0)
            logger.info(f"正在批量同步所有行权限，共{records_count}条记录...")
            logger.debug(f"行权限批量同步操作启动")
            
        elif action == "sync_single_row_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            row_filter = payload.get("row_filter")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name:
                logger.error("缺少必要的db_name或table_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的单个行权限同步逻辑
            logger.info(f"正在同步行权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 行筛选: [{row_filter if len(str(row_filter)) <= 50 else str(row_filter)[:50]+'...'}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加单条同步的具体实现
            logger.debug(f"单条行权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}]")
            
        elif action == "sync_delete_row_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name:
                logger.error("缺少必要的db_name或table_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的行权限删除同步逻辑
            logger.info(f"正在同步删除行权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加删除同步的具体实现
            logger.debug(f"删除行权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}]")
            
        elif action == "sync_column_permissions":
            # 这里处理批量字段权限同步通知
            records_count = payload.get("total", 0)
            logger.info(f"正在批量同步所有字段权限，共{records_count}条记录...")
            logger.debug(f"字段权限批量同步操作启动")
            
        elif action == "sync_single_column_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            col_name = payload.get("col_name")
            mask_type = payload.get("mask_type")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name or not col_name:
                logger.error("缺少必要的db_name、table_name或col_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的单个字段权限同步逻辑
            logger.info(f"正在同步字段权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 字段: [{col_name}], 脱敏类型: [{mask_type}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加单条同步的具体实现
            logger.debug(f"单条字段权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 字段: [{col_name}]")
            
        elif action == "sync_delete_column_permission":
            # 获取关键字段
            permission_id = payload.get("id")
            db_name = payload.get("db_name")
            table_name = payload.get("table_name")
            column_name = payload.get("column_name")
            user_name = payload.get("user_name")
            role_name = payload.get("role_name")
            
            if not permission_id:
                logger.error("缺少必要的permission_id参数")
                sys.exit(1)
                
            if not db_name or not table_name or not column_name:
                logger.error("缺少必要的db_name、table_name或column_name参数")
                sys.exit(1)
                
            # 这里可以添加实际的字段权限删除同步逻辑
            logger.info(f"正在同步删除字段权限 ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 字段: [{column_name}], 用户: [{user_name}], 角色: [{role_name}]")
            # 这里添加删除同步的具体实现
            logger.debug(f"删除字段权限同步操作成功完成，ID: {permission_id}, 数据库: [{db_name}], 表: [{table_name}], 字段: [{column_name}]")
            
        elif action == "sync_hdfs_quotas":
            # 这里处理批量HDFS配额同步通知
            # 批量同步时不需要额外参数，因为后端会遍历所有记录
            records_count = payload.get("total", 0)
            logger.info(f"正在批量同步所有HDFS配额，共{records_count}条记录...")
            logger.debug(f"HDFS配额批量同步操作启动")
            
        elif action == "sync_single_hdfs_quota":
            # 这里可以添加实际的单个HDFS配额同步逻辑
            quota_id = payload.get("id")
            db_name = payload.get("db_name")
            hdfs_quota = payload.get("hdfs_quota")
            is_delete = payload.get("is_delete", False)  # 检查是否为删除操作
            
            if not quota_id:
                logger.error("缺少必要的quota_id参数")
                sys.exit(1)
                
            if not db_name or hdfs_quota is None:
                logger.error("缺少必要的db_name或hdfs_quota参数")
                sys.exit(1)
            
            if is_delete:
                # 处理删除操作
                logger.info(f"正在处理删除数据库[{db_name}]的HDFS配额, ID: {quota_id}...")
                # 这里添加实际的删除同步逻辑
                logger.debug(f"删除HDFS配额操作成功完成，ID: {quota_id}, 数据库: [{db_name}]")
            else:
                # 处理普通的同步操作
                logger.info(f"正在同步数据库[{db_name}]的HDFS配额（{hdfs_quota}GB）, ID: {quota_id}...")
                # 这里添加实际的同步逻辑
                logger.debug(f"单条HDFS配额同步操作成功完成，ID: {quota_id}, 数据库: [{db_name}], 配额: {hdfs_quota}GB")
            
        else:
            logger.error(f"未知操作：{action}")
            sys.exit(1)
        
        # 操作成功
        logger.info(f"同步操作 '{action}' 成功完成")
        sys.exit(0)
        
    except json.JSONDecodeError:
        logger.error("无效的JSON参数，请检查输入")
        logger.debug(f"无效的JSON内容: {sys.argv[1] if len(sys.argv) > 1 else 'None'}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"操作执行失败: {str(e)}")
        logger.exception("发生异常")
        sys.exit(1)

if __name__ == "__main__":
    main()
