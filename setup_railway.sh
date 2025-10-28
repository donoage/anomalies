#!/bin/bash

# Railway Setup Script for Anomalies Project
# This script will guide you through setting up the Railway services

echo "🚂 Railway Setup for Anomalies Project"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "Install it with: npm i -g @railway/cli"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway."
    echo "Please run: railway login"
    exit 1
fi

echo "✅ Railway CLI is installed and you're logged in"
echo ""

# Project should already be initialized
echo "📦 Project Status:"
railway status

echo ""
echo "Next steps to complete manually:"
echo ""
echo "1. Add PostgreSQL Database:"
echo "   railway add"
echo "   Select: Database → PostgreSQL"
echo ""
echo "2. Set Environment Variables:"
echo "   railway variables set POLYGON_API_KEY=your_api_key_here"
echo "   railway variables set FLASK_SECRET_KEY=\$(openssl rand -hex 32)"
echo "   railway variables set EOD_SCHEDULE_TIME=16:30"
echo "   railway variables set TIMEZONE=America/New_York"
echo "   railway variables set LOOKBACK_DAYS=5"
echo "   railway variables set Z_SCORE_THRESHOLD=3.0"
echo ""
echo "3. Deploy the application:"
echo "   railway up"
echo ""
echo "4. Generate domain:"
echo "   railway domain"
echo ""
echo "5. Initialize database (after deployment):"
echo "   railway run python init_db.py"
echo ""
echo "6. Backfill data (optional):"
echo "   railway run python -c \"from data_fetcher import DataFetcher; DataFetcher().backfill_data(30)\""
echo ""
echo "Or visit the Railway dashboard:"
railway open

