-- Vendora simplified SQL schema generated from Django models
-- Adjust types and constraints for your chosen RDBMS

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(15),
  role VARCHAR(20) NOT NULL,
  profile_image VARCHAR(500),
  is_approved BOOLEAN DEFAULT true,
  email_verified BOOLEAN DEFAULT false,
  otp VARCHAR(6),
  otp_created_at TIMESTAMP,
  date_joined TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  is_staff BOOLEAN DEFAULT false
);

CREATE TABLE companies (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) UNIQUE,
  description TEXT,
  logo VARCHAR(500),
  address TEXT,
  city VARCHAR(100),
  state VARCHAR(100),
  country VARCHAR(100),
  postal_code VARCHAR(20),
  phone VARCHAR(15),
  email VARCHAR(255),
  website VARCHAR(255),
  tax_number VARCHAR(50),
  registration_number VARCHAR(50),
  currency VARCHAR(10)
);

CREATE TABLE sellers (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
  employee_id VARCHAR(50) UNIQUE,
  department VARCHAR(100),
  position VARCHAR(100),
  hire_date DATE
);

CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE,
  slug VARCHAR(100) UNIQUE,
  description TEXT,
  parent_id INTEGER REFERENCES categories(id),
  image VARCHAR(500)
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) UNIQUE NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
  seller_id INTEGER REFERENCES sellers(id) ON DELETE SET NULL,
  description TEXT,
  short_description VARCHAR(500),
  price DECIMAL(10,2),
  compare_price DECIMAL(10,2),
  cost_per_item DECIMAL(10,2),
  stock_quantity INTEGER,
  low_stock_threshold INTEGER,
  sku VARCHAR(50) UNIQUE,
  barcode VARCHAR(50),
  weight DECIMAL(10,2),
  dimensions VARCHAR(100),
  is_active BOOLEAN,
  is_featured BOOLEAN,
  is_digital BOOLEAN,
  average_rating DECIMAL(3,2),
  total_reviews INTEGER,
  total_sold INTEGER
);

CREATE TABLE product_images (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  image VARCHAR(500),
  alt_text VARCHAR(200),
  is_main BOOLEAN,
  "order" INTEGER
);

CREATE TABLE product_reviews (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  rating INTEGER,
  title VARCHAR(200),
  comment TEXT,
  verified_purchase BOOLEAN,
  is_approved BOOLEAN
);

CREATE TABLE wishlists (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE carts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE cart_items (
  id SERIAL PRIMARY KEY,
  cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  quantity INTEGER
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  company_id INTEGER REFERENCES companies(id),
  order_number VARCHAR(20) UNIQUE,
  total_amount DECIMAL(12,2),
  subtotal DECIMAL(12,2),
  shipping_cost DECIMAL(10,2),
  tax_amount DECIMAL(10,2),
  discount_amount DECIMAL(10,2),
  status VARCHAR(20),
  payment_status VARCHAR(20),
  payment_method VARCHAR(20),
  payment_id VARCHAR(100)
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  quantity INTEGER,
  price DECIMAL(10,2),
  total DECIMAL(10,2)
);

CREATE TABLE ai_chat_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  message TEXT,
  response TEXT,
  context_used JSONB
);

CREATE TABLE user_product_interests (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  interest_type VARCHAR(20),
  weight FLOAT,
  metadata JSONB
);

CREATE TABLE user_chat_preferences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  category VARCHAR(100),
  keyword VARCHAR(200),
  interest_score FLOAT
);

CREATE TABLE user_recommendations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
  reason VARCHAR(255),
  clicked BOOLEAN DEFAULT false
);

CREATE TABLE otps (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  code VARCHAR(6),
  created_at TIMESTAMP,
  expires_at TIMESTAMP,
  is_used BOOLEAN DEFAULT false
);

-- End of schema
