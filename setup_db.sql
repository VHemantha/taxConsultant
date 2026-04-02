-- Run this in MySQL to create the database
CREATE DATABASE IF NOT EXISTS tax_automation_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'tax_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON tax_automation_db.* TO 'tax_user'@'localhost';
FLUSH PRIVILEGES;

-- Then run Django migrations:
-- python manage.py makemigrations
-- python manage.py migrate
-- python manage.py createsuperuser
