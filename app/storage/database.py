from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import pymysql
from sqlalchemy.orm import Session, sessionmaker
from app.storage.user.SQLAlchemyUserRepository import SQLAlchemyUserRepository
from app.storage.book.SQLAlchemyBookRepository import SQLAlchemyBookRepository
from app.storage.book_inventory.SQLAlchemyBookinvRepository import SQLAlchemyBookinvRepository
from app.storage.book_location.SQLAlchemyBooklocRepository import SQLAlchemyBookLocationRepository
from fastapi import Depends

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 未来可以根据配置切换不同的实现
def get_user_repo(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(db)

def get_book_repo(db: Session = Depends(get_db)) -> SQLAlchemyBookRepository:
    return SQLAlchemyBookRepository(db)

def get_bookinv_repo(db: Session = Depends(get_db)) -> SQLAlchemyBookinvRepository:
    return SQLAlchemyBookinvRepository(db)

def get_bookloc_repo(db: Session = Depends(get_db)) -> SQLAlchemyBookLocationRepository:
    return SQLAlchemyBookLocationRepository(db)