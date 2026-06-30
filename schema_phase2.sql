USE project440;

CREATE TABLE IF NOT EXISTS item (
  itemId INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  postDate DATE NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  postedBy VARCHAR(255) NOT NULL,
  CONSTRAINT fk_item_posted_by FOREIGN KEY (postedBy) REFERENCES user(username)
);

CREATE TABLE IF NOT EXISTS category (
  categoryName VARCHAR(255) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS item_category (
  itemId INT NOT NULL,
  categoryName VARCHAR(255) NOT NULL,
  PRIMARY KEY (itemId, categoryName),
  CONSTRAINT fk_item_category_item FOREIGN KEY (itemId) REFERENCES item(itemId) ON DELETE CASCADE,
  CONSTRAINT fk_item_category_category FOREIGN KEY (categoryName) REFERENCES category(categoryName)
);

CREATE TABLE IF NOT EXISTS review (
  reviewId INT AUTO_INCREMENT PRIMARY KEY,
  itemId INT NOT NULL,
  reviewer VARCHAR(255) NOT NULL,
  score ENUM('Excellent', 'Good', 'Fair', 'Poor') NOT NULL,
  remark TEXT NOT NULL,
  reviewDate DATE NOT NULL,
  CONSTRAINT uq_review_item_reviewer UNIQUE (itemId, reviewer),
  CONSTRAINT fk_review_item FOREIGN KEY (itemId) REFERENCES item(itemId) ON DELETE CASCADE,
  CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewer) REFERENCES user(username)
);

GRANT SELECT, INSERT, UPDATE ON project440.* TO 'pyconn'@'127.0.0.1';
FLUSH PRIVILEGES;
