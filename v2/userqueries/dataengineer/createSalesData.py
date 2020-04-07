from pyspark import SparkContext
from pyspark import SQLContext

# Initialize spark SQL context
sqlContext = SQLContext(sparkContext=sc)

# Join orders and products to get the sales rollup
productsFile = sqlContext.read.parquet("s3://aws-bigdata-blog/artifacts/aws-blog-emr-ranger-v2/data/staging/products/")

productsFile.registerTempTable("products")

productsFile.write.mode("overwrite").format("parquet").option("path", "<s3 path>").saveAsTable("staging.products")

# Load orders data from S3 into Datafram
ordersFile = sqlContext.read.parquet("<s3 path>")

ordersFile.registerTempTable("orders")

#ordersFile.write.mode("overwrite").saveAsTable("retail.orders")

ordersFile.write.mode("overwrite").format("parquet").option("path", "<s3 path>").saveAsTable("staging.orders")

# Load orders data from S3 into Datafram
customersFile = sqlContext.read.parquet("<s3 path>")

customersFile.registerTempTable("customers")

#ordersFile.write.mode("overwrite").saveAsTable("retail.orders")

customersFile.write.mode("overwrite").format("parquet").option("path", "<s3 path>").saveAsTable("staging.customers")

# Join orders and products to get the sales rollup
sales_breakup_sql = sqlContext.sql("SELECT sum(orders.price) total_sales, products.sku, products.product_category "
                                   " FROM orders join products where orders.sku = products.sku group by products.sku, products.product_category")

#products_all = products_sql.map(lambda p: "Counts: {0} Ipsum Comment: {1}".format(p.name, p.comment_col))
sales_breakup_sql.show(n=2)

# Write output back to s3 under processed
sales_breakup_sql.write.mode('overwrite').format("parquet").option("path", "<s3 path>").saveAsTable("processed.sales")
