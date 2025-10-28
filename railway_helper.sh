#!/bin/bash

# Railway Helper Script for Anomalies Project
# Quick commands for common Railway operations

PROJECT_DIR="/Users/stephenbae/Projects/anomalies"

function show_help() {
    echo "🚂 Railway Helper for Anomalies Project"
    echo "========================================"
    echo ""
    echo "Usage: ./railway_helper.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status       - Show project status"
    echo "  logs         - View application logs"
    echo "  open         - Open Railway dashboard"
    echo "  deploy       - Deploy current code"
    echo "  vars         - Show environment variables"
    echo "  setvar       - Set environment variable (interactive)"
    echo "  initdb       - Initialize database"
    echo "  backfill     - Backfill 30 days of data"
    echo "  eod          - Run end-of-day job manually"
    echo "  connect      - Connect to PostgreSQL"
    echo "  health       - Check app health"
    echo "  domain       - Show/generate domain"
    echo "  help         - Show this help message"
    echo ""
}

function check_railway() {
    if ! command -v railway &> /dev/null; then
        echo "❌ Railway CLI not found. Install with: npm i -g @railway/cli"
        exit 1
    fi
}

function check_auth() {
    if ! railway whoami &> /dev/null; then
        echo "❌ Not logged into Railway. Run: railway login"
        exit 1
    fi
}

cd "$PROJECT_DIR" || exit 1
check_railway
check_auth

case "${1:-help}" in
    status)
        echo "📊 Project Status:"
        railway status
        ;;
    
    logs)
        echo "📋 Application Logs:"
        railway logs
        ;;
    
    open)
        echo "🌐 Opening Railway dashboard..."
        railway open
        ;;
    
    deploy)
        echo "🚀 Deploying to Railway..."
        railway up
        ;;
    
    vars)
        echo "🔧 Environment Variables:"
        railway variables
        ;;
    
    setvar)
        echo "🔧 Set Environment Variable"
        echo "Example: POLYGON_API_KEY=your_key"
        read -p "Variable (KEY=value): " var
        if [ -n "$var" ]; then
            railway variables set "$var"
        else
            echo "❌ No variable provided"
        fi
        ;;
    
    initdb)
        echo "🗄️  Initializing database..."
        railway run python init_db.py
        ;;
    
    backfill)
        echo "📊 Backfilling 30 days of data..."
        echo "This may take a while with unlimited API plan..."
        railway run python -c "from data_fetcher import DataFetcher; from anomaly_detector import AnomalyDetector; df = DataFetcher(); df.backfill_data(30); ad = AnomalyDetector(); ad.build_lookup_table()"
        ;;
    
    eod)
        echo "⏰ Running end-of-day job..."
        railway run python -c "from scheduler import EODScheduler; EODScheduler().run_now()"
        ;;
    
    connect)
        echo "🔌 Connecting to PostgreSQL..."
        railway connect postgres
        ;;
    
    health)
        echo "🏥 Checking app health..."
        # Get the domain first
        DOMAIN=$(railway domain 2>/dev/null | grep -o 'https://[^ ]*' | head -1)
        if [ -n "$DOMAIN" ]; then
            curl -s "$DOMAIN/health" | python3 -m json.tool
        else
            echo "❌ Could not determine app domain"
            echo "Run: railway domain"
        fi
        ;;
    
    domain)
        echo "🌐 Domain Information:"
        railway domain
        ;;
    
    help|*)
        show_help
        ;;
esac

