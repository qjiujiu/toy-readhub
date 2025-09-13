-- 1. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS library_db
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

-- 2. 使用数据库
USE library_db;

-- 3. 创建 books 表
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    description VARCHAR(500) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 插入一些测试数据
INSERT INTO books (title, author, description) VALUES
('三体', '刘慈欣', '中国科幻小说经典'),
('百年孤独', '加西亚·马尔克斯', '魔幻现实主义代表作'),
('The Great Gatsby', 'F. Scott Fitzgerald', '美国爵士时代经典');
