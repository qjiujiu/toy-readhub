from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.models.base import Base

class UserRestriction(Base):
    """ 用户借阅限制表（黑名单/冻结状态）
    
        CREATE TABLE IF NOT EXISTS user_restrictions  (
            ur_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            is_restricted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否被限制借阅',
            restricted_until DATETIME NULL COMMENT '限制到期时间（到期后可自动解除）',
            reason VARCHAR(255) NULL COMMENT '限制原因简述',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            -- 一个用户只保留一条当前限制记录（幂等更新）
            UNIQUE KEY uk_user (user_id),

            -- 外键到 users(id)
            CONSTRAINT fk_user_restrictions_user
              FOREIGN KEY (user_id) REFERENCES users (uid)
              ON UPDATE CASCADE ON DELETE CASCADE,

            -- 为到期自动解除或批量查询做索引
            INDEX idx_restricted_until (restricted_until),
            INDEX idx_is_restricted (is_restricted)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户借阅限制状态';
    """
    __tablename__ = "user_restrictions"

    ur_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.uid", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)  # 用户id，外键
    is_restricted = Column(Boolean, nullable=False, default=False)                                             # 当前是否限制
    restricted_until = Column(DateTime, nullable=True)                                                         # 限制到期时间（为空=不限期）
    reason = Column(String(255), nullable=True)                                                                # 简述原因（可选）
    created_at = Column(DateTime, nullable=False, server_default=func.now())                                   # 创建时间，据库自动填充当前时间             
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())              # 更新时间，据库自动填充当前时间

    __table_args__ = (
        UniqueConstraint("user_id", name="uk_user"),          # user_id 唯一
        Index("idx_restricted_until", "restricted_until"),    # 给 restricted_until 键索引，加速按到期时间查询更新
        Index("idx_is_restricted", "is_restricted"),          # 给 is_restricted 键索引，加速查找被限制用户的用户列表
    )

    # ORM 关联：从限制记录可访问用户；从 User 可反向访问 restriction（uselist=False 表示一对一）
    user = relationship("User", back_populates="restriction", uselist=False)
    