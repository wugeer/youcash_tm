#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import time
from datetime import datetime
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from sqlalchemy.orm import Session

from app.core.db import SessionLocal

# 设置日志
logger = logging.getLogger(__name__)

# 定义类型变量
F = TypeVar('F', bound=Callable[..., Any])

# 同步状态常量
SYNC_STATUS = {
    'SUCCESS': '成功',
    'FAILED': '失败',
    'RETRYING': '重试中',
}


class SyncRecord:
    """同步记录辅助类，用于记录同步操作的详细信息"""
    
    def __init__(self, module_name: str, record_id: int, action: str):
        self.module_name = module_name  # 模块名称，如 "HDFS配额", "表权限" 等
        self.record_id = record_id      # 记录ID
        self.action = action            # 动作，如 "创建", "更新", "批量导入" 等
        self.start_time = datetime.now()
        self.end_time = None
        self.status = None
        self.attempts = 0
        self.error_message = None
    
    def start(self) -> None:
        """开始记录同步操作"""
        self.start_time = datetime.now()
        logger.info(f"[{self.module_name}] 开始{self.action}同步: ID={self.record_id}, 时间={self.start_time}")
    
    def success(self) -> None:
        """标记同步操作成功"""
        self.end_time = datetime.now()
        self.status = SYNC_STATUS['SUCCESS']
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"[{self.module_name}] {self.action}同步成功: ID={self.record_id}, 耗时={duration:.2f}秒")
    
    def fail(self, error: Exception) -> None:
        """标记同步操作失败"""
        self.end_time = datetime.now()
        self.status = SYNC_STATUS['FAILED']
        self.error_message = str(error)
        duration = (self.end_time - self.start_time).total_seconds()
        logger.error(f"[{self.module_name}] {self.action}同步失败: ID={self.record_id}, 耗时={duration:.2f}秒, 错误={self.error_message}")
    
    def retry(self, attempt: int, max_attempts: int, error: Exception) -> None:
        """记录重试操作"""
        self.attempts = attempt
        self.status = SYNC_STATUS['RETRYING']
        self.error_message = str(error)
        logger.warning(f"[{self.module_name}] {self.action}同步重试: ID={self.record_id}, 尝试={attempt}/{max_attempts}, 错误={self.error_message}")


def with_sync_retry(max_attempts: int = 3, retry_delay: int = 2):
    """同步函数重试装饰器
    
    为同步函数添加重试逻辑和日志记录
    
    参数:
        max_attempts: 最大尝试次数，默认为3次
        retry_delay: 重试间隔时间(秒)，默认为2秒
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 提取模块名、记录ID和操作类型
            module_name = kwargs.get('module_name', '未知模块')
            record_id = kwargs.get('record_id', args[0] if args else 0)
            action = kwargs.get('action', '同步')
            
            # 创建同步记录
            sync_record = SyncRecord(module_name, record_id, action)
            
            # 获取数据库会话 - 如果没有传入则创建一个新的
            db = kwargs.get('db')
            local_db = False
            if db is None:
                db = SessionLocal()
                kwargs['db'] = db
                local_db = True
            
            attempt = 0
            last_error = None
            
            while attempt < max_attempts:
                attempt += 1
                try:
                    if attempt == 1:
                        sync_record.start()
                    else:
                        sync_record.retry(attempt, max_attempts, last_error)
                    
                    result = func(*args, **kwargs)
                    sync_record.success()
                    
                    # 如果是本地创建的数据库会话，关闭它
                    if local_db:
                        db.close()
                    
                    return result
                
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts:
                        # 重试前等待一段时间
                        time.sleep(retry_delay)
                    else:
                        sync_record.fail(e)
                        # 如果是本地创建的数据库会话，关闭它
                        if local_db:
                            db.close()
                        raise
            
            # 这里正常不会到达，但为了类型检查完整性
            raise last_error
        
        return cast(F, wrapper)
    
    return decorator
