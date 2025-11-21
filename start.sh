#!/bin/bash

echo "🎯 Starting Single Parlay Quoter"
echo "================================"
echo "Target: Josh Allen TD + Buffalo Winner"
echo "Port: 5002"
echo "================================"
echo ""

cd "$(dirname "$0")"

python3 app.py

