from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, FloatType, IntegerType
from pyspark.sql.functions import from_json, col
import logging

# Create Spark session
spark = SparkSession \
    .builder \
    .appName("SparkStructuredStreaming") \
    .config("spark.cassandra.connection.host", "172.18.0.5") \
    .config("spark.cassandra.connection.port", "9042") \
    .config("spark.cassandra.auth.username", "cassandra") \
    .config("spark.cassandra.auth.password", "cassandra") \
    .config("spark.driver.host", "172.18.0.2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Define schema
odometrySchema = StructType([
    StructField("id", IntegerType(), False),
    StructField("posex", FloatType(), False),
    StructField("posey", FloatType(), False),
    StructField("posez", FloatType(), False),
    StructField("orientx", FloatType(), False),
    StructField("orienty", FloatType(), False),
    StructField("orientz", FloatType(), False),
    StructField("orientw", FloatType(), False)
])

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "172.18.0.4:9092") \
    .option("subscribe", "rosmsgs") \
    .option("startingOffsets", "earliest") \
    .load()

# Apply schema
df1 = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), odometrySchema).alias("data")) \
    .select("data.*")

# Function to write to Cassandra with validation
def writeToCassandra(writeDF, _):
    # Check if 'id' column has null values
    null_id_count = writeDF.filter(col("id").isNull()).count()
    
    if null_id_count > 0:
        logging.error(f"Skipped writing to Cassandra: {null_id_count} records have null 'id' values.")
        return  # Skip this batch

    # Proceed to write to Cassandra if validation passes
    record_count = writeDF.count()

    writeDF.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode('append') \
        .options(table="odometry", keyspace="ros") \
        .save()

# Write to Cassandra
df1.writeStream \
    .foreachBatch(writeToCassandra) \
    .outputMode("update") \
    .start() \
    .awaitTermination()
