"""
Logging utilities for the FractFlow project.

Provides standardized logging functions and formatting to ensure
consistent logging across the entire system.
"""

import logging
import inspect
import json
import sys
from typing import Any, Dict, Optional, Union

# ANSI颜色代码
COLORS = {
    'RESET': '\033[0m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    # 添加暗色系列
    'DARK_GRAY': '\033[90m',
    'DARK_RED': '\033[31;2m',
    'DARK_GREEN': '\033[32;2m',
    'DARK_YELLOW': '\033[33;2m',
    'DARK_BLUE': '\033[34;2m',
    'DARK_MAGENTA': '\033[35;2m',
    'DARK_CYAN': '\033[36;2m',
    'DARK_WHITE': '\033[37;2m',
}

# 为日志级别设置颜色
LEVEL_COLORS = {
    'DEBUG': COLORS['BLUE'],
    'INFO': COLORS['GREEN'],
    'WARNING': COLORS['YELLOW'],
    'ERROR': COLORS['RED'],
    'CRITICAL': COLORS['MAGENTA'] + COLORS['BOLD']
}

# 定义消息内容的颜色配置
MESSAGE_COLORS = {
    'DEBUG': COLORS['DARK_BLUE'],
    'INFO': COLORS['DARK_GREEN'],  # 让INFO级别消息变暗
    'WARNING': COLORS['DARK_YELLOW'],
    'ERROR': COLORS['RED'],  # 错误保持显眼
    'CRITICAL': COLORS['MAGENTA'],  # 关键错误保持显眼
}

class ColorFormatter(logging.Formatter):
    """格式化器，为日志添加颜色"""
    
    def format(self, record):
        # 保存原始级别名和消息
        levelname = record.levelname
        message = record.getMessage()
        
        # 如果不在终端环境中运行，不添加颜色
        if sys.stdout.isatty():
            # 为级别名添加颜色
            level_color = LEVEL_COLORS.get(levelname, COLORS['RESET'])
            record.levelname = f"{level_color}{levelname}{COLORS['RESET']}"
            
            # 为消息内容添加颜色（降低亮度）
            message_color = MESSAGE_COLORS.get(levelname, COLORS['RESET'])
            
            # 替换原始消息为带颜色的版本
            record.msg = f"{message_color}{record.msg}{COLORS['RESET']}"
            
        formatted = super().format(record)
        
        # 恢复原始级别名和消息，避免影响其他格式化器
        record.levelname = levelname
        record.msg = record.msg.replace(f"{message_color}", "").replace(f"{COLORS['RESET']}", "")
        return formatted

# Configure default logging format
DEFAULT_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(level: int = logging.INFO, use_colors: bool = True):
    """
    Configure logging with standard formatting.
    
    Args:
        level: The logging level to use
        use_colors: Whether to enable colored output
    """
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 移除所有现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 使用带颜色的格式化器 
    if use_colors and sys.stdout.isatty():
        formatter = ColorFormatter(
            fmt=DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    else:
        formatter = logging.Formatter(
            fmt=DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

def get_logger(name: Optional[str] = None):
    """
    Get a logger with the given name or the caller's module name.
    
    Args:
        name: Logger name (if None, uses caller's module name)
        
    Returns:
        A logger instance
    """
    if name is None:
        # Get the caller's module name
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "unknown"
    
    logger = logging.getLogger(name)
    return LoggerWrapper(logger)

class LoggerWrapper:
    """
    Wrapper around standard logger to provide improved formatting.
    """
    
    def __init__(self, logger):
        """
        Initialize the logger wrapper.
        
        Args:
            logger: The standard logger to wrap
        """
        self.logger = logger
        self.use_colors = sys.stdout.isatty()
    
    def _format_data(self, data: Union[Dict[str, Any], str]) -> str:
        """Format dictionary data for readable output."""
        if isinstance(data, dict):
            # 为键值对添加颜色
            if self.use_colors:
                # 使用青色突出显示键名，并让值变暗
                return " | ".join(f"{COLORS['CYAN']}{k.upper()}{COLORS['RESET']}={COLORS['DARK_WHITE']}{self._format_value(v)}{COLORS['RESET']}" for k, v in data.items())
            else:
                return " | ".join(f"{k.upper()}={self._format_value(v)}" for k, v in data.items())
        return str(data)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for logging, handling different types appropriately."""
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, (list, tuple)):
            if len(value) > 3:
                # 仍然保持列表项的简化表示
                return f"[{len(value)} items]"
            return str(value)
        # 不再截断长字符串
        # elif isinstance(value, str) and len(value) > 100:
        #     return f"{value[:100]}..."
        return str(value)
    
    def _get_level_color(self, level_name: str) -> str:
        """获取日志级别对应的颜色"""
        if not self.use_colors:
            return ""
        return LEVEL_COLORS.get(level_name.upper(), "")
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an info message with optional structured data."""
        if data:
            self.logger.info(f"{message} {self._format_data(data)}")
        else:
            self.logger.info(message)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a debug message with optional structured data."""
        if data:
            self.logger.debug(f"{message} {self._format_data(data)}")
        else:
            self.logger.debug(message)
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a warning message with optional structured data."""
        if data:
            self.logger.warning(f"{message} {self._format_data(data)}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an error message with optional structured data."""
        if data:
            self.logger.error(f"{message} {self._format_data(data)}")
        else:
            self.logger.error(message)
    
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a critical message with optional structured data."""
        if data:
            self.logger.critical(f"{message} {self._format_data(data)}")
        else:
            self.logger.critical(message)
    
    def highlight(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        突出显示重要结果或最终输出，使用明亮的颜色和粗体。
        
        Args:
            message: 要高亮显示的消息
            data: 可选的结构化数据
        """
        highlighted_msg = message
        if self.use_colors:
            highlighted_msg = f"{COLORS['BOLD']}{COLORS['WHITE']}{message}{COLORS['RESET']}"
            
        if data:
            # 高亮显示数据部分
            formatted_data = " ".join(f"{COLORS['BOLD']}{COLORS['CYAN']}{k.upper()}{COLORS['RESET']}={COLORS['WHITE']}{self._format_value(v)}{COLORS['RESET']}" 
                                    for k, v in data.items()) if self.use_colors else self._format_data(data)
            self.logger.info(f"{highlighted_msg} {formatted_data}")
        else:
            self.logger.info(highlighted_msg)
            
    def result(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        记录最终结果，以突出显示方式。
        这是highlight方法的别名。
        
        Args:
            message: 结果消息
            data: 可选的结构化数据
        """
        self.highlight(message, data) 