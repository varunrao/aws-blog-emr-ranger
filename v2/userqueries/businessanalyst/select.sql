SELECT product_category,
       sum(total_sales) AS total_sales
FROM processed.sales
GROUP BY product_category
ORDER BY total_sales DESC
