CREATE SCHEMA IF NOT EXISTS project440;
USE project440;

CREATE USER IF NOT EXISTS 'pyconn'@'127.0.0.1' IDENTIFIED BY '1234';
CREATE USER IF NOT EXISTS 'pyconn'@'localhost' IDENTIFIED BY '1234';
GRANT SELECT, INSERT, UPDATE, CREATE ON project440.* TO 'pyconn'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE, CREATE ON project440.* TO 'pyconn'@'localhost';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS user (
  username VARCHAR(255) PRIMARY KEY,
  password VARCHAR(255) NOT NULL,
  firstName VARCHAR(255) NOT NULL,
  lastName VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(255) NOT NULL,
  CONSTRAINT u_email UNIQUE (email),
  CONSTRAINT u_phone UNIQUE (phone)
);

INSERT INTO user (username, password, firstName, lastName, email, phone)
VALUES ("123", "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3", "Test", "User","user@test.com", 1234555);