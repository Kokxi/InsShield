"""日志配置：统一的 logging 设置，供全项目使用"""
import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "jinrong-sdd",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """配置并返回全局 Logger

    Args:
        name: logger 名称
        level: 日志级别，默认 INFO
        log_file: 可选日志文件路径，默认只输出到 stderr
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 Handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stderr handler
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 可选文件 handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# 全局默认 logger，模块通过 getLogger(__name__) 使用
default_logger = setup_logger()
