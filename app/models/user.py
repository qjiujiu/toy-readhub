# 基本用户信息模型
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """ 用户模型，对应数据库中的 Users 表。
    
        USE BookHub;
        CREATE TABLE IF NOT EXISTS Users (
            uid INT AUTO_INCREMENT PRIMARY KEY,     -- 用户 ID
            name VARCHAR(100) NOT NULL,             -- 姓名
            student_id VARCHAR(20) NOT NULL UNIQUE, -- 业务唯一号码，学号，唯一，不同于底层使用的 uid
            email VARCHAR(50),     					-- 邮箱
            phone VARCHAR(50) NOT NULL              -- 电话（可为空）
        );

    """

    __tablename__ = "users"

    uid = Column(Integer, primary_key=True, autoincrement=True)         # 系统主键 ID
    
    
    name = Column(String(100), nullable=False)                          # 姓名
    student_id = Column(String(20), unique=True, nullable=False)        # 学号（唯一）
    email = Column(String(50), nullable=True)                           # 邮箱（可为空）
    phone = Column(String(50), nullable=False)                          # 电话

    # 反向引用：该用户的所有借阅订单
    orders = relationship("Order", back_populates="user")