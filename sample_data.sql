-- Optional demo data for testing all project phases.
-- Password for all sample users is: password123
-- SHA-256: ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f

USE project440;

INSERT IGNORE INTO user (username, password, firstName, lastName, email, phone) VALUES
  ('alice', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Alice', 'Smith', 'alice@test.com', '1111111111'),
  ('bob', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Bob', 'Jones', 'bob@test.com', '2222222222'),
  ('carol', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Carol', 'Lee', 'carol@test.com', '3333333333'),
  ('dave', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Dave', 'Kim', 'dave@test.com', '4444444444');

INSERT IGNORE INTO category (categoryName) VALUES
  ('electronic'), ('cellphone'), ('apple'), ('book'), ('fiction'), ('furniture');

INSERT INTO item (title, description, postDate, price, postedBy) VALUES
  ('Smartphone', 'This is the new iPhone X', '2024-07-04', 1000.00, 'alice'),
  ('Kindle', 'E-reader device', '2024-07-04', 120.00, 'alice'),
  ('Desk Chair', 'Comfortable office chair', '2024-07-04', 250.00, 'bob'),
  ('Novel', 'Bestselling fiction book', '2024-06-01', 15.00, 'bob'),
  ('Tablet', 'Android tablet', '2024-07-04', 400.00, 'bob'),
  ('Lamp', 'Desk lamp', '2024-05-10', 35.00, 'carol');

INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'electronic' FROM item i WHERE i.title = 'Smartphone';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'cellphone' FROM item i WHERE i.title = 'Smartphone';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'apple' FROM item i WHERE i.title = 'Smartphone';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'electronic' FROM item i WHERE i.title = 'Kindle';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'book' FROM item i WHERE i.title = 'Kindle';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'furniture' FROM item i WHERE i.title = 'Desk Chair';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'fiction' FROM item i WHERE i.title = 'Novel';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'book' FROM item i WHERE i.title = 'Novel';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'electronic' FROM item i WHERE i.title = 'Tablet';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'cellphone' FROM item i WHERE i.title = 'Tablet';
INSERT INTO item_category (itemId, categoryName)
SELECT i.itemId, 'furniture' FROM item i WHERE i.title = 'Lamp';

INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'bob', 'Excellent', 'Great phone.', '2024-07-05'
FROM item i WHERE i.title = 'Smartphone';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'carol', 'Good', 'Solid e-reader.', '2024-07-06'
FROM item i WHERE i.title = 'Kindle';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'alice', 'Fair', 'Decent chair.', '2024-07-07'
FROM item i WHERE i.title = 'Desk Chair';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'alice', 'Poor', 'Not my genre.', '2024-06-02'
FROM item i WHERE i.title = 'Novel';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'dave', 'Poor', 'Too slow.', '2024-07-08'
FROM item i WHERE i.title = 'Tablet';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'carol', 'Poor', 'Bad experience.', '2024-07-09'
FROM item i WHERE i.title = 'Tablet';
INSERT INTO review (itemId, reviewer, score, remark, reviewDate)
SELECT i.itemId, 'alice', 'Poor', 'Weak light.', '2024-05-11'
FROM item i WHERE i.title = 'Lamp';
