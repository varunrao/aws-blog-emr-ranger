import org.apache.spark.sql.internal.StaticSQLConf
val catalogType = spark.conf.get(StaticSQLConf.CATALOG_IMPLEMENTATION.key)
val extenstion = spark.conf.get(StaticSQLConf.SPARK_SESSION_EXTENSIONS.key)

sql("select * from staging.products").show()
