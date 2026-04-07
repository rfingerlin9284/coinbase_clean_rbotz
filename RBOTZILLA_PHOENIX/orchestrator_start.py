#!/usr/bin/env python3
"""
PROFESSIONAL HEDGE FUND TRADING ORCHESTRATOR
Quick-start demonstration and operational launcher

This system provides:
1. UNIFIED POSITION TRACKING: All positions (autonomous + manual LLM)
2. AGGRESSIVE MONITORING: 5-second checks with immediate red-alert exits
3. SMART MARGIN: 5-10% per symbol (not 1.5%)
4. MANUAL TRADING: Open/close positions via LLM commands
5. CLONED REPO SYNC: All positions synced across master+slaves

Usage:
    ./orchestrator_start.py                    # Start in interactive mode
    ./orchestrator_start.py --auto             # Start and run autonomously
    ./orchestrator_start.py --manual          # Manual trading mode only
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add util to path
sys.path.insert(0, str(Path(__file__).parent))

from util.portfolio_orchestrator import get_orchestrator

def print_welcome():
    """Display welcome banner"""
    print("\n" + "█"*100)
    print("█" + " "*98 + "█")
    print("█" + "🏢 RBOTZILLA PHOENIX - PROFESSIONAL HEDGE FUND TRADING ORCHESTRATOR".center(98) + "█")
    print("█" + " "*98 + "█")
    print("█" + "Aggressive Margin Management | Real-Time Position Tracking | LLM Trading Integration".center(98) + "█")
    print("█" + " "*98 + "█")
    print("█"*100 + "\n")

def print_menu():
    """Display interactive menu"""
    print("\n" + "="*100)
    print("COMMAND MENU")
    print("="*100)
    print("\n📊 PORTFOLIO COMMANDS:")
    print("  status               - Print full portfolio status report")
    print("  summary              - Quick portfolio summary")
    print("  positions            - List all open positions")
    print("  manual               - List manual positions (LLM only)")
    
    print("\n🤖 TRADING COMMANDS:")
    print("  buy SYMBOL PRICE SL TP SIZE")
    print("    Example: buy EUR_USD 1.0950 1.0940 1.0975 1.0")
    print("  sell SYMBOL PRICE SL TP SIZE")
    print("    Example: sell GBP_USD 1.2500 1.2530 1.2450 0.5")
    print("  close POSITION_ID    - Close a specific position")
    print("  auto POSITION_ID     - Enable auto-management for manual position")
    
    print("\n🔐 CAPITAL PRESERVATION:")
    print("  oco_status           - Check OCO (SL/TP) order status")
    print("  oco_verify           - Verify all OCO orders working")
    print("  oco_recreate         - Recreate broken OCO orders")
    print("  red_positions        - Show all positions in red")
    print("  prune_analysis       - Analyze positions for pruning")
    print("  prune_execute        - Execute capital pruning (close losers)")
    print("  efficiency           - Check capital efficiency score")
    
    print("\n⚙️  CONFIGURATION:")
    print("  config               - Display current operating configuration")
    print("  info                 - Show system information")
    
    print("\n🔄 SYNC & CLONES:")
    print("  sync                 - Manual trigger sync across clones")
    print("  sync_status          - Check cross-repo sync status")
    
    print("\n⏹️  CONTROL:")
    print("  stop                 - Stop trading operations")
    print("  exit                 - Exit this program")
    print("\n" + "="*100)

    parser = argparse.ArgumentParser(description="Orchestrate professional trading")
    parser.add_argument('--auto', action='store_true', help='Run autonomously (no interactive menu)')
    parser.add_argument('--manual', action='store_true', help='Manual trading mode only')
    parser.add_argument('--swarm', action='store_true', help='Boot the Hive Mind Cluster (3 trading engine instances)')
    parser.add_argument('--account', type=float, default=25000.0, help='Account balance')
    parser.add_argument('--repo', default='/home/rfing/RBOTZILLA_PHOENIX', help='Master repo path')
    
    args = parser.parse_args()
    
    print_welcome()
    
    # Initialize orchestrator
    orchestrator = get_orchestrator(
        master_repo_path=args.repo,
        account_balance=args.account,
    )
    
    # Handle Swarm Boot
    swarm_processes = []
    if args.swarm:
        print("🐝 INITIATING HIVE MIND SWARM (Spawn 3 Wolf Pack Engines) 🐝")
        engine_path = Path(__file__).parent / "oanda_trading_engine.py"
        python_exe = sys.executable
        
        for i in range(1, 4):
            print(f"   🚀 Launching Wolf {i}...")
            p = subprocess.Popen([python_exe, str(engine_path), "--node-id", str(i)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            swarm_processes.append(p)
            time.sleep(1) # stagger startup
        print("✅ Swarm active in the background. They will aggregate via unified telemetry.\n")

    # Start trading operations
    orchestrator.start_trading(use_repo_sync=True)
    
    if args.auto:
        # Run autonomously - just monitor
        print("🚀 Running in AUTONOMOUS mode")
        print("ℹ️  Press Ctrl+C to stop\n")
        
        try:
            while True:
                time.sleep(30)
                # Print status every 30 seconds
                summary = orchestrator.registry.get_portfolio_summary()
                pos_count = summary['total_open_positions']
                pnl = summary['total_pnl_usd']
                print(f"[{time.strftime('%H:%M:%S')}] Positions: {pos_count} | P&L: ${pnl:+.2f}")
        except KeyboardInterrupt:
            print("\n⏹️  Stopping...")
            orchestrator.stop_trading()
    
    elif args.manual:
        # Manual trading mode only
        print("👤 Running in MANUAL mode")
        print("ℹ️  You control all positions via commands\n")
        
        interactive_loop(orchestrator)
    
    else:
        # Interactive mode
        print("💬 Running in INTERACTIVE mode")
        print("ℹ️  Type 'help' for commands\n")
        
        interactive_loop(orchestrator)

def interactive_loop(orchestrator):
    """Interactive command loop"""
    try:
        while True:
            try:
                print_menu()
                cmd = input("\n🔹 Enter command: ").strip().lower()
                
                if not cmd:
                    continue
                
                if cmd == 'help':
                    print_menu()
                
                elif cmd == 'status':
                    orchestrator.print_full_status_report()
                
                elif cmd == 'summary':
                    summary = orchestrator.registry.get_portfolio_summary()
                    print(f"\n📊 Portfolio Summary:")
                    print(f"   Open Positions: {summary['total_open_positions']}")
                    print(f"   Total P&L: ${summary['total_pnl_usd']:+.2f}")
                    print(f"   Total Notional: ${summary['total_notional']:,.2f}")
                    print(f"   In Green: {summary['positions_in_green']} | In Red: {summary['positions_in_red']}")
                
                elif cmd == 'positions':
                    positions = orchestrator.registry.get_all_open_positions()
                    if not positions:
                        print("No open positions")
                    else:
                        for pos in positions:
                            pnl = pos.metrics.pnl_usd
                            color = "🟢" if pnl > 0 else "🔴"
                            source = "🤖" if pos.source.value == 'autonomous' else "👤"
                            print(f"{color}{source} {pos.symbol} | ${pnl:+.2f} ({pos.metrics.pnl_percent:+.2f}%)")
                
                elif cmd == 'manual':
                    orchestrator.llm_interface.print_manual_positions_summary()
                
                elif cmd.startswith('buy '):
                    parts = cmd.split()
                    if len(parts) >= 6:
                        symbol = parts[1]
                        entry = float(parts[2])
                        sl = float(parts[3])
                        tp = float(parts[4])
                        size = float(parts[5])
                        
                        pos_id = orchestrator.open_manual_position(
                            symbol=symbol,
                            direction='BUY',
                            entry_price=entry,
                            size_units=size,
                            stop_loss=sl,
                            take_profit=tp,
                        )
                    else:
                        print("❌ Format: buy SYMBOL PRICE SL TP SIZE")
                
                elif cmd.startswith('sell '):
                    parts = cmd.split()
                    if len(parts) >= 6:
                        symbol = parts[1]
                        entry = float(parts[2])
                        sl = float(parts[3])
                        tp = float(parts[4])
                        size = float(parts[5])
                        
                        pos_id = orchestrator.open_manual_position(
                            symbol=symbol,
                            direction='SELL',
                            entry_price=entry,
                            size_units=size,
                            stop_loss=sl,
                            take_profit=tp,
                        )
                    else:
                        print("❌ Format: sell SYMBOL PRICE SL TP SIZE")
                
                elif cmd.startswith('close '):
                    pos_id = cmd.split()[1]
                    orchestrator.close_manual_position(pos_id)
                
                elif cmd.startswith('auto '):
                    pos_id = cmd.split()[1]
                    orchestrator.enable_auto_management(pos_id)
                
                elif cmd == 'config':
                    orchestrator.print_operating_configuration()
                
                elif cmd == 'info':
                    print("\n📋 SYSTEM INFORMATION:")
                    print(f"   Master Repo: {orchestrator.master_repo_path}")
                    print(f"   Account Balance: ${orchestrator.account_balance:,.2f}")
                    print(f"   Monitor Interval: {orchestrator.monitor.check_interval}s")
                    print(f"   Position Tracking: Universal Registry")
                    print(f"   Red Alert Threshold: {(orchestrator.monitor.RED_ALERT_LOSS_PERCENT*100):.1f}%")
                
                elif cmd == 'oco_status':
                    orchestrator.oco_manager.print_oco_status()
                
                elif cmd == 'oco_verify':
                    print("🔐 Verifying all OCO orders...")
                    results = orchestrator.verify_all_oco_orders(recreate_broken=True)
                    print(f"✅ Verification complete:")
                    print(f"   Active: {results['active']}")
                    print(f"   Broken: {results['broken']}")
                    print(f"   Recreated: {results['recreated']}")
                
                elif cmd == 'oco_recreate':
                    print("🔄 Recreating all broken OCO orders...")
                    results = orchestrator.verify_all_oco_orders(recreate_broken=True)
                    print(f"✅ {results['recreated']} OCO orders recreated")
                
                elif cmd == 'red_positions':
                    orchestrator.pruning_engine.monitor.print_red_positions()
                
                elif cmd == 'prune_analysis':
                    orchestrator.analyze_capital_pruning()
                
                elif cmd == 'prune_execute':
                    print("✂️  Executing capital pruning...")
                    summary = orchestrator.execute_capital_pruning()
                    print(f"✅ Pruning complete:")
                    print(f"   Actions taken: {summary['actions_taken']}")
                    print(f"   Candidates found: {summary['candidates_found']}")
                
                elif cmd == 'efficiency':
                    eff = orchestrator.get_capital_efficiency_report()
                    print(f"\n💪 CAPITAL EFFICIENCY:")
                    print(f"   Efficiency Score: {eff['efficiency_score']:.1f}/100")
                    print(f"   Notional Deployed: ${eff['notional_deployed']:,.2f}")
                    print(f"   P&L Per Notional: {eff['pnl_per_notional']:.2f}%")
                    print(f"   In Profit: {eff['positions_in_profit']} | In Loss: {eff['positions_in_loss']}")
                
                elif cmd == 'sync':
                    print("🔄 Triggering manual sync across clones...")
                    orchestrator.repo_coordinator.sync_all()
                    print("✅ Sync complete")
                
                elif cmd == 'sync_status':
                    orchestrator.repo_coordinator.print_sync_report()
                
                elif cmd == 'stop':
                    print("\n⏹️  Stopping trading operations...")
                    orchestrator.stop_trading()
                    break
                
                elif cmd == 'exit':
                    orchestrator.stop_trading()
                    print("\n👋 Goodbye!")
                    sys.exit(0)
                
                else:
                    print(f"❌ Unknown command: {cmd}")
            
            except ValueError as e:
                print(f"❌ Invalid input: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
        orchestrator.stop_trading()
    finally:
        if 'swarm_processes' in locals():
            print("🐝 Shutting down Wolf Pack...")
            for p in swarm_processes:
                p.terminate()

if __name__ == '__main__':
    main()
