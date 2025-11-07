from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.models.base import Base

class UserCredit(Base):
    """ 用户信誉表（借阅惩罚/限制状态）

        CREATE TABLE IF NOT EXISTS user_credit (
            uc_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            
            is_lost TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否存在丢失图书的情况（丢失未处理前禁止借书）',
            is_overdue TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否存在逾期未处理的情况（逾期期间禁止借书）',
            
            penalty_until DATETIME NULL COMMENT '惩罚到期时间（逾期惩罚结束时间）',
            reason VARCHAR(255) NULL COMMENT '信誉状态原因简述（例如：逾期天数、丢失书籍等）',
            
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            -- 一个用户只保留一条当前信誉记录（幂等更新）
            UNIQUE KEY uk_user (user_id),

            -- 外键到 users(uid)
            CONSTRAINT fk_user_credit_user
              FOREIGN KEY (user_id) REFERENCES users (uid)
              ON UPDATE CASCADE ON DELETE CASCADE,

            -- 索引：便于按惩罚到期时间查询自动解除状态
            INDEX idx_penalty_until (penalty_until),
            INDEX idx_is_lost (is_lost),
            INDEX idx_is_overdue (is_overdue)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信誉状态表';
    """
    __tablename__ = "user_credit"

    uc_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.uid", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    is_lost = Column(Boolean, nullable=False, default=False)              # 是否存在丢失图书
    is_overdue = Column(Boolean, nullable=False, default=False)           # 是否存在逾期未处理情况
    
    penalty_until = Column(DateTime, nullable=True)                       # 惩罚到期时间（例如逾期惩罚）
    reason = Column(String(255), nullable=True)                           # 状态原因简述

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uk_user"),
        Index("idx_penalty_until", "penalty_until"),
        Index("idx_is_lost", "is_lost"),
        Index("idx_is_overdue", "is_overdue"),
    )

    # ORM 关系：从信誉记录可访问用户；从 User 可反向访问 credit（1对1）
    user = relationship("User", back_populates="credit", uselist=False)

