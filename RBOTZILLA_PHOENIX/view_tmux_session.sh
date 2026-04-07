#!/bin/bash
# View RICK Trading System tmux sessions
# Shows active trading sessions running in background

echo "================================================================"
echo "📊 RICK Trading System - Active Sessions"
echo "================================================================"
echo ""

if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed"
    echo "   Install with: sudo apt-get install tmux"
    exit 1
fi

# List all tmux sessions
echo "Active tmux sessions:"
echo ""
tmux list-sessions 2>/dev/null || echo "  No active tmux sessions found"

echo ""
echo "================================================================"
echo "Available Commands:"
echo "================================================================"
echo ""
echo "  View specific session:"
echo "    tmux attach-session -t rick_trading"
echo "    tmux attach-session -t rick_paper"
echo "    tmux attach-session -t rick_dashboard"
echo ""
echo "  List all sessions:"
echo "    tmux list-sessions"
echo ""
echo "  Kill a session:"
echo "    tmux kill-session -t <session_name>"
echo ""
echo "  Detach from session (while inside):"
echo "    Press: Ctrl+b, then d"
echo ""
echo "================================================================"
