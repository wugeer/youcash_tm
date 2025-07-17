#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import gzip
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    扩展TimedRotatingFileHandler，添加日志压缩功能
    使用gzip进行压缩，提供最佳的压缩率
    """
    
    def __init__(self, filename, when='D', interval=1, backupCount=30, 
                 encoding='utf-8', delay=False, utc=False, atTime=None):
        """
        初始化压缩日志处理器
        
        参数:
            filename: 日志文件路径
            when: 滚动间隔类型，'S'秒, 'M'分钟, 'H'小时, 'D'天, 'W'周, 'midnight'午夜
            interval: 滚动间隔
            backupCount: 保留的备份文件数量
            encoding: 文件编码
            delay: 是否延迟创建文件
            utc: 是否使用UTC时间
            atTime: 在指定时间滚动
        """
        super().__init__(
            filename, when, interval, backupCount, 
            encoding, delay, utc, atTime
        )
        # 设置后缀为.gz，表示gzip压缩
        self.suffix = "%Y-%m-%d_%H-%M-%S"
        self.ext = ".gz"
    
    def doRollover(self):
        """
        执行日志滚动并压缩
        """
        # 关闭当前日志文件
        if self.stream:
            self.stream.close()
            self.stream = None
            
        # 计算当前时间和滚动后的文件名
        current_time = int(time.time())
        dst_path_name = self.rotation_filename(
            f"{self.baseFilename}.{time.strftime(self.suffix, time.localtime(current_time))}"
        )
        
        # 如果目标文件已存在，先删除
        if os.path.exists(dst_path_name):
            os.remove(dst_path_name)
            
        # 重命名当前日志文件
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dst_path_name)
            
            # 压缩日志文件
            with open(dst_path_name, 'rb') as f_in:
                with gzip.open(f"{dst_path_name}{self.ext}", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩的滚动日志文件
            os.remove(dst_path_name)
        
        # 创建新的日志文件
        if not self.delay:
            self.stream = self._open()
            
        # 删除过旧的日志文件
        if self.backupCount > 0:
            # 获取所有.gz结尾的日志文件
            log_dir = os.path.dirname(self.baseFilename)
            base_name = os.path.basename(self.baseFilename)
            
            compressed_files = []
            for file in Path(log_dir).glob(f"{base_name}.*{self.ext}"):
                compressed_files.append(str(file))
                
            # 如果压缩日志文件数量超过备份数量，删除最旧的文件
            if len(compressed_files) > self.backupCount:
                compressed_files.sort()
                for i in range(len(compressed_files) - self.backupCount):
                    os.remove(compressed_files[i])


def setup_compressed_rotating_logger(logger_name, log_file, level=logging.INFO, 
                                    when='D', interval=1, backup_count=30,
                                    formatter=None):
    """
    配置带压缩功能的滚动日志记录器
    
    参数:
        logger_name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        when: 滚动间隔类型
        interval: 滚动间隔
        backup_count: 保留的备份文件数量
        formatter: 日志格式化器
    
    返回:
        配置好的日志记录器
    """
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建默认格式化器（如果未提供）
    if formatter is None:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 创建压缩滚动日志处理器
    handler = CompressedTimedRotatingFileHandler(
        log_file,
        when=when,
        interval=interval,
        backupCount=backup_count
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    
    # 获取日志记录器并添加处理器
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    
    return logger
