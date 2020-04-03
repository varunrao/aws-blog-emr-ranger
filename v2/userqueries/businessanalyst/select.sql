select product_category, sum(total_sales) as total_sales from processed.sales group by product_category order by total_sales desc
