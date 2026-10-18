-- 金额为分，时间为北京时间；收银单号通过数据库唯一约束按自然日去重。
CREATE TABLE cafe_student (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  student_no varchar(40) NOT NULL,
  name varchar(80) NOT NULL,
  dingtalk_user_id varchar(100) NULL,
  first_login_time datetime(3) NOT NULL,
  last_login_time datetime(3) NOT NULL,
  UNIQUE KEY uk_student_no(student_no), UNIQUE KEY uk_dingtalk_user(dingtalk_user_id),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_category (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code varchar(30) NOT NULL,
  name varchar(50) NOT NULL,
  name_en varchar(100) NOT NULL DEFAULT '',
  sort int NOT NULL DEFAULT 0,
  UNIQUE KEY uk_category_code(code),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_menu_item (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name varchar(100) NOT NULL,
  name_en varchar(100) NOT NULL DEFAULT '',
  description varchar(1000) NOT NULL DEFAULT '',
  description_en varchar(1000) NOT NULL DEFAULT '',
  price int NOT NULL,
  category_code varchar(30) NOT NULL,
  image_url varchar(1000) NOT NULL,
  recommended bit(1) NOT NULL DEFAULT b'0',
  enabled bit(1) NOT NULL DEFAULT b'1',
  sold_out bit(1) NOT NULL DEFAULT b'0',
  sort int NOT NULL DEFAULT 0,
  CHECK(price>=0), KEY idx_menu_category(category_code),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_option_group (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name varchar(50) NOT NULL,
  name_en varchar(100) NOT NULL DEFAULT '',
  sort int NOT NULL DEFAULT 0,
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_option (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  group_id bigint NOT NULL,
  name varchar(50) NOT NULL,
  name_en varchar(100) NOT NULL DEFAULT '',
  price_delta int NOT NULL DEFAULT 0,
  is_default bit(1) NOT NULL DEFAULT b'0',
  sort int NOT NULL DEFAULT 0,
  CHECK(price_delta>=0), KEY idx_option_group(group_id),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_item_group (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  item_id bigint NOT NULL,
  group_id bigint NOT NULL,
  KEY idx_item_group(item_id,group_id), KEY idx_group_item(group_id,item_id),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_shop (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  open bit(1) NOT NULL DEFAULT b'1',
  banner varchar(120) NOT NULL DEFAULT '',
  business_hours json NOT NULL,
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_order (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_no varchar(40) NOT NULL,
  student_id bigint NOT NULL,
  student_no varchar(40) NOT NULL,
  student_name varchar(80) NOT NULL,
  status tinyint NOT NULL,
  business_date date NOT NULL,
  pos_order_no varchar(20) NULL,
  total_price int NOT NULL,
  cup_count int NOT NULL,
  entered_time datetime(3) NULL,
  done_time datetime(3) NULL,
  failure_reason varchar(200) NULL,
  request_key varchar(64) NOT NULL,
  fingerprint char(64) NOT NULL,
  version int NOT NULL DEFAULT 0,
  retry_after datetime(3) NULL,
  CHECK(total_price>=0), CHECK(cup_count>0), CHECK(status IN(0,1,2,10,20,30)),
  UNIQUE KEY uk_order_no(order_no),
  UNIQUE KEY uk_order_request(student_id,request_key),
  UNIQUE KEY uk_order_pos_day(business_date,pos_order_no),
  KEY idx_order_board(business_date,status,create_time,id),
  KEY idx_order_student(student_id,create_time,id),
  KEY idx_order_retry(status,retry_after),
  KEY idx_order_fingerprint(student_id,fingerprint,create_time),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE cafe_order_item (
  id bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_id bigint NOT NULL,
  item_id bigint NOT NULL,
  name varchar(100) NOT NULL,
  name_en varchar(100) NOT NULL DEFAULT '',
  image_url varchar(1000) NOT NULL,
  unit_price int NOT NULL,
  quantity int NOT NULL,
  options_text varchar(1000) NOT NULL,
  options json NOT NULL,
  CHECK(unit_price>=0), CHECK(quantity>0), KEY idx_order_item(order_id),
  creator varchar(64) NULL DEFAULT '',
  create_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updater varchar(64) NULL DEFAULT '',
  update_time datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  deleted bit(1) NOT NULL DEFAULT b'0' 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

INSERT INTO cafe_category (id,code,name,name_en,sort) VALUES
(1,'coffee','现磨咖啡','Coffee',1),(2,'seasonal','当季新品','Seasonal',2),(3,'fruit','鲜果茶','Fruit tea',3),(4,'bakery','烘焙轻食','Bakery',4);

INSERT INTO cafe_option_group (id,name,name_en,sort) VALUES (1,'温度','Temperature',1),(2,'糖度','Sugar',2);
INSERT INTO cafe_option (id,group_id,name,name_en,price_delta,is_default,sort) VALUES
(1,1,'热','Hot',0,b'1',1),(2,1,'冰','Iced',0,b'0',2),
(3,2,'无糖','No sugar',0,b'0',1),(4,2,'半糖','Half sugar',0,b'0',2),(5,2,'标准','Regular',0,b'1',3),(6,2,'多糖','Extra sugar',0,b'0',4);

INSERT INTO cafe_shop (id,open,banner,business_hours) VALUES (1,b'1','','[{"start":"11:40","end":"12:30"},{"start":"15:30","end":"17:00"}]');

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (1,'经典拿铁','Caffe Latte',1500,'coffee','/static/menu/latte.jpg',1,1);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (1,1),(1,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (2,'意式浓缩','Espresso',1000,'coffee','/static/menu/espresso.jpg',0,2);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (2,1),(2,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (3,'卡布奇诺','Cappuccino',1600,'coffee','/static/menu/cappuccino.jpg',0,3);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (3,1),(3,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (4,'焦糖玛奇朵','Caramel Macchiato',1900,'coffee','/static/menu/macchiato.jpg',1,4);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (4,1),(4,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (5,'澳白咖啡','Flat White',1700,'coffee','/static/menu/flatwhite.jpg',0,5);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (5,1),(5,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (6,'生椰拿铁','Iced Coconut Latte',1800,'seasonal','/static/menu/coconut-latte.jpg',1,6);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (6,1),(6,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (7,'冷萃咖啡','Cold Brew',2000,'seasonal','/static/menu/coldbrew.jpg',0,7);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (7,1),(7,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (8,'抹茶奶绿','Matcha Milk Green Tea',1700,'fruit','/static/menu/matcha.jpg',0,8);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (8,1),(8,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (9,'鲜果茶','Citrus Fruit Tea',1500,'fruit','/static/menu/fruit-tea.jpg',0,9);

INSERT INTO cafe_item_group (item_id,group_id) VALUES (9,1),(9,2);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (10,'黄油可颂','Butter Croissant',1200,'bakery','/static/menu/croissant.jpg',0,10);

INSERT INTO cafe_menu_item (id,name,name_en,price,category_code,image_url,recommended,sort) VALUES (11,'巴斯克芝士蛋糕','Basque Cheesecake',2200,'bakery','/static/menu/cheesecake.jpg',1,11);
