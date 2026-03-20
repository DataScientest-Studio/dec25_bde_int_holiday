#!/bin/bash
set -e

# Cron runs with a minimal PATH; ensure python is discoverable
export PATH="/usr/local/bin:/usr/bin:/bin"

if [ -f /app/.env.cron ]; then
    set -a
    source /app/.env.cron
    set +a
fi

cd /app
echo "============================================================"
echo "Running Batch ETL Pipeline..."
echo "============================================================"
/usr/local/bin/python3 -m src.pipelines.batch_etl --limit-per-run 1000 --max-pages 5 --since-hours 24
echo ""
echo "============================================================"
echo "Running Graph Loader..."
echo "============================================================"
/usr/local/bin/python3 -m src.pipelines.run_graph_load --batch-size 100