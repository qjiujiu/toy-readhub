import pymysql

# ======== 配置区，按你的 MySQL 修改 ========
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "123456"   # 这里换成你的 MySQL 密码
DB_NAME = "library_db"
# ==========================================

# 初始化 SQL
INIT_SQL = f"""
CREATE DATABASE IF NOT EXISTS {DB_NAME}
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE {DB_NAME};

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    description VARCHAR(500) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO books (title, author, description) VALUES
('三体', '刘慈欣', '中国科幻小说经典'),
('百年孤独', '加西亚·马尔克斯', '魔幻现实主义代表作'),
('The Great Gatsby', 'F. Scott Fitzgerald', '美国爵士时代经典')
ON DUPLICATE KEY UPDATE title=VALUES(title);
"""

def init_db():
    try:
        # 连接 MySQL（先不指定数据库）
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = conn.cursor()
        # 执行初始化 SQL
        for stmt in INIT_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)
        print("✅ 数据库和表已初始化成功！")
    except Exception as e:
        print("❌ 初始化失败：", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
