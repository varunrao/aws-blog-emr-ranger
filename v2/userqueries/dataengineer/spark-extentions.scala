import org.apache.spark.sql.internal.StaticSQLConf
val catalogType = spark.conf.get(StaticSQLConf.CATALOG_IMPLEMENTATION.key)
val extenstion = spark.conf.get(StaticSQLConf.SPARK_SESSION_EXTENSIONS.key)

sql("select * from retail.products").show()

//productsFile = sqlContext.read.parquet("s3://aws-datalake-security-data-vbhamidi-us-east-1/rawdata/products/")
//productsFile.show(n=2)
