from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# ======== 配置区 ========
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "102412"   # 你的 MySQL 密码
DB_NAME = "library_db"
# ========================

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# SQLAlchemy 引擎
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_database():
    """
    自动初始化数据库和表
    """
    try:
        # 先连接 MySQL（不指定 DB）
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = conn.cursor()
        # 创建数据库
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        )
        print(f"✅ 数据库 {DB_NAME} 已确认存在！")
    except Exception as e:
        print("❌ 初始化数据库失败：", e)
    finally:
        if conn:
            conn.close()
