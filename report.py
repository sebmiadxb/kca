"""Generate a rich terminal report for Kit.com email performance analysis."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box


console = Console()

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}
VERDICT_LABELS = {
    "excellent": ("[bold green]Excellent[/]", "+"),
    "good": ("[green]Good[/]", "="),
    "below_average": ("[yellow]Below Average[/]", "-"),
    "needs_attention": ("[bold red]Needs Attention[/]", "!"),
}


def _pct(value):
    """Format a rate as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value:.1%}"


# ------------------------------------------------------------------ #
# Report sections
# ------------------------------------------------------------------ #


def print_header():
    console.print()
    console.print(
        Panel(
            "[bold]Kit.com Email Performance Analysis[/bold]\n"
            "Powered by Kit API v4",
            style="blue",
            expand=False,
        )
    )
    console.print()


def print_summary(summary):
    """Print the aggregate summary metrics."""
    console.print("[bold underline]Overall Performance Summary[/]")
    console.print()

    table = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Broadcasts Sent", str(summary.get("total_broadcasts", 0)))
    table.add_row("Total Recipients", f"{summary.get('total_recipients', 0):,}")
    table.add_row("Total Opens", f"{summary.get('total_opened', 0):,}")
    table.add_row("Total Clicks", f"{summary.get('total_clicks', 0):,}")
    table.add_row("Total Unsubscribes", f"{summary.get('total_unsubscribes', 0):,}")
    table.add_row("", "")
    table.add_row("Avg Open Rate", _pct(summary.get("avg_open_rate")))
    table.add_row("Avg Click Rate", _pct(summary.get("avg_click_rate")))
    table.add_row("Avg Click-to-Open Rate", _pct(summary.get("avg_click_to_open_rate")))
    table.add_row("Avg Unsubscribe Rate", _pct(summary.get("avg_unsubscribe_rate")))
    table.add_row("", "")
    table.add_row("Best Open Rate", _pct(summary.get("max_open_rate")))
    table.add_row("Worst Open Rate", _pct(summary.get("min_open_rate")))
    table.add_row("Best Click Rate", _pct(summary.get("max_click_rate")))
    table.add_row("Worst Click Rate", _pct(summary.get("min_click_rate")))

    console.print(table)
    console.print()


def print_benchmarks(comparisons):
    """Print the benchmark comparison table."""
    console.print("[bold underline]Industry Benchmark Comparison[/]")
    console.print()

    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="bold")
    table.add_column("Your Value", justify="right")
    table.add_column("Benchmark", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Verdict")

    for label, data in comparisons.items():
        delta_str = f"{data['delta']:+.1%}"
        verdict_markup, _ = VERDICT_LABELS.get(data["verdict"], ("[white]—[/]", ""))
        table.add_row(
            label,
            _pct(data["value"]),
            _pct(data["benchmark"]),
            delta_str,
            verdict_markup,
        )

    console.print(table)
    console.print()


def print_top_bottom(top, bottom, metric_label="Open Rate"):
    """Print the top and bottom performing broadcasts."""
    console.print(f"[bold underline]Top Performing Broadcasts by {metric_label}[/]")
    console.print()

    table = Table(box=box.SIMPLE, show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Subject", max_width=60)
    table.add_column(metric_label, justify="right")

    for i, (bc, val) in enumerate(top, 1):
        subject = bc.get("subject", "(no subject)")
        table.add_row(str(i), subject, _pct(val))

    console.print(table)
    console.print()

    console.print(f"[bold underline]Lowest Performing Broadcasts by {metric_label}[/]")
    console.print()

    table = Table(box=box.SIMPLE, show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Subject", max_width=60)
    table.add_column(metric_label, justify="right")

    for i, (bc, val) in enumerate(bottom, 1):
        subject = bc.get("subject", "(no subject)")
        table.add_row(str(i), subject, _pct(val))

    console.print(table)
    console.print()


def print_subject_line_analysis(sa):
    """Print subject line pattern analysis."""
    console.print("[bold underline]Subject Line Analysis[/]")
    console.print()

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Pattern", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Avg Open Rate", justify="right")

    rows = [
        ("Short (<=40 chars)", sa.get("short_subject_count", 0), sa.get("short_subject_avg_open")),
        ("Medium (41-60 chars)", sa.get("medium_subject_count", 0), sa.get("medium_subject_avg_open")),
        ("Long (>60 chars)", sa.get("long_subject_count", 0), sa.get("long_subject_avg_open")),
        ("Contains question (?)", sa.get("question_count", 0), sa.get("question_avg_open")),
        ("Contains numbers", sa.get("number_count", 0), sa.get("number_avg_open")),
        ("Contains emoji/special", sa.get("emoji_count", 0), sa.get("emoji_avg_open")),
        ("Personalized (you/your)", sa.get("personalized_count", 0), sa.get("personalized_avg_open")),
    ]

    for label, count, avg in rows:
        if count > 0:
            table.add_row(label, str(count), _pct(avg))

    console.print(table)
    console.print()


def print_send_time_analysis(sta):
    """Print send-time performance breakdown."""
    console.print("[bold underline]Send Time Analysis[/]")
    console.print()

    by_day = sta.get("by_day", {})
    if by_day:
        console.print("[bold]By Day of Week:[/]")
        table = Table(box=box.SIMPLE)
        table.add_column("Day", style="bold")
        table.add_column("Broadcasts", justify="right")
        table.add_column("Avg Open Rate", justify="right")

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in day_order:
            if day in by_day:
                data = by_day[day]
                table.add_row(day, str(data["count"]), _pct(data["avg_open_rate"]))

        console.print(table)
        console.print()

    by_hour = sta.get("by_hour", {})
    if by_hour:
        console.print("[bold]By Hour of Day (UTC):[/]")
        table = Table(box=box.SIMPLE)
        table.add_column("Hour", style="bold")
        table.add_column("Broadcasts", justify="right")
        table.add_column("Avg Open Rate", justify="right")

        for hour in sorted(by_hour.keys()):
            data = by_hour[hour]
            table.add_row(f"{hour:02d}:00", str(data["count"]), _pct(data["avg_open_rate"]))

        console.print(table)
        console.print()


def print_trends(trends):
    """Print chronological performance trend."""
    if not trends:
        return

    console.print("[bold underline]Performance Trend (Chronological)[/]")
    console.print()

    table = Table(box=box.SIMPLE, show_lines=False)
    table.add_column("Date", style="dim")
    table.add_column("Subject", max_width=45)
    table.add_column("Recipients", justify="right")
    table.add_column("Open Rate", justify="right")
    table.add_column("Click Rate", justify="right")
    table.add_column("Unsubs", justify="right")

    for entry in trends:
        date_str = entry["date"].strftime("%Y-%m-%d") if entry["date"] else "—"
        table.add_row(
            date_str,
            (entry["subject"] or "(no subject)")[:45],
            f"{entry['recipients']:,}",
            _pct(entry["open_rate"]),
            _pct(entry["click_rate"]),
            _pct(entry["unsubscribe_rate"]),
        )

    console.print(table)
    console.print()


def print_top_links(links, top_n=10):
    """Print top performing links across all broadcasts."""
    if not links:
        return

    console.print("[bold underline]Top Clicked Links (Across All Broadcasts)[/]")
    console.print()

    table = Table(box=box.SIMPLE)
    table.add_column("#", style="dim", width=3)
    table.add_column("URL", max_width=70)
    table.add_column("Unique Clicks", justify="right")
    table.add_column("Avg CTO Rate", justify="right")

    for i, (url, clicks, cto) in enumerate(links[:top_n], 1):
        display_url = url if len(url) <= 70 else url[:67] + "..."
        table.add_row(str(i), display_url, str(clicks), _pct(cto))

    console.print(table)
    console.print()


def print_recommendations(recs):
    """Print actionable recommendations."""
    console.print("[bold underline]Recommendations[/]")
    console.print()

    if not recs:
        console.print("[dim]No specific recommendations — your metrics look solid![/]")
        console.print()
        return

    # Sort by priority: high -> medium -> low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs_sorted = sorted(recs, key=lambda r: priority_order.get(r["priority"], 9))

    for rec in recs_sorted:
        color = PRIORITY_COLORS.get(rec["priority"], "white")
        priority_label = rec["priority"].upper()
        console.print(
            Panel(
                f"[bold]{rec['title']}[/bold]\n\n{rec['detail']}",
                title=f"[{color}][{priority_label}][/{color}] {rec['category']}",
                border_style=color,
                expand=False,
                width=90,
            )
        )

    console.print()


# ------------------------------------------------------------------ #
# Full report
# ------------------------------------------------------------------ #


def print_full_report(summary, benchmarks, top_open, bottom_open, top_click,
                      bottom_click, subject_analysis, send_time_analysis,
                      trends, links, recommendations):
    """Print the complete analysis report."""
    print_header()
    print_summary(summary)
    print_benchmarks(benchmarks)
    print_top_bottom(top_open, bottom_open, metric_label="Open Rate")
    print_top_bottom(top_click, bottom_click, metric_label="Click Rate")
    print_subject_line_analysis(subject_analysis)
    print_send_time_analysis(send_time_analysis)
    print_trends(trends)
    print_top_links(links)
    print_recommendations(recommendations)

    console.print(
        Panel(
            "[dim]Data sourced from Kit.com API v4. Benchmarks based on creator/newsletter industry averages.\n"
            "Open-rate accuracy depends on email client image loading; actual engagement may be higher.[/dim]",
            style="dim",
            expand=False,
        )
    )
    console.print()
