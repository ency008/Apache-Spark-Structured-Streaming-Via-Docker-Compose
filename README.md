# SparkKafkaCassandraFlow
Project Description: Kafka-Spark-Cassandra Data Pipeline Project Overview:  This project aims to establish a robust and scalable data pipeline that efficiently ingests, processes, and stores real-time data. 



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
      - ./spark_run:/opt/bitnami/spark/home

See ```docker-compose.yml```

```
version: '3'

networks:
    datapipeline:
        driver: bridge
        ipam:
            driver: default
            config:
                - subnet: "172.18.0.0/16"

```


### 3. Running docker-compose file
Open your workspace folder which includes all files provided and run the given command as below.
```
# run docker-compose file
docker-compose up
```
After all container is running, you can set up your environment.

#### Prepare Kafka for Use Case
First of all, we will create a new Kafka topic namely *rosmsgs* for ROS odom data using the given commands:
```
# Execute kafka container with container id given above
docker exec -it kafka bash

# Create Kafka "odometry" topic for ROS odom data
kafka$ bin/kafka-topics.sh --create --topic rosmsgs --partitions 1 --replication-factor 1 -bootstrap-server localhost:9092
```
#### Check Kafka setup through Zookeeper
```
# Execute zookeeper container with container id given above
docker exec -it zookeeper bash

# run command
opt/bitnami/zookeeper/bin/zkCli.sh -server localhost:2181

# list all brokers topic
ls /brokers/topics
```

#### Prepare Cassandra for Use Case
Initially, we will create a *keyspace* and then a *topic* in it using given command:
```
# Execute cassandra container with container id given above
docker exec -it cassandra bash

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
We will write streaming script that read *odometry* topic from Kafka, analyze it and then write results to Cassandra. 
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
Then, we create a Spark Session and specify our config h

In order to read Kafka stream, we use **readStream()** and specify Kafka configurations


### 5. Demonstration & Results



# open  terminal and run random_kafka.py
```
python3 random_kafka.py
```
#### (Option-1) Start Streaming to Console
```
# Execute spark container with container id given above
docker exec -it spark_master bash
```
# go to /home and run given command
```
cd home
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0 streamingKafka2Console.py
```

#### (Option-2) Start Streaming to Cassandra
```
# Execute spark container with container id given above
docker exec -it spark_master bash

# go to /home and run given command
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0,com.datastax.spark:spark-cassandra-connector_2.12:3.0.0 streamingKafka2Cassandra.py
```

After all the process is done, we got the data in our Cassandra table as the given below:

You can query the given command to see your table:
```
docker exec -it cassandra bash
# Then write select query to see content of the table
cqlsh -u cassandra -p cassandra
cqlsh> select * from ros.odometry;
```

