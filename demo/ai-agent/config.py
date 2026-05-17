"""
全局配置模块
统一管理 API 配置，所有 demo 通过 import config 读取
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


def get_api_key():
    """获取 API Key，优先环境变量，其次 .env"""
    key = os.getenv("MINIMAX_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "未找到 API Key，请设置环境变量 MINIMAX_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY\n"
            "或创建 .env 文件（参考 .env.example）"
        )
    return key


def get_api_url():
    """获取 API URL，默认为 MiniMax"""
    return os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/v1")


def get_model():
    """获取模型名，默认为 MiniMax-M2.7"""
    return os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")


# 测试连通性
if __name__ == "__main__":
    try:
        print(f"API URL: {get_api_url()}")
        print(f"Model: {get_model()}")
        print(f"API Key: {get_api_key()[:8]}...")
    except ValueError as e:
        print(f"配置错误: {e}")