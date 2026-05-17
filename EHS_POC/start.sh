#!/bin/bash
# start.sh - Start both backend and frontend

echo "🦺 Starting EHS AI POC..."

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found."
    echo " Please create and edit .env and add your GROQ_API_KEY"
    echo "   Get a free key at: https://console.groq.com"
fi

# Start backend
echo "🚀 Starting FastAPI backend on port 8000..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🖥️  Starting Streamlit frontend on port 8501..."
cd frontend
streamlit run app.py &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ EHS AI POC is running!"
echo "   Frontend: http://localhost:8501"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Handle cleanup
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

wait
