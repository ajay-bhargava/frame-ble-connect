#!/bin/bash

# Test script for haptic-triggered photo capture using curl
# This script demonstrates the complete haptic workflow

BASE_URL="http://localhost:8000/api/v1/haptic"

echo "🚀 FRAME GLASSES HAPTIC CAPTURE TEST"
echo "===================================="

# Function to print step headers
print_step() {
    echo ""
    echo "🎯 STEP $1: $2"
    echo "📝 $3"
    echo "------------------------------------"
}

# Function to print results
print_result() {
    echo "✅ $1 Result:"
    if [[ $2 == *"success"*"true"* ]]; then
        echo "   Status: ✅ Success"
    else
        echo "   Status: ❌ Failed"
    fi
    echo "   Response: $2"
}

# Step 1: Check initial status
print_step "1" "Initial Status Check" "Check if haptic service is available"
RESPONSE=$(curl -s "$BASE_URL/status")
print_result "Status Check" "$RESPONSE"

# Step 2: Connect in haptic mode
print_step "2" "Haptic Connection" "Connect to Frame glasses in haptic mode"
RESPONSE=$(curl -s -X POST "$BASE_URL/connect")
print_result "Haptic Connection" "$RESPONSE"

# Check if connection was successful
if [[ $RESPONSE == *"success"*"true"* ]]; then
    echo "   ✅ Successfully connected in haptic mode"
    
    # Step 3: Start monitoring
    print_step "3" "Start Monitoring" "Start monitoring for touch events"
    RESPONSE=$(curl -s -X POST "$BASE_URL/start-monitoring")
    print_result "Start Monitoring" "$RESPONSE"
    
    if [[ $RESPONSE == *"success"*"true"* ]]; then
        echo "   ✅ Haptic monitoring started"
        
        # Step 4: Check monitoring status
        print_step "4" "Monitoring Status" "Check if monitoring is active"
        RESPONSE=$(curl -s "$BASE_URL/status")
        print_result "Monitoring Status" "$RESPONSE"
        
        # Step 5: Test manual capture
        print_step "5" "Manual Capture Test" "Test manual capture in haptic mode"
        RESPONSE=$(curl -s -X POST "$BASE_URL/capture-manual" \
            -H "Content-Type: application/json" \
            -d '{"resolution": 720}')
        print_result "Manual Capture" "$RESPONSE"
        
        # Step 6: Display test message
        print_step "6" "Display Test" "Display test message on glasses"
        RESPONSE=$(curl -s -X POST "$BASE_URL/display" \
            -H "Content-Type: application/json" \
            -d '"Touch to capture!"')
        print_result "Display Test" "$RESPONSE"
        
        # Step 7: Stop monitoring
        print_step "7" "Stop Monitoring" "Stop haptic monitoring"
        RESPONSE=$(curl -s -X POST "$BASE_URL/stop-monitoring")
        print_result "Stop Monitoring" "$RESPONSE"
        
        # Step 8: Disconnect
        print_step "8" "Disconnect" "Disconnect from Frame glasses"
        RESPONSE=$(curl -s -X POST "$BASE_URL/disconnect")
        print_result "Disconnect" "$RESPONSE"
        
    else
        echo "   ❌ Failed to start monitoring"
    fi
else
    echo "   ❌ Failed to connect in haptic mode"
    echo "   Note: This is expected if Frame glasses are not connected"
fi

echo ""
echo "🎉 HAPTIC CAPTURE TEST COMPLETE!"
echo "================================="
echo ""
echo "📚 Available Haptic Endpoints:"
echo "   POST /api/v1/haptic/connect          - Connect in haptic mode"
echo "   POST /api/v1/haptic/disconnect       - Disconnect and stop monitoring"
echo "   POST /api/v1/haptic/start-monitoring - Start touch monitoring"
echo "   POST /api/v1/haptic/stop-monitoring  - Stop touch monitoring"
echo "   GET  /api/v1/haptic/status           - Get haptic status"
echo "   POST /api/v1/haptic/capture-manual   - Manual capture in haptic mode"
echo "   POST /api/v1/haptic/display          - Display text on glasses"
echo ""
echo "🔧 Interactive Testing: http://localhost:8000/docs"
echo "📖 API Documentation: http://localhost:8000/redoc" 