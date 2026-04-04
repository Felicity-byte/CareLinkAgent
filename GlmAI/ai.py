import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 设置环境变量
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 检查必要的环境变量
required_env_vars = ["GLM_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    print(f"[警告] 缺少以下环境变量: {', '.join(missing_vars)}")
    print("   请在 .env 文件中配置或设置系统环境变量")

# 可选环境变量（智谱知识库）
if not os.environ.get("ZHIPU_API_KEY"):
    print("[信息] 未配置 ZHIPU_API_KEY，智谱知识库功能将不可用")

if not os.environ.get("ZHIPU_KNOWLEDGE_ID"):
    print("[信息] 未配置 ZHIPU_KNOWLEDGE_ID，智谱知识库功能将不可用")


def main():
    """主函数 - 启动 AI 服务"""
    from connect.server import serve
    
    print("=" * 60)
    print("  术后随访 AI 协同系统 - 服务端")
    print("  Post-Surgery Follow-up AI System")
    print("=" * 60)
    
    # 启动 gRPC 服务
    serve()


if __name__ == "__main__":
    main()
