CREATE DATABASE IF NOT EXISTS bankdb;
USE bankdb;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sender_id INT,
  receiver_id INT,
  amount DECIMAL(12,2) NOT NULL,
  txn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  note VARCHAR(255),
  FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insert a sample user (password to be set later via app) or use register page
INSERT INTO users (name, email, password_hash, balance)
VALUES ('Bank Admin', 'admin@example.com', 'PLACEHOLDER', 100000.00);
