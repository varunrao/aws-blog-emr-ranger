/* Explore staging data */
SELECT *
FROM orders
LIMIT 10;


SELECT *
FROM products limit 10;

/* Simple query to get the total sales by category - data engineer can you help build a pipeline for this?*/
SELECT sum(orders.price) total_sales, products.sku, products.product_category
        FROM orders join products where orders.sku = products.sku
        group by products.sku, products.product_category LIMIT 10;


SELECT *
FROM customers
LIMIT 10;
