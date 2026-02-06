"""
Zero-Loss Circuit Breaker: Main Demo Runner
============================================

This is the entry point for demonstrating the multi-agent tribunal system.
Run with: python main.py

Demonstrates three key scenarios:
1. Happy Path (Refund) - Agents agree, clear data
2. Adversarial (Deny) - User lies, agents detect fraud
3. Circuit Breaker (Escalate) - Ambiguous data, strategic refusal
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown

from dotenv import load_dotenv
load_dotenv()

from models.schemas import Decision, Verdict, TransactionSignal
from mock_data.scenarios import (
    get_happy_path_scenario,
    get_adversarial_scenario,
    get_circuit_breaker_scenario,
    ALL_SCENARIOS
)
from core.graph import run_tribunal

console = Console()


def display_header():
    """Display the demo header."""
    header = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗███████╗██████╗  ██████╗       ██╗      ██████╗ ███████╗███████╗   ║
║   ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗      ██║     ██╔═══██╗██╔════╝██╔════╝   ║
║     ███╔╝ █████╗  ██████╔╝██║   ██║█████╗██║     ██║   ██║███████╗███████╗   ║
║    ███╔╝  ██╔══╝  ██╔══██╗██║   ██║╚════╝██║     ██║   ██║╚════██║╚════██║   ║
║   ███████╗███████╗██║  ██║╚██████╔╝      ███████╗╚██████╔╝███████║███████║   ║
║   ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝       ╚══════╝ ╚═════╝ ╚══════╝╚══════╝   ║
║                                                                               ║
║                    CIRCUIT BREAKER - Payment Dispute Tribunal                 ║
║                                                                               ║
║       "The most intelligent action in ambiguity is often no action at all"    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(header, style="bold cyan")


def display_transaction_signal(signal: TransactionSignal):
    """Display the incoming transaction signal."""
    table = Table(title="📥 INCOMING DISPUTE", box=box.ROUNDED, border_style="yellow")
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white", width=60)
    
    table.add_row("Transaction ID", signal.transaction_id)
    table.add_row("User Claim", signal.user_claim[:80] + "..." if len(signal.user_claim) > 80 else signal.user_claim)
    table.add_row("Amount", f"${signal.amount:.2f}")
    table.add_row("Bank Status", signal.bank_status.value)
    table.add_row("Ledger Status", signal.ledger_status.value)
    
    console.print(table)
    console.print()


def display_debate_log(state: dict):
    """Display the tribunal debate log."""
    console.print(Panel("[bold magenta]🏛️ TRIBUNAL IN SESSION[/bold magenta]", expand=False))
    
    # Round 1
    console.print("\n[bold yellow]━━━ ROUND 1: Opening Statements ━━━[/bold yellow]")
    for arg in state.get("round_1_arguments", []):
        style = "green" if arg.position == Decision.REFUND else "red" if arg.position == Decision.DENY else "yellow"
        console.print(f"  [{style}]{arg.agent_name}[/{style}]: {arg.position.value} ({arg.confidence:.0f}% confidence)")
        console.print(f"     [dim]{arg.reasoning[:100]}...[/dim]")
    
    # Round 2
    console.print("\n[bold yellow]━━━ ROUND 2: Challenge & Rebuttal ━━━[/bold yellow]")
    for arg in state.get("round_2_rebuttals", []):
        style = "green" if arg.position == Decision.REFUND else "red" if arg.position == Decision.DENY else "yellow"
        console.print(f"  [{style}]{arg.agent_name}[/{style}]: {arg.position.value} ({arg.confidence:.0f}% confidence)")
        console.print(f"     [dim]{arg.reasoning[:100]}...[/dim]")
    
    # Round 3
    console.print("\n[bold yellow]━━━ ROUND 3: Final Votes ━━━[/bold yellow]")
    for vote in state.get("round_3_votes", []):
        style = "green" if vote.vote == Decision.REFUND else "red" if vote.vote == Decision.DENY else "yellow"
        veto_str = " [bold red]⛔ VETO[/bold red]" if vote.veto_triggered else ""
        console.print(f"  [{style}]{vote.agent_name}[/{style}]: {vote.vote.value} ({vote.confidence:.0f}%){veto_str}")
    
    console.print()


def display_verdict(verdict: Verdict):
    """Display the final verdict with appropriate styling."""
    if verdict.circuit_breaker_triggered:
        # CIRCUIT BREAKER - Yellow/Orange warning
        border_style = "bold yellow on red"
        title = "⚠️  CIRCUIT BREAKER TRIGGERED  ⚠️"
        decision_style = "bold yellow"
        icon = "🔒"
    elif verdict.decision == Decision.REFUND:
        # REFUND - Green success
        border_style = "bold green"
        title = "✅ VERDICT: REFUND APPROVED"
        decision_style = "bold green"
        icon = "💰"
    elif verdict.decision == Decision.DENY:
        # DENY - Red denial
        border_style = "bold red"
        title = "❌ VERDICT: REFUND DENIED"
        decision_style = "bold red"
        icon = "🚫"
    else:
        # ESCALATE - Yellow
        border_style = "bold yellow"
        title = "⏸️ VERDICT: ESCALATED TO HUMAN"
        decision_style = "bold yellow"
        icon = "👤"
    
    # Build verdict content
    content = f"""
{icon} **Decision**: [{decision_style}]{verdict.decision.value}[/{decision_style}]
📊 **Confidence**: {verdict.confidence:.1f}%
📝 **Reasoning**: {verdict.reasoning}
"""
    
    if verdict.circuit_breaker_triggered:
        content += f"""
🚨 **Escalation Reason**: {verdict.escalation_reason}

[bold yellow blink]⚡ STRATEGIC REFUSAL ENGAGED ⚡[/bold yellow blink]
[dim]Human intervention required. Workflow locked.[/dim]
"""
    
    console.print(Panel(content, title=title, border_style=border_style, box=box.DOUBLE))


def run_scenario(name: str, scenario_fn):
    """Run a single scenario and display results."""
    console.print(f"\n{'='*80}")
    console.print(f"[bold cyan]SCENARIO: {name.upper().replace('_', ' ')}[/bold cyan]")
    console.print(f"{'='*80}\n")
    
    # Get the transaction signal
    signal = scenario_fn()
    display_transaction_signal(signal)
    
    # Run the tribunal
    console.print("[dim]Running tribunal deliberation...[/dim]")
    console.print()
    
    try:
        final_state = run_tribunal(signal)
        
        # Display debate log
        display_debate_log(final_state)
        
        # Display verdict
        verdict = final_state.get("verdict")
        if verdict:
            display_verdict(verdict)
        else:
            console.print("[red]ERROR: No verdict rendered[/red]")
            
    except Exception as e:
        console.print(f"[red]ERROR running scenario: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print()


def run_all_demos():
    """Run all three main demo scenarios."""
    display_header()
    
    console.print("\n[bold]This demo will show three scenarios:[/bold]")
    console.print("  1. [green]Happy Path[/green] - Clear failure, agents agree, REFUND issued")
    console.print("  2. [red]Adversarial[/red] - User lies, agents detect fraud, DENY issued")
    console.print("  3. [yellow]Circuit Breaker[/yellow] - 504 Timeout, agents disagree, ESCALATE triggered")
    console.print()
    
    input("Press Enter to start the demo...")
    
    # Scenario 1: Happy Path
    run_scenario("Happy Path (Consensus: Refund)", get_happy_path_scenario)
    input("\nPress Enter for next scenario...")
    
    # Scenario 2: Adversarial
    run_scenario("Adversarial (Fraud Detection: Deny)", get_adversarial_scenario)
    input("\nPress Enter for next scenario...")
    
    # Scenario 3: Circuit Breaker (The Winning Moment)
    run_scenario("Circuit Breaker (Strategic Refusal: Escalate)", get_circuit_breaker_scenario)
    
    console.print("\n" + "="*80)
    console.print("[bold green]DEMO COMPLETE[/bold green]")
    console.print("="*80)
    console.print("\n[dim]Key Takeaway: The system successfully demonstrated 'Strategic Refusal'[/dim]")
    console.print("[dim]When data is ambiguous, REFUSING to act is a feature, not a failure.[/dim]\n")


def run_interactive():
    """Run an interactive mode where user can pick scenarios."""
    display_header()
    
    while True:
        console.print("\n[bold]Choose a scenario:[/bold]")
        console.print("  1. Happy Path (Clear Refund)")
        console.print("  2. Adversarial (Fraud Detection)")
        console.print("  3. Circuit Breaker (504 Timeout)")
        console.print("  4. Pending Transaction")
        console.print("  5. Conflicting Data")
        console.print("  6. Run All Demos")
        console.print("  0. Exit")
        
        choice = input("\nEnter choice (0-6): ").strip()
        
        if choice == "0":
            console.print("[yellow]Exiting...[/yellow]")
            break
        elif choice == "1":
            run_scenario("Happy Path", get_happy_path_scenario)
        elif choice == "2":
            run_scenario("Adversarial", get_adversarial_scenario)
        elif choice == "3":
            run_scenario("Circuit Breaker", get_circuit_breaker_scenario)
        elif choice == "4":
            from mock_data.scenarios import get_pending_scenario
            run_scenario("Pending Transaction", get_pending_scenario)
        elif choice == "5":
            from mock_data.scenarios import get_conflicting_scenario
            run_scenario("Conflicting Data", get_conflicting_scenario)
        elif choice == "6":
            run_all_demos()
        else:
            console.print("[red]Invalid choice. Try again.[/red]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zero-Loss Circuit Breaker Demo")
    parser.add_argument("--demo", action="store_true", help="Run the full demo sequence")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive mode")
    parser.add_argument("--scenario", "-s", choices=["happy", "adversarial", "circuit", "pending", "conflict"], 
                        help="Run a specific scenario")
    
    args = parser.parse_args()
    
    if args.demo:
        run_all_demos()
    elif args.interactive:
        run_interactive()
    elif args.scenario:
        scenario_map = {
            "happy": ("Happy Path", get_happy_path_scenario),
            "adversarial": ("Adversarial", get_adversarial_scenario),
            "circuit": ("Circuit Breaker", get_circuit_breaker_scenario),
            "pending": ("Pending", ALL_SCENARIOS["pending"]),
            "conflict": ("Conflicting", ALL_SCENARIOS["conflicting"])
        }
        name, fn = scenario_map[args.scenario]
        display_header()
        run_scenario(name, fn)
    else:
        # Default: interactive mode
        run_interactive()
