import asyncio
import time
import os
from datetime import datetime, timezone
import json

try:
    from aiokafka import AIOKafkaConsumer  # type: ignore

    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    print("aiokafka not found. Kafka functionality will be disabled.")
    print("To enable Kafka analysis, install with: pip install aiokafka")

try:
    import plotly.graph_objects as go  # type: ignore
    import plotly.express as px  # type: ignore
    from plotly.offline import plot  # type: ignore
    import numpy as np  # type: ignore

    PLOTLY_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError as e:
    PLOTLY_AVAILABLE = False
    NUMPY_AVAILABLE = False
    print("Plotly or numpy not found. Advanced analysis will be limited.")
    print("To enable full analysis, install with: pip install plotly kaleido numpy")
    if "numpy" not in str(e):
        try:
            import numpy as np  # type: ignore

            NUMPY_AVAILABLE = True
        except ImportError:
            pass

BROKER = "localhost:9094"  # Kafka Broker EXTERNAL listener
TOPIC = "taxi.processed_data.stream"  # Kafka sink topic for processed data
WINDOW_SIZE_MS = 60 * 1000  # 1 minute window in milliseconds
BATCH_SIZE = 1000  # Process messages in batches for better performance
MAX_MESSAGES = 300000  # Stop after processing this many messages

results = []


def create_event_latency_per_message_visualization(
    all_messages, output_file="results/event_latency_per_message_chart.html"
):
    """
    Create a visualization showing event latency for each record/message
    """
    if not PLOTLY_AVAILABLE:
        print("Plotly not available. Skipping event latency visualization.")
        return None

    if not all_messages:
        print("No messages to visualize!")
        return None

    # Extract latency data for each message
    record_numbers = []
    latencies_seconds = []
    timestamps = []

    for i, message in enumerate(all_messages):
        sent_at_ms = message.get("sent_at_utc_ms")
        processed_at_ms = message.get("processed_at_utc_ms")

        if sent_at_ms is not None and processed_at_ms is not None:
            latency_ms = processed_at_ms - sent_at_ms
            if latency_ms >= 0:  # Only include non-negative latencies
                record_numbers.append(i + 1)  # Record count starting from 1
                latencies_seconds.append(latency_ms / 1000)  # Convert to seconds
                timestamps.append(
                    datetime.fromtimestamp(
                        processed_at_ms / 1000, tz=timezone.utc
                    ).isoformat()
                )

    if not record_numbers:
        print("No valid latency data found for event latency visualization!")
        return None

    # Create the figure
    fig = go.Figure()

    # Add scatter plot with gradient fill
    fig.add_trace(
        go.Scatter(
            x=record_numbers,
            y=latencies_seconds,
            mode="markers",
            name="Event Latency Per Message",
            marker=dict(
                color=latencies_seconds,
                colorscale="Viridis",
                size=4,
                colorbar=dict(title="Latency (s)"),
            ),
            hovertemplate="<b>Message:</b> %{x}<br>"
            + "<b>Latency:</b> %{y:.3f} seconds<br>"
            + "<b>Time:</b> %{customdata}<br>"
            + "<extra></extra>",
            customdata=timestamps,
        )
    )

    # Update layout
    fig.update_layout(
        title={
            "text": "Event Latency Per Message",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20},
        },
        xaxis=dict(
            title=dict(text=f"Number of Messages in Topic {TOPIC}", font=dict(size=14)),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
        ),
        yaxis=dict(
            title=dict(text="Event Latency in Seconds", font=dict(size=14)),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
            tickformat=".1f",
        ),
        hovermode="closest",
        template="plotly_white",
        width=1200,
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )

    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save as HTML (interactive)
    html_file = output_file
    fig.write_html(html_file)
    print(f"Event latency chart saved as: {html_file}")

    # Save as static image (PNG)
    png_file = output_file.replace(".html", ".png")
    try:
        fig.write_image(png_file, width=1200, height=600, scale=3)
        print(f"Static event latency chart saved as: {png_file}")
        return png_file
    except Exception as e:
        print(f"Could not save PNG (requires kaleido): {e}")
        print("Please install with: pip install kaleido")
        return html_file


def create_event_latency_vs_load_visualization(
    results,
    all_messages,
    output_file="results/event_latency_vs_load_chart.html",
):
    """
    Create an enhanced visualization showing how latency varies with taxi count including percentiles and performance zones
    """
    if not PLOTLY_AVAILABLE:
        print(
            "Plotly not available. Skipping enhanced latency vs taxi count visualization."
        )
        return None

    if not results or not all_messages:
        print("No data to visualize!")
        return None

    # Extract data for plotting - filter out windows with no latency data
    valid_windows = [r for r in results if r.get("latency_samples", 0) > 0]

    if not valid_windows:
        print("No windows with latency data found!")
        return None

    # Calculate percentiles for each taxi count level
    taxi_count_data = {}

    # Group latencies by taxi count windows
    for message in all_messages:
        sent_at_ms = message.get("sent_at_utc_ms")
        processed_at_ms = message.get("processed_at_utc_ms")

        if sent_at_ms is not None and processed_at_ms is not None:
            latency_ms = processed_at_ms - sent_at_ms
            if latency_ms >= 0:
                # Find which window this message belongs to
                for window in valid_windows:
                    if (
                        window["window_start_utc_ms"]
                        <= processed_at_ms
                        < window["window_end_utc_ms"]
                    ):
                        taxi_count = window["cumulative_taxi_count"]
                        if taxi_count not in taxi_count_data:
                            taxi_count_data[taxi_count] = []
                        taxi_count_data[taxi_count].append(
                            latency_ms / 1000
                        )  # Convert to seconds
                        break

    # Calculate statistics for each taxi count level
    taxi_counts = sorted(taxi_count_data.keys())
    mean_latencies = []
    p50_latencies = []
    p95_latencies = []
    p99_latencies = []

    for taxi_count in taxi_counts:
        latencies = taxi_count_data[taxi_count]
        if latencies and NUMPY_AVAILABLE:
            mean_latencies.append(np.mean(latencies))
            p50_latencies.append(np.percentile(latencies, 50))
            p95_latencies.append(np.percentile(latencies, 95))
            p99_latencies.append(np.percentile(latencies, 99))
        elif latencies:
            # Fallback without numpy
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            mean_latencies.append(sum(latencies) / len(latencies))
            p50_latencies.append(sorted_latencies[int(n * 0.5)])
            p95_latencies.append(sorted_latencies[int(n * 0.95)])
            p99_latencies.append(sorted_latencies[int(n * 0.99)])

    if not taxi_counts:
        print("No valid latency data found for enhanced visualization!")
        return None

    # Create the figure
    fig = go.Figure()

    # Add performance zone indicators (background regions)
    max_taxi_count = max(taxi_counts) if taxi_counts else 1000
    max_latency = max(p99_latencies) if p99_latencies else 1.0

    # Performance zones
    fig.add_hrect(
        y0=0,
        y1=1,
        fillcolor="rgba(34, 197, 94, 0.15)",
        line_width=0,
        annotation_text="Excellent Performance (<1s)",
        annotation_position="top left",
    )
    fig.add_hrect(
        y0=1,
        y1=5,
        fillcolor="rgba(132, 204, 22, 0.15)",
        line_width=0,
        annotation_text="Good Performance (1-5s)",
        annotation_position="top left",
    )
    fig.add_hrect(
        y0=5,
        y1=10,
        fillcolor="rgba(245, 158, 11, 0.15)",
        line_width=0,
        annotation_text="Acceptable Performance (5-10s)",
        annotation_position="top left",
    )
    fig.add_hrect(
        y0=10,
        y1=12 if max_latency < 10 else max_latency,
        fillcolor="rgba(239, 68, 68, 0.15)",
        line_width=0,
        annotation_text="Poor Performance (>10s)",
        annotation_position="top left",
    )

    # Add percentile lines
    fig.add_trace(
        go.Scatter(
            x=taxi_counts,
            y=p99_latencies,
            mode="lines+markers",
            name="P99 Latency",
            line=dict(color="#ef4444", width=2, dash="dash"),
            marker=dict(size=4, color="#ef4444"),
            hovertemplate="<b>Taxi Count:</b> %{x}<br><b>P99 Latency:</b> %{y:.3f}s<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=taxi_counts,
            y=p95_latencies,
            mode="lines+markers",
            name="P95 Latency",
            line=dict(color="#f97316", width=2, dash="dot"),
            marker=dict(size=4, color="#f97316"),
            hovertemplate="<b>Taxi Count:</b> %{x}<br><b>P95 Latency:</b> %{y:.3f}s<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=taxi_counts,
            y=p50_latencies,
            mode="lines+markers",
            name="P50 Latency (Median)",
            line=dict(color="#3b82f6", width=2),
            marker=dict(size=5, color="#3b82f6"),
            hovertemplate="<b>Taxi Count:</b> %{x}<br><b>P50 Latency:</b> %{y:.3f}s<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=taxi_counts,
            y=mean_latencies,
            mode="lines+markers",
            name="Mean Latency",
            line=dict(color="#22c55e", width=2),
            marker=dict(size=6, color="#22c55e"),
            hovertemplate="<b>Taxi Count:</b> %{x}<br><b>Mean Latency:</b> %{y:.3f}s<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        title={
            "text": "Pipeline Performance Analysis: Event Latency vs Pipeline Load with Percentiles",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20},
        },
        xaxis=dict(
            title=dict(text="Number of Taxis (Pipeline Load)", font=dict(size=14)),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
        ),
        yaxis=dict(
            title=dict(
                text="Event Latency in Seconds", font=dict(size=14)
            ),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
            tickformat=".1f",
        ),
        hovermode="x unified",
        template="plotly_white",
        width=1400,
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )

    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save as HTML (interactive)
    html_file = output_file
    fig.write_html(html_file)
    print(f"Enhanced latency vs load chart saved as: {html_file}")

    # Save as static image (PNG)
    png_file = output_file.replace(".html", ".png")
    try:
        fig.write_image(png_file, width=1400, height=700, scale=3)
        print(f"Static event latency vs load chart saved as: {png_file}")
        return png_file
    except Exception as e:
        print(f"Could not save PNG (requires kaleido): {e}")
        print("Please install with: pip install kaleido")
        return html_file


def create_throughput_vs_event_latency_visualization(
    results, all_messages, output_file="results/throughput_vs_event_latency_chart.html"
):
    """
    Create a throughput vs latency visualization showing the performance envelope

    This graph shows the trade-off between throughput (messages processed per second in each window)
    and latency (end-to-end processing time). Fixed to use per-window message counts instead of
    cumulative counts for accurate throughput calculation.
    """
    if not PLOTLY_AVAILABLE:
        print("Plotly not available. Skipping throughput vs latency visualization.")
        return None

    if not results or not all_messages:
        print("No data to visualize!")
        return None

    # Calculate throughput (messages per second) and latency for each window
    throughputs = []
    mean_latencies = []
    p95_latencies = []
    taxi_counts = []

    for i, window in enumerate(results):
        if window.get("latency_samples", 0) > 0:
            # Calculate throughput for this window (messages processed in this window only)
            window_duration_s = (
                window["window_end_utc_ms"] - window["window_start_utc_ms"]
            ) / 1000

            # Count messages processed in this specific window (not cumulative)
            messages_in_window = 0
            for message in all_messages:
                processed_at_ms = message.get("processed_at_utc_ms")
                if (
                    processed_at_ms is not None
                    and window["window_start_utc_ms"]
                    <= processed_at_ms
                    < window["window_end_utc_ms"]
                ):
                    messages_in_window += 1

            throughput = (
                messages_in_window / window_duration_s if window_duration_s > 0 else 0
            )

            # Get latencies for this window
            window_latencies = []
            for message in all_messages:
                processed_at_ms = message.get("processed_at_utc_ms")
                sent_at_ms = message.get("sent_at_utc_ms")

                if (
                    sent_at_ms is not None
                    and processed_at_ms is not None
                    and window["window_start_utc_ms"]
                    <= processed_at_ms
                    < window["window_end_utc_ms"]
                ):
                    latency_ms = processed_at_ms - sent_at_ms
                    if latency_ms >= 0:
                        window_latencies.append(latency_ms / 1000)  # Convert to seconds

            if window_latencies:
                mean_latency = sum(window_latencies) / len(window_latencies)
                if NUMPY_AVAILABLE:
                    p95_latency = np.percentile(window_latencies, 95)
                else:
                    sorted_latencies = sorted(window_latencies)
                    p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]

                throughputs.append(throughput)
                mean_latencies.append(mean_latency)
                p95_latencies.append(p95_latency)
                taxi_counts.append(window["cumulative_taxi_count"])

    if not throughputs:
        print("No valid throughput vs latency data found!")
        return None

    # Create the figure
    fig = go.Figure()

    # Add performance envelope (mean latency)
    fig.add_trace(
        go.Scatter(
            x=throughputs,
            y=mean_latencies,
            mode="markers+lines",
            name="Mean Latency",
            marker=dict(
                size=8,
                color=taxi_counts,
                colorscale="Viridis",
                colorbar=dict(title="Taxi Count"),
                line=dict(width=2, color="white"),
            ),
            line=dict(color="#22c55e", width=2),
            hovertemplate="<b>Throughput:</b> %{x:.1f} msg/s<br>"
            + "<b>Mean Latency:</b> %{y:.3f}s<br>"
            + "<b>Taxi Count:</b> %{marker.color}<br>"
            + "<b>Note:</b> Per-window throughput<br>"
            + "<extra></extra>",
        )
    )

    # Add P95 latency envelope
    fig.add_trace(
        go.Scatter(
            x=throughputs,
            y=p95_latencies,
            mode="markers+lines",
            name="P95 Latency",
            marker=dict(size=6, color="#ef4444"),
            line=dict(color="#ef4444", width=2, dash="dash"),
            hovertemplate="<b>Throughput:</b> %{x:.1f} msg/s<br>"
            + "<b>P95 Latency:</b> %{y:.3f}s<br>"
            + "<extra></extra>",
        )
    )

    # Add performance zones
    max_throughput = max(throughputs) if throughputs else 100
    max_latency = max(p95_latencies) if p95_latencies else 1.0

    # Update layout
    fig.update_layout(
        title={
            "text": "Throughput vs Latency Trade-off",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20},
        },
        xaxis=dict(
            title=dict(text="Throughput (Messages/Second)", font=dict(size=14)),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
        ),
        yaxis=dict(
            title=dict(text="Event Latency in Seconds", font=dict(size=14)),
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#e2e8f0",
            tickformat=".1f",
        ),
        hovermode="closest",
        template="plotly_white",
        width=1400,
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )

    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save as HTML (interactive)
    html_file = output_file
    fig.write_html(html_file)
    print(f"Throughput vs event latency chart saved as: {html_file}")

    # Save as static image (PNG)
    png_file = output_file.replace(".html", ".png")
    try:
        fig.write_image(png_file, width=1400, height=700, scale=3)
        print(f"Static throughput vs event latency chart saved as: {png_file}")
        return png_file
    except Exception as e:
        print(f"Could not save PNG (requires kaleido): {e}")
        print("Please install with: pip install kaleido")
        return html_file


async def consume():
    # Check if aiokafka is available
    if not AIOKAFKA_AVAILABLE:
        print("❌ Cannot proceed: aiokafka is not installed!")
        print("Please install the required dependency: pip install aiokafka")
        print("Or install all dependencies: pip install aiokafka plotly numpy kaleido")
        return

    # Capture the script start time in UTC milliseconds
    script_start_time_ms = int(time.time() * 1000)
    script_start_utc = datetime.fromtimestamp(
        script_start_time_ms / 1000, tz=timezone.utc
    )
    print(
        f"Kafka Streaming Pipeline Benchmarking Script started at: {script_start_utc.isoformat()}"
    )
    print(f"Will process messages with processed_at_utc_ms < {script_start_time_ms}")

    print("Starting Kafka consumer to read ALL messages from the beginning...")
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=[BROKER],
        auto_offset_reset="earliest",  # Read from the beginning of the topic
        enable_auto_commit=False,  # We don't need to commit offsets for this analysis
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=10000,  # Increase timeout to reduce frequent network calls
        fetch_max_bytes=1048576,  # Limit the maximum size of data fetched per request (1 MB)
        max_partition_fetch_bytes=262144,  # Limit the maximum size of data fetched per partition (256 KB)
        request_timeout_ms=30000,  # Increase request timeout to handle larger batches
    )
    await consumer.start()
    print(f"Connected to Kafka broker at {BROKER}, subscribed to topic '{TOPIC}'")

    # Store all messages first to sort by processed_at_utc_ms
    all_messages = []
    messages_after_start = 0  # Count messages that arrived after script start

    try:
        print("Step 1: Reading all existing messages from the topic...")

        # First, collect messages up to the limit or timeout
        message_count = 0
        consecutive_timeouts = 0
        max_consecutive_timeouts = 2  # Reduced to 2 timeouts (10 seconds total)
        start_time = time.time()
        max_wait_time = 10  # Maximum wait time in seconds

        print(f"Will stop after {MAX_MESSAGES} messages or {max_wait_time}s timeout...")

        while (
            consecutive_timeouts < max_consecutive_timeouts
            and message_count < MAX_MESSAGES
            and (time.time() - start_time) < max_wait_time
        ):
            try:
                # Wait for a message with timeout
                msg_batch = await asyncio.wait_for(
                    consumer.getmany(timeout_ms=5000, max_records=BATCH_SIZE),
                    timeout=6.0,
                )

                if not msg_batch:
                    consecutive_timeouts += 1
                    elapsed_time = time.time() - start_time
                    print(
                        f"No messages received (timeout {consecutive_timeouts}/{max_consecutive_timeouts}, elapsed: {elapsed_time:.1f}s)"
                    )
                    continue

                # Reset timeout counter when we receive messages
                consecutive_timeouts = 0

                # Process the batch of messages
                for tp, messages in msg_batch.items():
                    for msg in messages:
                        try:
                            message_data = msg.value
                            if (
                                "processed_at_utc_ms" in message_data
                                and "taxi_id" in message_data
                            ):
                                # Add message regardless of timestamp (remove timestamp filtering)
                                all_messages.append(message_data)
                                message_count += 1

                                if message_count % BATCH_SIZE == 0:
                                    print(f"Collected {message_count} messages...")

                                # Stop if we've reached the limit
                                if message_count >= MAX_MESSAGES:
                                    print(
                                        f"Reached message limit of {MAX_MESSAGES}, stopping collection..."
                                    )
                                    break

                        except Exception as e:
                            print(f"Error processing message: {e}")
                            continue

                    # Break out of outer loop if we've reached the limit
                    if message_count >= MAX_MESSAGES:
                        break

                # Break out of the while loop if we've reached the limit
                if message_count >= MAX_MESSAGES:
                    break

            except asyncio.TimeoutError:
                consecutive_timeouts += 1
                elapsed_time = time.time() - start_time
                print(
                    f"Batch timeout (timeout {consecutive_timeouts}/{max_consecutive_timeouts}, elapsed: {elapsed_time:.1f}s)"
                )
                continue

        final_elapsed_time = time.time() - start_time
        if message_count >= MAX_MESSAGES:
            stop_reason = f"Reached message limit of {MAX_MESSAGES}"
        elif final_elapsed_time >= max_wait_time:
            stop_reason = f"Reached timeout of {max_wait_time}s"
        else:
            stop_reason = f"No more messages after {consecutive_timeouts} timeouts"

        print(f"Step 2: Finished collecting messages.")
        print(f"Stop reason: {stop_reason}")
        print(f"Total messages collected: {len(all_messages)}")
        print(f"Total elapsed time: {final_elapsed_time:.1f}s")
        print(f"Message limit: {MAX_MESSAGES}")

        print(f"Step 3: Sorting {len(all_messages)} messages by UTC timestamp...")

        # Sort messages by processed_at_utc_ms to process them in chronological order
        all_messages.sort(key=lambda x: x["processed_at_utc_ms"])

        if not all_messages:
            print("No valid messages found!")
            return

        # Get the first and last timestamps for analysis scope
        first_timestamp_ms = all_messages[0]["processed_at_utc_ms"]
        last_timestamp_ms = all_messages[-1]["processed_at_utc_ms"]

        print(f"Analysis time range:")
        print(
            f"  First message: {datetime.fromtimestamp(first_timestamp_ms/1000, tz=timezone.utc).isoformat()}"
        )
        print(
            f"  Last message:  {datetime.fromtimestamp(last_timestamp_ms/1000, tz=timezone.utc).isoformat()}"
        )
        print(f"  Total messages: {len(all_messages)}")
        print(f"  Message limit applied: {MAX_MESSAGES}")

        # Initialize windowing variables
        current_window_start = (
            first_timestamp_ms // WINDOW_SIZE_MS
        ) * WINDOW_SIZE_MS  # Align to window boundary
        cumulative_taxis = set()
        total_messages = 0
        window_latencies = []  # Store latencies for current window

        print(
            f"Step 4: Processing messages in {WINDOW_SIZE_MS/1000}s windows with latency analysis..."
        )

        for message in all_messages:
            processed_at_ms = message["processed_at_utc_ms"]
            sent_at_ms = message.get("sent_at_utc_ms")
            taxi_id = message.get("taxi_id")

            # Check if we need to start a new window
            while processed_at_ms >= current_window_start + WINDOW_SIZE_MS:
                # Calculate mean latency for completed window
                mean_latency_ms = (
                    sum(window_latencies) / len(window_latencies)
                    if window_latencies
                    else 0
                )

                # Record results for the completed window
                window_end = current_window_start + WINDOW_SIZE_MS
                window_start_utc = datetime.fromtimestamp(
                    current_window_start / 1000, tz=timezone.utc
                )

                entry = {
                    "window_start_utc_ms": current_window_start,
                    "window_end_utc_ms": window_end,
                    "cumulative_taxi_count": len(cumulative_taxis),
                    "total_messages": total_messages,
                    "mean_latency_ms": round(mean_latency_ms, 2),
                    "latency_samples": len(window_latencies),
                    "timestamp_utc": window_start_utc.isoformat(),
                }
                results.append(entry)

                # Progress update
                if len(results) % 10 == 0:
                    print(
                        f"Completed window {len(results)}: {window_start_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} - "
                        f"Cumulative taxis: {len(cumulative_taxis)}, Total messages: {total_messages}, "
                        f"Mean latency: {mean_latency_ms:.1f}ms"
                    )

                # Move to next window and reset latency tracking
                current_window_start += WINDOW_SIZE_MS
                window_latencies = []

            # Process the current message
            if taxi_id is not None:
                cumulative_taxis.add(taxi_id)

            # Calculate and store latency for this message
            if sent_at_ms is not None and processed_at_ms is not None:
                latency_ms = processed_at_ms - sent_at_ms
                if latency_ms >= 0:  # Only include non-negative latencies
                    window_latencies.append(latency_ms)

            total_messages += 1

        # Record the final window
        final_mean_latency_ms = (
            sum(window_latencies) / len(window_latencies) if window_latencies else 0
        )
        final_window_start_utc = datetime.fromtimestamp(
            current_window_start / 1000, tz=timezone.utc
        )
        final_entry = {
            "window_start_utc_ms": current_window_start,
            "window_end_utc_ms": current_window_start + WINDOW_SIZE_MS,
            "cumulative_taxi_count": len(cumulative_taxis),
            "total_messages": total_messages,
            "mean_latency_ms": round(final_mean_latency_ms, 2),
            "latency_samples": len(window_latencies),
            "timestamp_utc": final_window_start_utc.isoformat(),
        }
        results.append(final_entry)

        print("\n" + "=" * 80)
        print("FINAL ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Total messages processed: {total_messages}")
        print(f"Total unique taxi_ids found: {len(cumulative_taxis)}")
        print(f"Number of time windows: {len(results)}")
        print(f"Window size: {WINDOW_SIZE_MS/1000} seconds")
        print(
            f"Analysis scope: {datetime.fromtimestamp(first_timestamp_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} to {script_start_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        print(
            f"First window: {datetime.fromtimestamp(results[0]['window_start_utc_ms']/1000, tz=timezone.utc).isoformat()}"
        )
        print(
            f"Last window: {datetime.fromtimestamp(results[-1]['window_start_utc_ms']/1000, tz=timezone.utc).isoformat()}"
        )

        print("\nSample results (first 5 windows):")
        print(json.dumps(results[:5], indent=2))

        print("\nSample results (last 5 windows):")
        print(json.dumps(results[-5:], indent=2))

        # Save results to file
        output_file = "performance_benchmark_results.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "analysis_metadata": {
                        "topic": TOPIC,
                        "broker": BROKER,
                        "script_start_time_utc": script_start_utc.isoformat(),
                        "script_start_time_ms": script_start_time_ms,
                        "total_messages": total_messages,
                        "total_unique_taxis": len(cumulative_taxis),
                        "messages_excluded_after_start": messages_after_start,
                        "window_size_ms": WINDOW_SIZE_MS,
                        "window_size_seconds": WINDOW_SIZE_MS / 1000,
                        "total_windows": len(results),
                        "first_window_utc": (
                            results[0]["timestamp_utc"] if results else None
                        ),
                        "last_window_utc": (
                            results[-1]["timestamp_utc"] if results else None
                        ),
                        "analysis_completed_at": datetime.now(timezone.utc).isoformat(),
                    },
                    "time_series_data": results,
                },
                f,
                indent=2,
            )

        print(f"\nResults saved to: {output_file}")

        # Create and display visualizations
        print("\nCreating visualizations...")
        if PLOTLY_AVAILABLE:
            # Create enhanced latency vs taxi count chart with percentiles
            print("1. Creating event latency vs load analysis with percentiles...")
            chart_file1 = create_event_latency_vs_load_visualization(
                results, all_messages
            )

            # Create throughput vs latency chart
            print("2. Creating throughput vs event latency performance analysis...")
            chart_file2 = create_throughput_vs_event_latency_visualization(
                results, all_messages
            )

            # Create event latency chart
            print("3. Creating event latency per message chart...")
            chart_file3 = create_event_latency_per_message_visualization(all_messages)

            # Open all charts
            charts = [
                (chart_file1, "event latency vs load performance analysis chart"),
                (chart_file2, "throughput vs event latency performance analysis chart"),
                (chart_file3, "event latency per message performance analysis chart"),
            ]

            created_charts = [chart for chart, _ in charts if chart]
            if not created_charts:
                print("Failed to create visualizations")
            else:
                print(
                    f"\nSuccessfully created {len(created_charts)} visualization charts!"
                )
        else:
            print("Plotly not available. Install with: pip install plotly kaleido")
            print("Analysis complete. Check the JSON file for results.")

    except Exception as e:
        print(f"Error during consumption: {e}")

    finally:
        print("Stopping Kafka consumer...")
        await consumer.stop()
        print("Kafka consumer stopped.")


def main():
    """
    Main function to run the taxi data analysis
    """
    print("Kafka Pipeline Performance Benchmark and Visualization Script")

    # Check dependencies
    missing_deps = []
    if not AIOKAFKA_AVAILABLE:
        missing_deps.append("aiokafka")
    if not PLOTLY_AVAILABLE:
        missing_deps.append("plotly")
    if not NUMPY_AVAILABLE:
        missing_deps.append("numpy")

    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nTo install all required packages:")
        print("pip install aiokafka plotly numpy kaleido")
        print("\nOr install them individually:")
        for dep in missing_deps:
            print(f"pip install {dep}")

        if not AIOKAFKA_AVAILABLE:
            print("\nCannot proceed without aiokafka. Please install it first.")
            return
    else:
        print("All dependencies are available!")

    try:
        # Run the main analysis
        print("\nStarting Kafka message analysis...")
        asyncio.run(consume())

    except Exception as e:
        error_msg = f"Error during analysis: {e}"
        print(f"\n{error_msg}")


if __name__ == "__main__":
    main()
