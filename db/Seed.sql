-- Seed data for Library Agent Database

-- Insert 10 Books
INSERT INTO books (isbn, title, author, price, stock) VALUES
('978-0132350884', 'Clean Code', 'Robert Martin', 39.99, 50),
('978-0137081073', 'The Clean Coder', 'Robert Martin', 34.99, 22),
('978-0201616224', 'The Pragmatic Programmer', 'Andrew Hunt', 44.99, 30),
('978-0134685991', 'Effective Java', 'Joshua Bloch', 49.99, 25),
('978-0596007126', 'Head First Design Patterns', 'Eric Freeman', 39.99, 40),
('978-1593279288', 'Python Crash Course', 'Eric Matthes', 39.95, 35),
('978-1491950296', 'Fluent Python', 'Luciano Ramalho', 54.99, 20),
('978-0135957059', 'The Mythical Man-Month', 'Frederick Brooks', 34.99, 15),
('978-0321125215', 'Domain-Driven Design', 'Eric Evans', 59.99, 4),
('978-0201633610', 'Design Patterns', 'Gang of Four', 54.99, 28);

-- Insert 6 Customers
INSERT INTO customers (name, email) VALUES
('Alice Johnson', 'alice@example.com'),
('Bob Smith', 'bob@example.com'),
('Charlie Brown', 'charlie@example.com'),
('Diana Prince', 'diana@example.com'),
('Ethan Hunt', 'ethan@example.com'),
('Fiona Green', 'fiona@example.com');

-- Insert 4 Orders
INSERT INTO orders (customer_id, total_amount, status, created_at) VALUES
(1, 79.98, 'completed', datetime('now', '-7 days')),
(2, 44.99, 'completed', datetime('now', '-5 days')),
(3, 119.85, 'completed', datetime('now', '-3 days')),
(4, 109.98, 'completed', datetime('now', '-1 day'));

-- Insert Order Items for 4 Orders
-- Order 1: Alice bought 2x Clean Code
INSERT INTO order_items (order_id, isbn, quantity, price_at_purchase) VALUES
(1, '978-0132350884', 2, 39.99);

-- Order 2: Bob bought 1x The Pragmatic Programmer
INSERT INTO order_items (order_id, isbn, quantity, price_at_purchase) VALUES
(2, '978-0201616224', 1, 44.99);

-- Order 3: Charlie bought 3x Python Crash Course
INSERT INTO order_items (order_id, isbn, quantity, price_at_purchase) VALUES
(3, '978-1593279288', 3, 39.95);

-- Order 4: Diana bought 2x Effective Java
INSERT INTO order_items (order_id, isbn, quantity, price_at_purchase) VALUES
(4, '978-0134685991', 2, 49.99);