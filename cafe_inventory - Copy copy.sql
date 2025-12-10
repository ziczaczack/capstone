BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "inventory" (
	"id"	INTEGER,
	"sku"	TEXT NOT NULL UNIQUE,
	"standard_name"	TEXT NOT NULL,
	"brand_name"	TEXT,
	"unit"	TEXT NOT NULL,
	"unit_cost"	REAL DEFAULT 0,
	"current_stock"	REAL DEFAULT 0,
	"threshold"	REAL DEFAULT 0,
	"is_active"	INTEGER DEFAULT 1,
	"supplier_id"	INTEGER,
	"category"	TEXT DEFAULT '',
	"low_stock"	INTEGER DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("supplier_id") REFERENCES "suppliers"("id")
);
CREATE TABLE IF NOT EXISTS "inventory_audit" (
	"id"	INTEGER,
	"sku"	TEXT NOT NULL,
	"change"	REAL NOT NULL,
	"before_stock"	REAL,
	"after_stock"	REAL,
	"reason"	TEXT,
	"ref_id"	INTEGER,
	"created_by"	INTEGER,
	"created_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "products" (
	"id"	INTEGER,
	"category"	TEXT,
	"product_name"	TEXT,
	"description"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "recipes" (
	"id"	INTEGER,
	"product_name"	TEXT,
	"ingredient_sku"	TEXT,
	"usage"	REAL,
	"unit"	TEXT,
	"ingredient_category"	TEXT DEFAULT '',
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("ingredient_sku") REFERENCES "inventory"("sku"),
	FOREIGN KEY("ingredient_sku") REFERENCES "",
	FOREIGN KEY("product_name") REFERENCES "products"("product_name")
);
CREATE TABLE IF NOT EXISTS "stock_receipts" (
	"id"	INTEGER,
	"sku"	TEXT NOT NULL,
	"quantity"	REAL NOT NULL,
	"unit_cost"	REAL,
	"total_cost"	REAL,
	"supplier_id"	INTEGER,
	"created_by"	INTEGER,
	"created_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"notes"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "suppliers" (
	"id"	INTEGER,
	"company_name"	TEXT NOT NULL,
	"contact_person"	TEXT,
	"phone"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "transactions" (
	"id"	INTEGER,
	"product_id"	INTEGER NOT NULL,
	"quantity"	INTEGER NOT NULL,
	"total_cost"	REAL,
	"sale_date"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"status"	TEXT DEFAULT 'completed',
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("product_id") REFERENCES "products"("id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"role"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "inventory" VALUES (1,'CF-BEAN','Coffee Bean','Ghostbird','g',0.095,11430.0,4680.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (2,'MLK-FARM','Milk','farm fresh','g',0.00713,91500.0,36600.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (3,'SYR-SIMPLE','Simple Syrup','(Homemade)','g',0.022,1750.0,700.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (4,'CHOC-545','Chocolate 54.5%','Callebaut','g',0.936,3000.0,1200.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (5,'CHOC-705','Chocolate 70.5%','Callebaut','g',0.1088,750.0,300.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (6,'MILK-OAT','Oat Milk','Oatside','g',0.009,1000.0,3100.0,1,1,NULL,1);
INSERT INTO "inventory" VALUES (7,'MLK-CDENSED','Condensed Milk','F&N','g',0.00636,1250.0,500.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (8,'SYR-STRAWBERRY','Strawberry Syrup','MONT','g',0.0564,750.0,300.0,1,1,'Flavour Syrup',0);
INSERT INTO "inventory" VALUES (9,'SYR-PINEAPPLE','Pineapple Syrup','MONT','g',0.0564,7500.0,3000.0,1,1,'Flavour Syrup',0);
INSERT INTO "inventory" VALUES (10,'SYR-YUZU','Yuzu Syrup','MONT','g',0.06,1250.0,500.0,1,1,'Flavour Syrup',0);
INSERT INTO "inventory" VALUES (11,'SYR-SEASALT','Sea Salted Caramel Syrup','MONT','g',0.0564,0.0,600.0,1,1,'Flavour Syrup',1);
INSERT INTO "inventory" VALUES (12,'SYR-R.HAZELNUT','Roasted Hazelnut Syrup','MONT','g',0.0564,0.0,600.0,1,1,'Flavour Syrup',1);
INSERT INTO "inventory" VALUES (13,'SYR-GRENADINE','Grenadine Syrup','MONT','g',0.0564,750.0,300.0,1,1,'Flavour Syrup',0);
INSERT INTO "inventory" VALUES (14,'SYR-HONEY','Honey Syrup','MONT','g',0.0564,250.0,100.0,1,1,'Flavour Syrup',0);
INSERT INTO "inventory" VALUES (15,'SYR-VANILLA','Vanilla Syrup','MONT','g',0.0564,0.0,600.0,1,1,'Flavour Syrup',1);
INSERT INTO "inventory" VALUES (16,'MATCHA-POW','Matcha Powder','Yamama Masudaen CO.,LTD.','g',0.238,500.0,200.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (17,'COCOA-POW','Chocolate Powder','Callebaut','g',0.06818,5.0,2.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (18,'MASCARPONE','Cream','Elle & Vire','g',0.049,1500.0,600.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (19,'LADY-FINGER','Lady Finger','Gastone Lago','nos',0.295,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (20,'EARL-GREY','Tea Powder','JING','TB',1.85,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (21,'ENG-BREAKFAST','Tea Powder','JING','TB',1.85,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (22,'JADE-SWORD','Tea Powder','JING','TB',1.7,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (23,'CHAMOMILE','Tea Powder','JING','TB',2.5,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (24,'BLKCURRANT-HIBCUS','Tea Powder','JING','TB',2.5,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (25,'LEMON-JUICE','Lemon Juice','SECAI MARCHE','g',0.0467,1000.0,400.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (26,'LEMON-WEDGE','Lemon Wedge',NULL,'nos',0.0583,50.0,20.0,NULL,NULL,NULL,0);
INSERT INTO "inventory" VALUES (27,'LIME-JUICE','Lime Juice','SECAI MARCHE','g',0.007523,3000.0,1200.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (28,'ORANGE','Orange',NULL,'nos',1.4,125.0,50.0,NULL,NULL,NULL,0);
INSERT INTO "inventory" VALUES (29,'ORANGE-JUICE','Orange Juice','SECAI MARCHE','g',0.014,12000.0,4800.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (30,'MINT','Mint','SECAI MARCHE','nos',0.0079,300.0,120.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (31,'ORANGE-DRIED','Dried Orange','Shopee','pc',0.3966,75.0,30.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (32,'SODA-WATER','Soda Water','Soda Express','g',0.22,111.0,44.4,1,1,NULL,0);
INSERT INTO "inventory" VALUES (33,'BUTTERFLY-PEA-FLOWER','Butterfly Pea Flower','Shopee','g',0.135,350.0,140.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (34,'SOCHOC-KELANTAN','Chocolate kelantan','Chocolate Concierge ','g',0.145,1350.0,600.0,1,1,'SO Chocolate',0);
INSERT INTO "inventory" VALUES (35,'SOCHOC-PAHANG','Chocolate pahang','Chocolate Concierge ','g',0.145,15.0,600.0,1,1,'SO Chocolate',1);
INSERT INTO "inventory" VALUES (36,'SYR-PEACH','Syrup','Tehmag','slice',0.15,50.0,20.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (37,'TEA-CEYLON','Tea Powder','888','g',0.018,3750.0,1500.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (38,'STRAWBERRY','Strawberry ','Dirafrost ','g',0.025,50000.0,20000.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (39,'BLACKTEA-BASE','Black Tea Base','(Tealeaf + Brown Sugar + Water)','g',0.00107,8000.0,3200.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (40,'BUTTERFLY-FLOWER-SYR','Butterfly pea Flower Syrup','(Butterfly Pea Flower + Water + Sugar)','g',0.002397,2000.0,800.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (41,'BROWN-SUGAR','Brown Sugar','SECAI MARCHE','g',0.007,21500.0,8600.0,1,1,NULL,0);
INSERT INTO "inventory" VALUES (42,'STRAWBERRY-COMPOTE','Strawberry Compote','(Lemon + Strawberry + Sugar)','g',0.0325,1500.0,600.0,1,1,NULL,0);
INSERT INTO "products" VALUES (1,'Coffee','Double Shot Espresso','2*single espresso');
INSERT INTO "products" VALUES (2,'Coffee ','Piccolo Latte ','Small cafe latte');
INSERT INTO "products" VALUES (3,'Coffee ','Americano',NULL);
INSERT INTO "products" VALUES (4,'Coffee ','Flat White/Latte/Cappucino',NULL);
INSERT INTO "products" VALUES (5,'Coffee ','Cafe Latte',NULL);
INSERT INTO "products" VALUES (6,'Coffee ','Flavoured Latte','Options: Vanilla or Roasted Hazelnut or Sea Salt Caramel');
INSERT INTO "products" VALUES (7,'Coffee ','Cappucino',NULL);
INSERT INTO "products" VALUES (8,'Specialty Coffee','Espresso Tonic','Double shot espresso, Lemon Juice, Soda');
INSERT INTO "products" VALUES (9,'Specialty Coffee','Orange Americano','Double shot espresso, Fresh Orange Juice, Simple Syrup');
INSERT INTO "products" VALUES (10,'Specialty Coffee','Spanish Latte','Double shot espresso, Sweetened Milk');
INSERT INTO "products" VALUES (11,'Specialty Coffee','Tiramisu Latte','Double shot espresso, Mascarpone Cream Topping');
INSERT INTO "products" VALUES (12,'Specialty Coffee','Affogato','Gelato, Double shot espresso');
INSERT INTO "products" VALUES (13,'Tea','Jing Earl Grey ',NULL);
INSERT INTO "products" VALUES (14,'Tea','Jing English Breakfast',NULL);
INSERT INTO "products" VALUES (15,'Tea','Jing Jade Sword',NULL);
INSERT INTO "products" VALUES (16,'Tea','Jing Chamomile',NULL);
INSERT INTO "products" VALUES (17,'Non-Coffee','Signature Chocolate','Blend of 70.5% and 54.5% Callebaut Belgian Chocolate');
INSERT INTO "products" VALUES (18,'Non-Coffee','Single Origin Chocolate','Options: Kelantan COE or Triang, Pahang');
INSERT INTO "products" VALUES (19,'Non-Coffee','Matcha Latte ','Yamama Masudaen Ceremonial Grade');
INSERT INTO "products" VALUES (20,'Non-Coffee','Strawberry Matcha Latte','Matcha, Housemade Strawberry Compote, Milk');
INSERT INTO "products" VALUES (21,'Non-Coffee','Babycinno','Steamed Fresh Milk (Options: Vanilla or Roasted Hazelnut or Sea Salt Caramel or Strawberry)');
INSERT INTO "products" VALUES (22,'Cold Refreshments ','Fresh Orange Juice','250ml Pure Chilled Fresh Orange Juice, No Sugar, No Ice');
INSERT INTO "products" VALUES (23,'Cold Refreshments ','Peach Mint Tea','Iced Shaken Black Tea, Peach, Lime, Mint');
INSERT INTO "products" VALUES (24,'Signature Mocktails ','Tropical Pine Sunrise','Pineapple, Orange, Grenadine');
INSERT INTO "products" VALUES (25,'Signature Mocktails ','Cosmic Lemonade','Yuzu, Lime, Honey, Butterfly Pea Flower');
INSERT INTO "products" VALUES (30,'Non-Coffee','Flavoured Babycinno','Babycinno with syrup');
INSERT INTO "recipes" VALUES (1,'Double Shot Espresso','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (2,'Piccolo Latte','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (3,'Piccolo Latte','MLK-FARM',100.0,'g',NULL);
INSERT INTO "recipes" VALUES (4,'Americano','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (5,'Flat White/Latte/Cappucino','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (6,'Flat White/Latte/Cappucino','MLK-FARM',155.0,'g',NULL);
INSERT INTO "recipes" VALUES (7,'Flavoured Latte','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (8,'Flavoured Latte','MLK-FARM',155.0,'g',NULL);
INSERT INTO "recipes" VALUES (9,'Flavoured Latte',NULL,15.0,'g','Flavour Syrup');
INSERT INTO "recipes" VALUES (10,'Mocha','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (11,'Mocha','MLK-FARM',155.0,'g',NULL);
INSERT INTO "recipes" VALUES (12,'Mocha','CHOC-545',20.0,'g',NULL);
INSERT INTO "recipes" VALUES (13,'Orange Mocha','ORANGE-JUICE',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (14,'Orange Mocha','SYR-SIMPLE',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (15,'Orange Mocha','CHOC-545',25.0,'g',NULL);
INSERT INTO "recipes" VALUES (16,'Orange Mocha','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (17,'Orange Mocha','ORANGE-DRIED',0.5,'pc',NULL);
INSERT INTO "recipes" VALUES (18,'Orange Americano','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (19,'Orange Americano','ORANGE-JUICE',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (20,'Orange Americano','SYR-SIMPLE',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (21,'Orange Americano','ORANGE-DRIED',0.5,'pc',NULL);
INSERT INTO "recipes" VALUES (22,'Spanish Latte','MLK-CDENSED',25.0,'g',NULL);
INSERT INTO "recipes" VALUES (23,'Spanish Latte','MLK-FARM',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (24,'Spanish Latte','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (25,'Tiramisu Latte','MASCARPONE',30.0,'g',NULL);
INSERT INTO "recipes" VALUES (26,'Tiramisu Latte','LADY-FINGER',1.0,'pc',NULL);
INSERT INTO "recipes" VALUES (27,'Tiramisu Latte','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (28,'Tiramisu Latte','SYR-SIMPLE',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (29,'Tiramisu Latte','MLK-FARM',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (30,'Tiramisu Latte','COCOA-POW',0.05,'g',NULL);
INSERT INTO "recipes" VALUES (31,'Jing Earl Grey (unwrapped)','EARL-GREY',1.0,'TB',NULL);
INSERT INTO "recipes" VALUES (32,'Jing English Breakfast (unwrapped)','ENG-BREAKFAST',1.0,'TB',NULL);
INSERT INTO "recipes" VALUES (33,'Jing Jade Sword (unwrapped)','JADE-SWORD',1.0,'TB',NULL);
INSERT INTO "recipes" VALUES (34,'Jing Chamomile (wrapped)','CHAMOMILE',1.0,'TB',NULL);
INSERT INTO "recipes" VALUES (35,'Jing Blackcurrant & Hibiscus (wrapped)','BLKCURRANT-HIBCUS',1.0,'TB',NULL);
INSERT INTO "recipes" VALUES (36,'Signature Chocolate','CHOC-545',15.0,'g',NULL);
INSERT INTO "recipes" VALUES (37,'Signature Chocolate','CHOC-705',15.0,'g',NULL);
INSERT INTO "recipes" VALUES (38,'Signature Chocolate','MLK-FARM',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (39,'Single Origin Chocolate',NULL,30.0,'g','SO Chocolate');
INSERT INTO "recipes" VALUES (40,'Single Origin Chocolate','MLK-FARM',130.0,'g',NULL);
INSERT INTO "recipes" VALUES (41,'Single Origin Chocolate','COCOA-POW',0.05,'g',NULL);
INSERT INTO "recipes" VALUES (42,'Matcha Latte ','MATCHA-POW',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (43,'Matcha Latte ','SYR-SIMPLE',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (44,'Matcha Latte ','MLK-FARM',155.0,'g',NULL);
INSERT INTO "recipes" VALUES (45,'Strawberry Matcha Latte','MATCHA-POW',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (46,'Strawberry Matcha Latte','SYR-SIMPLE',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (47,'Strawberry Matcha Latte','MLK-FARM',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (48,'Strawberry Matcha Latte','STRAWBERRY-COMPOTE',30.0,'g',NULL);
INSERT INTO "recipes" VALUES (49,'Strawberry Matcha Latte','SYR-STRAWBERRY',15.0,'g',NULL);
INSERT INTO "recipes" VALUES (50,'Babycinno','MLK-FARM',250.0,'g',NULL);
INSERT INTO "recipes" VALUES (51,'Flavoured Babycinno','MLK-FARM',250.0,'g',NULL);
INSERT INTO "recipes" VALUES (52,'Flavoured Babycinno',NULL,15.0,'g','Flavour Syrup');
INSERT INTO "recipes" VALUES (53,'Espresso Tonic','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (54,'Espresso Tonic','SODA-WATER',0.22,'g',NULL);
INSERT INTO "recipes" VALUES (55,'Espresso Tonic','LEMON-JUICE',20.0,'g',NULL);
INSERT INTO "recipes" VALUES (56,'Espresso Tonic','LEMON-WEDGE',1.0,'nos',NULL);
INSERT INTO "recipes" VALUES (57,'Fresh Orange Juice','ORANGE',2.5,'nos',NULL);
INSERT INTO "recipes" VALUES (58,'Peach Mint Tea','BLACKTEA-BASE',160.0,'g',NULL);
INSERT INTO "recipes" VALUES (59,'Peach Mint Tea','LIME-JUICE',20.0,'g',NULL);
INSERT INTO "recipes" VALUES (60,'Peach Mint Tea','MINT',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (61,'Peach Mint Tea','SYR-PEACH',1.0,'Slice',NULL);
INSERT INTO "recipes" VALUES (62,'Tropical Pine Sunrise','SYR-GRENADINE',15.0,'g',NULL);
INSERT INTO "recipes" VALUES (63,'Tropical Pine Sunrise','SYR-PINEAPPLE',30.0,'g',NULL);
INSERT INTO "recipes" VALUES (64,'Tropical Pine Sunrise','SYR-PINEAPPLE',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (65,'Tropical Pine Sunrise','SODA-WATER',1.0,'nos',NULL);
INSERT INTO "recipes" VALUES (66,'Tropical Pine Sunrise','ORANGE-DRIED',0.5,'pc',NULL);
INSERT INTO "recipes" VALUES (67,'Tropical Pine Sunrise','MINT',1.0,'nos',NULL);
INSERT INTO "recipes" VALUES (68,'Cosmic Lemonade','BUTTERFLY-FLOWER-SYR',40.0,'g',NULL);
INSERT INTO "recipes" VALUES (69,'Cosmic Lemonade','LIME-JUICE',40.0,'g',NULL);
INSERT INTO "recipes" VALUES (70,'Cosmic Lemonade','SYR-YUZU',25.0,'g',NULL);
INSERT INTO "recipes" VALUES (71,'Cosmic Lemonade','SYR-HONEY',5.0,'g',NULL);
INSERT INTO "recipes" VALUES (72,'Cosmic Lemonade','SYR-SIMPLE',10.0,'g',NULL);
INSERT INTO "recipes" VALUES (73,'Cosmic Lemonade','SODA-WATER',1.0,'nos',NULL);
INSERT INTO "recipes" VALUES (74,'Affogato','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (75,'Affogato','GELATO ',120.0,'g',NULL);
INSERT INTO "recipes" VALUES (76,'Oat Milk','MILK-OAT',155.0,'g',NULL);
INSERT INTO "recipes" VALUES (77,'Flavoured Syrups ','Flavoured-Syrups ',15.0,'g',NULL);
INSERT INTO "recipes" VALUES (78,'Double Shot Espresso ','CF-BEAN',18.0,'g',NULL);
INSERT INTO "recipes" VALUES (79,'Strawberry Compote','LEMON',90.0,'g',NULL);
INSERT INTO "recipes" VALUES (80,'Strawberry Compote','STRAWBERRY',1000.0,'g',NULL);
INSERT INTO "recipes" VALUES (81,'Strawberry Compote','SUGAR',880.0,'g',NULL);
INSERT INTO "recipes" VALUES (82,'BUTTERFLY-FLOWER-SYR','BUTTERFLY-PEA-FLOWER',7.0,'g',NULL);
INSERT INTO "recipes" VALUES (83,'BUTTERFLY-FLOWER-SYR','SUGAR',200.0,'g',NULL);
INSERT INTO "recipes" VALUES (84,'BLACKTEA-BASE','TEA-CEYLON',75.0,'g',NULL);
INSERT INTO "recipes" VALUES (85,'BLACKTEA-BASE','BROWN-SUGAR',430.0,'g',NULL);
INSERT INTO "suppliers" VALUES (1,'Ghostbird','Afiq','011-16388950');
INSERT INTO "suppliers" VALUES (2,'Ichiban Pacific','Jack','018-3753668');
INSERT INTO "suppliers" VALUES (3,'Chocalte Conerge','Yatze','016-6031497');
INSERT INTO "suppliers" VALUES (4,'Bidfood','Khoo','014-7268097');
INSERT INTO "suppliers" VALUES (5,'Lucky Frozen','CK',NULL);
INSERT INTO "suppliers" VALUES (6,'Milk','Alya','014-62667943');
INSERT INTO "suppliers" VALUES (7,'Secai Marche','Best Supply',' 011-27511759');
INSERT INTO "suppliers" VALUES (8,'Shopee',NULL,NULL);
INSERT INTO "suppliers" VALUES (9,'Soda Express',NULL,NULL);
INSERT INTO "transactions" VALUES (1,1,1,1.71,'2025-11-12 15:32:55','completed');
INSERT INTO "transactions" VALUES (4,1,1,1.71,'2025-11-22 15:39:51','completed');
INSERT INTO "transactions" VALUES (5,3,10,17.1,'2025-11-24 06:16:46','completed');
INSERT INTO "transactions" VALUES (6,18,5,21.75,'2025-11-24 08:18:35','completed');
INSERT INTO "users" VALUES (1,'admin','$2b$12$aeOy.POeSlPhZ5D8LAkSvOhHeaNc2bVqf8maa5qOCSo.OZPXK5h.S','staff');
INSERT INTO "users" VALUES (2,'SuperAdmin','$2b$12$fDjeoEoWVrQvz8YzUIy/7.22UhW/gYza1clnDUd5EMIQaNd6pX/Qm','superadmin');
INSERT INTO "users" VALUES (3,'Jamal','$2b$12$qD8VOfeeKvaT6UYzBpN4..MPFLh29zzCWZSnHIctw.GnuNgSg5H0G','staff');
COMMIT;
