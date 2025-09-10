#!/bin/bash
set -e

info() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S,%3N')] INFO $1"
}

warn() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S,%3N')] WARN $1"
}

error() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S,%3N')] ERROR $1"
}

info "Starting Kafka topics creation."

# Wait for Kafka to be fully up
RETRY_LIMIT=10
RETRY_INTERVAL=5

for ((i=1;i<=RETRY_LIMIT;i++)); do
  info "⏳ Checking if Kafka broker is reachable (attempt $i)."
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server "$KAFKA_BROKER" --list > /dev/null 2>&1 && break
  warn "⚠️ Kafka broker not reachable yet. Sleeping $RETRY_INTERVAL seconds."
  sleep $RETRY_INTERVAL
done

if [ $i -gt $RETRY_LIMIT ]; then
  error "Failed to reach Kafka broker after $RETRY_LIMIT attempts. Check Kafka broker logs. Exiting."
  exit 1
fi

info "✅ Kafka broker is reachable."

# Create Kafka Topics
IFS=',' read -ra TOPIC_ARRAY <<< "$TOPICS"

for TOPIC_NAME in "${TOPIC_ARRAY[@]}"; do
  info "⏳ Creating topic: $TOPIC_NAME with $PARTITIONS partitions and replication factor $REPLICATION_FACTOR."
  /opt/kafka/bin/kafka-topics.sh --create \
     --if-not-exists \
     --topic "$TOPIC_NAME" \
     --bootstrap-server "$KAFKA_BROKER" \
     --partitions "$PARTITIONS" \
     --replication-factor "$REPLICATION_FACTOR" 2>&1
done

# Check if Kafka Topics Creation Success or Not and is Available
for attempt in $(seq 1 "$RETRY_LIMIT"); do
  EXISTING_TOPICS=$(/opt/kafka/bin/kafka-topics.sh --bootstrap-server "$KAFKA_BROKER" --list 2>/dev/null)

  MISSING_TOPICS=()
  for TOPIC_NAME in "${TOPIC_ARRAY[@]}"; do
    echo "$EXISTING_TOPICS" | grep -q "^${TOPIC_NAME}$" || MISSING_TOPICS+=("$TOPIC_NAME")
  done

  if [ ${#MISSING_TOPICS[@]} -eq 0 ]; then
    info "✅ All topics are available in the Kafka broker. Found topics: ${TOPIC_ARRAY[*]}"
    info "Exiting..."
    exit 0
  fi

  warn "⚠️ Missing topics: ${MISSING_TOPICS[*]}. Retrying in ${RETRY_INTERVAL}s... ($attempt/$RETRY_LIMIT)"
  sleep "$RETRY_INTERVAL"
done

error "All Kafka topics not found. Missing topics: ${MISSING_TOPICS[*]}"
exit 1