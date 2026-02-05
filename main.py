#!/usr/bin/env python3
"""Kit.com Email Performance Analyzer — CLI entry point.

Fetches your Kit.com broadcast data, analyzes performance metrics, and
prints a detailed report with actionable optimization recommendations.

Usage:
    python main.py                   # Full analysis of all broadcasts
    python main.py --top 10          # Show top/bottom 10 instead of 5
    python main.py --export report   # Also save report to report.txt
"""

import argparse
import sys

from rich.console import Console

from kit_client import KitClient, KitAPIError
from analyzer import (
    compute_summary,
    rank_broadcasts,
    analyze_subject_lines,
    analyze_send_times,
    analyze_trends,
    analyze_links,
    compare_to_benchmarks,
    generate_recommendations,
)
from report import print_full_report, console


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze your Kit.com email broadcast performance."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top/bottom broadcasts to show (default: 5)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        metavar="FILE",
        help="Export the report to a plain-text file (e.g. --export report.txt)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Kit API key (overrides .env / KIT_API_KEY env var)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # --- Connect to Kit API ---
    try:
        client = KitClient(api_key=args.api_key)
    except ValueError as exc:
        console.print(f"[bold red]Configuration error:[/] {exc}")
        sys.exit(1)

    console.print("[dim]Fetching broadcasts from Kit.com...[/]")

    try:
        broadcasts = client.get_all_broadcast_data()
    except KitAPIError as exc:
        console.print(f"[bold red]API error:[/] {exc}")
        sys.exit(1)

    if not broadcasts:
        console.print("[yellow]No broadcasts found in your Kit.com account.[/]")
        sys.exit(0)

    console.print(f"[dim]Fetched {len(broadcasts)} broadcast(s). Analyzing...[/]")

    # --- Run analysis ---
    summary = compute_summary(broadcasts)

    if summary.get("error"):
        console.print(f"[yellow]{summary['error']}[/]")
        sys.exit(0)

    top_open, bottom_open = rank_broadcasts(broadcasts, metric="open_rate", top_n=args.top)
    top_click, bottom_click = rank_broadcasts(broadcasts, metric="click_rate", top_n=args.top)
    subject_analysis = analyze_subject_lines(broadcasts)
    send_time_analysis = analyze_send_times(broadcasts)
    trends = analyze_trends(broadcasts)
    links = analyze_links(broadcasts)
    benchmarks = compare_to_benchmarks(summary)
    recommendations = generate_recommendations(
        summary, subject_analysis, send_time_analysis, benchmarks, trends
    )

    # --- Print report ---
    report_args = (
        summary, benchmarks, top_open, bottom_open, top_click,
        bottom_click, subject_analysis, send_time_analysis,
        trends, links, recommendations,
    )

    # Print to terminal
    print_full_report(*report_args)

    # Optionally export to file
    if args.export:
        import report as _rmod

        original_console = _rmod.console
        with open(args.export, "w") as f:
            _rmod.console = Console(file=f, force_terminal=False, width=120)
            print_full_report(*report_args)
            _rmod.console = original_console
        console.print(f"[green]Report exported to {args.export}[/]")


if __name__ == "__main__":
    main()
