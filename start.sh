#!/bin/bash

# Start Backend
echo "Starting Backend..."
cd chat-app/backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Trap SIGINT to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT

wait
