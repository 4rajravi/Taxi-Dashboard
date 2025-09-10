#!/bin/sh
set -e

info() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO $1"
}

warn() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN $1"
}

error() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR $1"
}

FLINK_API="http://flink-jobmanager:8081"
JOB_NAME="FlinkDataStreamingJob"
RETRY_LIMIT=12
RETRY_INTERVAL=5

info "Starting Flink job submission."

# Wait for Flink Cluster to be Ready
info "⏳ Waiting for Flink cluster to become available..."

for i in $(seq 1 $RETRY_LIMIT); do
  if curl -sf "${FLINK_API}/overview" > /dev/null; then
    info "✅ Flink cluster is reachable."
    break
  fi
  warn "⚠️ Flink cluster not ready. Retrying in ${RETRY_INTERVAL}s... ($i/$RETRY_LIMIT)"
  sleep "${RETRY_INTERVAL}"
  if [ "$i" -eq "$RETRY_LIMIT" ]; then
    error "❌ Flink cluster did not become ready in time."
    exit 1
  fi
done

# Submit Flink Job
info "⏳ Submitting Flink job '${JOB_NAME}'..."

if ./bin/flink run --jobmanager flink-jobmanager:8081 --detached --python /opt/flink/jobs/main.py; then
  info "✅ Flink job '${JOB_NAME}' submitted successfully."
else
  error "❌ Flink job '${JOB_NAME}' submission failed."
  exit 1
fi

# Wait for Flink Job to Reach RUNNING
info "⏳ Waiting for job '${JOB_NAME}' to reach RUNNING state..."

for i in $(seq 1 $RETRY_LIMIT); do
  output=$(curl -fs "${FLINK_API}/jobs/overview" || true)

  echo "$output" | grep -q "\"name\":\"${JOB_NAME}\"" &&
  echo "$output" | grep -q "\"state\":\"RUNNING\"" && {
    info "✅ Flink job '${JOB_NAME}' is RUNNING."
    info "Exiting..."
    exit 0
  }

  warn "⚠️ Flink job ${JOB_NAME} not yet RUNNING. Retrying in ${RETRY_INTERVAL}s... ($i/$RETRY_LIMIT)"
  sleep "$RETRY_INTERVAL"
done

error "❌ Flink job '${JOB_NAME}' did not reach RUNNING state in time."
exit 1
