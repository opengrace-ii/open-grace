#!/bin/bash

# Start Backend API
echo "Starting Open Grace API on http://0.0.0.0:8000..."
uvicorn open_grace.api.server:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start Frontend UI
echo "Starting Open Grace Dashboard on http://0.0.0.0:5173..."
cd frontend && npm run dev -- --host 0.0.0.0 &
UI_PID=$!

echo "=========================================================="
echo "Open Grace is running!"
echo "Access the Dashboard from your mobile phone at:"
echo "http://192.168.0.165:5173"
echo "Press Ctrl+C to stop all services."
echo "=========================================================="

# Trap ctrl+c to kill both processes
trap "echo -e '\nStopping Open Grace...'; kill $API_PID $UI_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for processes
wait $API_PID $UI_PID
