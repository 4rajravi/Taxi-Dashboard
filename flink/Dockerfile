FROM flink:1.18.1

COPY requirements.txt .

# Environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64 \
    PATH="${JAVA_HOME}/bin:${PATH}"

RUN apt-get update -y && \
    # Install Python3, pip3, Java 17 JDK
    apt-get install -y python3 python3-pip python3-dev openjdk-17-jdk && \
    # Clean up
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    # Set 'python' to point to 'python3'
    ln -sf /usr/bin/python3 /usr/bin/python && \
    # Install dependencies (Apache Flink Libraries, Apache Flink, Orjson)
    pip3 install --no-cache-dir -r requirements.txt && \
    # Download flink-connector-kafka 1.18 and save to path /opt/flink/lib
    wget -P /opt/flink/lib https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-kafka/3.2.0-1.18/flink-connector-kafka-3.2.0-1.18.jar  && \
    # Download Kafka client JAR (version 3.6.0 is compatible with Flink 1.18.x Kafka connector 3.2.x)
    wget -P /opt/flink/lib https://repo.maven.apache.org/maven2/org/apache/kafka/kafka-clients/3.6.0/kafka-clients-3.6.0.jar
