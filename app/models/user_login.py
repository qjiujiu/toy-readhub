from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime, timedelta

class UserLogin(Base):
    """ 用户登录信息模型，对应数据库中的 user_login 表。

        CREATE TABLE IF NOT EXISTS user_login (
            id INT AUTO_INCREMENT PRIMARY KEY,        -- 登录信息的唯一 ID
            user_id INT NOT NULL,                     -- 用户的 ID，外键关联到 users 表的 uid
            username VARCHAR(50) NOT NULL UNIQUE,     -- 用户登录用户名，唯一
            password VARCHAR(100) NOT NULL,           -- 用户登录密码
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最后登录时间
            FOREIGN KEY (user_id) REFERENCES users(uid) -- 外键约束
        );
    """

    __tablename__ = "user_login"

    id = Column(Integer, primary_key=True, autoincrement=True)          # 登录信息唯一标识
    user_id = Column(Integer, ForeignKey('users.uid'), nullable=False)  # 用户 ID，外键关联到 users 表
    username = Column(String(50), unique=True, nullable=False)          # 用户登录用户名（唯一）即学号
    password = Column(String(100), nullable=False)                      # 用户密码（存储加密后的密码）
    last_login = Column(DateTime, default=datetime.utcnow)              # 用户最后登录时间

    # 反向引用：与 User 模型的关联
    user = relationship("User", back_populates="login_info")

