

#### Run the given code and analysis the data we will use
This script publishes random odometry data  So, we can see the published data with the given command:

```
# run the script environment
python3 random_kafka.py

```
 
### 2. Prepare Docker-Compose File
First of all, we generated a network called datapipeline for the architecture. The architecture consists of 4 services and each has a static IP address and uses the default port as the given below:
- Spark: 172.18.0.2
- Zookeeper: 172.18.0.3
- Kafka: 172.18.0.4
- Cassandra : 172.18.0.5

We use "volumes" to import our scripts to containers.
>:exclamation: You have to implement " ../streamingProje:/home"  part for your system.

You can access the [docker-compose](https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/docker-compose.yml) and repleca your configs.

```
version: '3'

networks:
    datapipeline:
        driver: bridge
        ipam:
            driver: default
            config:
                - subnet: "172.18.0.0/16"


services:  
  spark:
    image: docker.io/bitnami/spark:3
    container_name: spark_master
    hostname: spark_master
    user: root
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    ports:
      - '8080:8080'
    volumes:
      - ../streamingProje:/home
      - /opt/spark/conf/spark-defaults.conf:/opt/bitnami/spark/conf/spark-defaults.conf
      - /opt/spark/jars:/opt/bitnami/spark/ivy:z
    networks:
      datapipeline:
        ipv4_address: 172.18.0.2

  zookeeper:
    image: 'bitnami/zookeeper:latest'
    container_name: zookeeper
    hostname: zookeeper
    ports:
      - '2181:2181'
    environment:
      - ALLOW_ANONYMOUS_LOGIN=yes
    networks:
      datapipeline:
        ipv4_address: 172.18.0.3

  kafka:
    image: 'bitnami/kafka:latest'
    container_name: kafka
    hostname: kafka
    ports:
      - '9092:9092'
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_CFG_LISTENERS=PLAINTEXT://172.18.0.4:9092
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://172.18.0.4:9092
      - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
      - ALLOW_PLAINTEXT_LISTENER=yes
    depends_on:
      - zookeeper
    volumes:
      - ../streamingProje:/home
    networks:
      datapipeline:
        ipv4_address: 172.18.0.4

  cassandra:
    image: 'bitnami/cassandra:latest'
    container_name: cassandra
    hostname: cassandra
    ports:
      - '9042:9042'
    volumes:
      - ../streamingProje:/home
    networks:
      datapipeline:
        ipv4_address: 172.18.0.5
```


### 3. Running docker-compose file
Open your workspace folder which includes all files provided and run the given command as below.
```
# run docker-compose file
docker-compose up
```
You will have a view like:
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/docker_ps_output.jpg"> 
</p>
After all container is running, you can set up your environment.

#### Prepare Kafka for Use Case
First of all, we will create a new Kafka topic namely *odometry* for ROS odom data using the given commands:
```
# Execute kafka container with container id given above
docker exec -it 1c31511ce206 bash

# Create Kafka "odometry" topic for ROS odom data
kafka$ bin/kafka-topics.sh --create --topic odom --partitions 1 --replication-factor 1 -bootstrap-server localhost:9092
```
#### Check Kafka setup through Zookeeper
```
# Execute zookeeper container with container id given above
docker exec -it 1c31511ce206 bash

# run command
opt/bitnami/zookeeper/bin/zkCli.sh -server localhost:2181

# list all brokers topic
ls /brokers/topics
```
You will have a view like:
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/zookeeper.jpg"> 
</p>

#### Prepare Cassandra for Use Case
Initially, we will create a *keyspace* and then a *topic* in it using given command:
```
# Execute cassandra container with container id given above
docker exec -it 1c31511ce206 bash

# Open the cqlsh
cqlsh -u cassandra -p cassandra

# Run the command to create 'ros' keyspace
cqlsh> CREATE KEYSPACE ros WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};

# Then, run the command to create 'odometry' topic in 'ros'
cqlsh> create table ros.odometry(
        id int primary key, 
        posex float,
        posey float,
        posez float,
        orientx float,
        orienty float,
        orientz float,
        orientw float);

# Check your setup is correct
cqlsh> DESCRIBE ros.odometry
```
> :warning: **The content of topic has to be the same as Spark schema**: Be very careful here!

### 4. Prepare Apache Spark structured streaming
You are able to write analysis results to either console or Cassandra.
#### (First Way) Prepare Apache Spark Structured Streaming Pipeline Kafka to Cassandra
We will write streaming script that read *odometry* topic from Kafka, analyze it and then write results to Cassandra. We will use [streamingKafka2Cassandra.py](https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/streamingKafka2Cassandra.py) to do it.

First of all, we create a schema same as we already defined in Cassandra.
> :warning: **The content of schema has to be the same as Casssandra table**: Be very careful here!

```python3
odometrySchema = StructType([
                StructField("id",IntegerType(),False),
                StructField("posex",FloatType(),False),
                StructField("posey",FloatType(),False),
                StructField("posez",FloatType(),False),
                StructField("orientx",FloatType(),False),
                StructField("orienty",FloatType(),False),
                StructField("orientz",FloatType(),False),
                StructField("orientw",FloatType(),False)
            ])
```
Then, we create a Spark Session and specify our config here:
```python3
spark = SparkSession \
    .builder \
    .appName("SparkStructuredStreaming") \
    .config("spark.cassandra.connection.host","172.18.0.5")\
    .config("spark.cassandra.connection.port","9042")\
    .config("spark.cassandra.auth.username","cassandra")\
    .config("spark.cassandra.auth.password","cassandra")\
    .config("spark.driver.host", "localhost")\
    .getOrCreate()
```

In order to read Kafka stream, we use **readStream()** and specify Kafka configurations as the given below:
```python3
df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "172.18.0.4:9092") \
  .option("subscribe", "rosmsgs") \
  .option("delimeter",",") \
  .option("startingOffsets", "earliest") \
  .load() 
```
Since Kafka send data as binary, first we need to convert the binary value to String using **selectExpr()** as the given below:
```python3
df1 = df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"),odometrySchema).alias("data")).select("data.*")
df1.printSchema()
```
Although Apache Spark isn't capable of directly write stream data to Cassandra yet (using **writeStream()**), we can do it with use **foreachBatch()** as the given below:
```python3
def writeToCassandra(writeDF, _):
  writeDF.write \
    .format("org.apache.spark.sql.cassandra")\
    .mode('append')\
    .options(table="odometry", keyspace="ros")\
    .save()

df1.writeStream \
    .foreachBatch(writeToCassandra) \
    .outputMode("update") \
    .start()\
    .awaitTermination()
df1.show()
```
Finally, we got the given script [streamingKafka2Cassandra.py](https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/streamingKafka2Cassandra.py):
```python3
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType,StructField,FloatType,IntegerType
from pyspark.sql.functions import from_json,col

odometrySchema = StructType([
                StructField("id",IntegerType(),False),
                StructField("posex",FloatType(),False),
                StructField("posey",FloatType(),False),
                StructField("posez",FloatType(),False),
                StructField("orientx",FloatType(),False),
                StructField("orienty",FloatType(),False),
                StructField("orientz",FloatType(),False),
                StructField("orientw",FloatType(),False)
            ])

spark = SparkSession \
    .builder \
    .appName("SparkStructuredStreaming") \
    .config("spark.cassandra.connection.host","172.18.0.5")\
    .config("spark.cassandra.connection.port","9042")\
    .config("spark.cassandra.auth.username","cassandra")\
    .config("spark.cassandra.auth.password","cassandra")\
    .config("spark.driver.host", "localhost")\
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")


df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "172.18.0.4:9092") \
  .option("subscribe", "rosmsgs") \
  .option("delimeter",",") \
  .option("startingOffsets", "earliest") \
  .load() 

df.printSchema()

df1 = df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"),odometrySchema).alias("data")).select("data.*")
df1.printSchema()


def writeToCassandra(writeDF, _):
  writeDF.write \
    .format("org.apache.spark.sql.cassandra")\
    .mode('append')\
    .options(table="odometry", keyspace="ros")\
    .save()

df1.writeStream \
    .foreachBatch(writeToCassandra) \
    .outputMode("update") \
    .start()\
    .awaitTermination()
df1.show()
```
#### (Second Way) Prepare Apache Spark Structured Streaming Pipeline Kafka to Console
There are a few differences between writing to the console and writing to Cassandra. We directly srite stream to console.
With **writeStream()** we can write stream data directly to the console.
```python3
df1.writeStream \
  .outputMode("update") \
  .format("console") \
  .option("truncate", False) \
  .start() \
  .awaitTermination()
```
The rest of the process takes place in the same way as the previous one. Finally, we got the given script [streamingKafka2Console.py](https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/streamingKafka2Console.py):
```python3
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType,StructField,LongType,IntegerType,FloatType,StringType
from pyspark.sql.functions import split,from_json,col

odometrySchema = StructType([
                StructField("id",IntegerType(),False),
                StructField("posex",FloatType(),False),
                StructField("posey",FloatType(),False),
                StructField("posez",FloatType(),False),
                StructField("orientx",FloatType(),False),
                StructField("orienty",FloatType(),False),
                StructField("orientz",FloatType(),False),
                StructField("orientw",FloatType(),False)
            ])

spark = SparkSession \
    .builder \
    .appName("SSKafka") \
    .config("spark.driver.host", "localhost")\
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "172.18.0.4:9092") \
  .option("subscribe", "rosmsgs") \
  .option("delimeter",",") \
  .option("startingOffsets", "earliest") \
  .load() 

df.printSchema()

df1 = df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"),odometrySchema).alias("data")).select("data.*")
df1.printSchema()

df1.writeStream \
  .outputMode("update") \
  .format("console") \
  .option("truncate", False) \
  .start() \
  .awaitTermination()
```

<!-- If you are sure that all preparations are done, you can start a demo. You have to follow the given steps .

#### Start ROS and publish odom data to Kafka.
- roscore : starts ROS master
- odomPublisher.py : generates random odom data and publishes them along network
- ros2Kafka.py : subscribes odom topic and writes odom data into kafka container
```
# these all are implemented in your local pc
# open a terminal and start roscore
roscore -->

### 5. Demonstration & Results



# open  terminal and run odomPublisher.py
python3 random_kafka.py
```
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/odomPublisher.jpg"> 
</p>

```
# open another terminal and run ros2Kafka.py
python3 random_kafka.py
```

<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/ros2kafka.jpg"> 
</p>

#### (Option-1) Start Streaming to Console
```
# Execute spark container with container id given above
docker exec -it e3080e48085c bash

# go to /home and run given command
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0 streamingKafka2Console.py
```

#### (Option-2) Start Streaming to Cassandra
```
# Execute spark container with container id given above
docker exec -it e3080e48085c bash

# go to /home and run given command
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0,com.datastax.spark:spark-cassandra-connector_2.12:3.0.0 streamingKafka2Console.py
```
After the spark job is started, you can see the schema on screen.
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/schema.jpg"> 
</p>

If you run option-1, you will have a view as the given below on your terminal screen.
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/streaming.jpg"> 
</p>


After all the process is done, we got the data in our Cassandra table as the given below:

You can query the given command to see your table:
```
# Then write select query to see content of the table
cqlsh> select * from ros.odometry
```
<p align="center" width="100%">
    <img src="https://github.com/zekeriyyaa/Apache-Spark-Structured-Streaming-Via-Docker-Compose/blob/main/img/cassandra.jpg"> 
</p>

