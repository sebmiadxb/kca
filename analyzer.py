"""Analyze Kit.com broadcast performance and generate insights."""

from datetime import datetime
from config import BENCHMARKS


def _parse_dt(dt_str):
    """Parse an ISO-8601 datetime string from the Kit API."""
    if not dt_str:
        return None
    # Handle both "Z" suffix and "+00:00" offset
    dt_str = dt_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def _safe_div(numerator, denominator):
    if denominator:
        return numerator / denominator
    return 0.0


# ------------------------------------------------------------------ #
# Core analysis
# ------------------------------------------------------------------ #


def compute_summary(broadcasts):
    """Compute aggregate summary metrics across all sent broadcasts.

    Args:
        broadcasts: list of enriched broadcast dicts (from KitClient.get_all_broadcast_data)

    Returns:
        dict with aggregate metrics.
    """
    sent = [
        b for b in broadcasts
        if b.get("stats", {}).get("status") not in ("draft", None)
        and b.get("stats", {}).get("recipients", 0) > 0
    ]

    if not sent:
        return {"total_broadcasts": 0, "error": "No sent broadcasts found."}

    total_recipients = sum(b["stats"]["recipients"] for b in sent)
    total_opened = sum(b["stats"].get("emails_opened", 0) for b in sent)
    total_clicks = sum(b["stats"].get("total_clicks", 0) for b in sent)
    total_unsubs = sum(b["stats"].get("unsubscribes", 0) for b in sent)

    open_rates = [b["stats"]["open_rate"] for b in sent]
    click_rates = [b["stats"]["click_rate"] for b in sent]
    unsub_rates = [b["stats"]["unsubscribe_rate"] for b in sent]

    avg_open = sum(open_rates) / len(open_rates)
    avg_click = sum(click_rates) / len(click_rates)
    avg_unsub = sum(unsub_rates) / len(unsub_rates)
    avg_cto = _safe_div(total_clicks, total_opened) if total_opened else 0.0

    return {
        "total_broadcasts": len(sent),
        "total_recipients": total_recipients,
        "total_opened": total_opened,
        "total_clicks": total_clicks,
        "total_unsubscribes": total_unsubs,
        "avg_open_rate": avg_open,
        "avg_click_rate": avg_click,
        "avg_click_to_open_rate": avg_cto,
        "avg_unsubscribe_rate": avg_unsub,
        "max_open_rate": max(open_rates),
        "min_open_rate": min(open_rates),
        "max_click_rate": max(click_rates),
        "min_click_rate": min(click_rates),
    }


def rank_broadcasts(broadcasts, metric="open_rate", top_n=5):
    """Return the top-N and bottom-N broadcasts sorted by a stat metric.

    Args:
        broadcasts: enriched broadcast list.
        metric: key inside the ``stats`` dict to rank by.
        top_n: how many to return from each end.

    Returns:
        (top_list, bottom_list) — each entry is (broadcast, value).
    """
    sent = [
        b for b in broadcasts
        if b.get("stats", {}).get("status") not in ("draft", None)
        and b.get("stats", {}).get("recipients", 0) > 0
    ]
    ranked = sorted(sent, key=lambda b: b["stats"].get(metric, 0), reverse=True)
    top = [(b, b["stats"].get(metric, 0)) for b in ranked[:top_n]]
    bottom = [(b, b["stats"].get(metric, 0)) for b in ranked[-top_n:]]
    return top, bottom


def analyze_subject_lines(broadcasts):
    """Identify patterns in subject lines correlated with higher engagement.

    Returns a dict of observations.
    """
    sent = [
        b for b in broadcasts
        if b.get("stats", {}).get("status") not in ("draft", None)
        and b.get("stats", {}).get("recipients", 0) > 0
    ]
    if not sent:
        return {}

    # Bucket by characteristics
    short_subjects = []  # <= 40 chars
    long_subjects = []   # > 60 chars
    medium_subjects = [] # 41-60 chars
    question_subjects = []
    number_subjects = []
    emoji_subjects = []
    personalized_subjects = []  # contains "you" or "your"

    for b in sent:
        subject = b.get("subject", "") or ""
        opr = b["stats"].get("open_rate", 0)
        entry = (subject, opr)

        slen = len(subject)
        if slen <= 40:
            short_subjects.append(entry)
        elif slen > 60:
            long_subjects.append(entry)
        else:
            medium_subjects.append(entry)

        if "?" in subject:
            question_subjects.append(entry)
        if any(ch.isdigit() for ch in subject):
            number_subjects.append(entry)
        if any(ord(ch) > 127 for ch in subject):
            emoji_subjects.append(entry)

        lower = subject.lower()
        if "you" in lower or "your" in lower:
            personalized_subjects.append(entry)

    def _avg(entries):
        if not entries:
            return None
        return sum(v for _, v in entries) / len(entries)

    return {
        "short_subject_avg_open": _avg(short_subjects),
        "short_subject_count": len(short_subjects),
        "medium_subject_avg_open": _avg(medium_subjects),
        "medium_subject_count": len(medium_subjects),
        "long_subject_avg_open": _avg(long_subjects),
        "long_subject_count": len(long_subjects),
        "question_avg_open": _avg(question_subjects),
        "question_count": len(question_subjects),
        "number_avg_open": _avg(number_subjects),
        "number_count": len(number_subjects),
        "emoji_avg_open": _avg(emoji_subjects),
        "emoji_count": len(emoji_subjects),
        "personalized_avg_open": _avg(personalized_subjects),
        "personalized_count": len(personalized_subjects),
    }


def analyze_send_times(broadcasts):
    """Analyze performance by day-of-week and hour-of-day.

    Returns:
        dict with ``by_day`` and ``by_hour`` breakdowns.
    """
    by_day = {}   # day_name -> [open_rate, ...]
    by_hour = {}  # hour (0-23) -> [open_rate, ...]

    for b in broadcasts:
        stats = b.get("stats", {})
        if stats.get("status") in ("draft", None) or stats.get("recipients", 0) == 0:
            continue

        dt = _parse_dt(b.get("send_at") or b.get("published_at"))
        if not dt:
            continue

        opr = stats.get("open_rate", 0)
        day_name = dt.strftime("%A")
        hour = dt.hour

        by_day.setdefault(day_name, []).append(opr)
        by_hour.setdefault(hour, []).append(opr)

    def _summarize(bucket):
        return {
            k: {"avg_open_rate": sum(v) / len(v), "count": len(v)}
            for k, v in bucket.items()
        }

    return {
        "by_day": _summarize(by_day),
        "by_hour": _summarize(by_hour),
    }


def analyze_trends(broadcasts):
    """Compute a chronological trend of key metrics.

    Returns a list of dicts sorted by send date, each with date, subject,
    open_rate, click_rate, unsubscribe_rate, recipients.
    """
    entries = []
    for b in broadcasts:
        stats = b.get("stats", {})
        if stats.get("status") in ("draft", None) or stats.get("recipients", 0) == 0:
            continue
        dt = _parse_dt(b.get("send_at") or b.get("published_at"))
        entries.append({
            "date": dt,
            "subject": b.get("subject", ""),
            "recipients": stats.get("recipients", 0),
            "open_rate": stats.get("open_rate", 0),
            "click_rate": stats.get("click_rate", 0),
            "unsubscribe_rate": stats.get("unsubscribe_rate", 0),
            "total_clicks": stats.get("total_clicks", 0),
        })
    entries.sort(key=lambda e: e["date"] or datetime.min)
    return entries


def analyze_links(broadcasts):
    """Aggregate link-level click data across all broadcasts.

    Returns a sorted list of (url, total_unique_clicks, avg_cto_rate).
    """
    link_data = {}  # url -> {clicks: int, cto_rates: []}
    for b in broadcasts:
        for click in b.get("clicks", []):
            url = click.get("url", "")
            if not url:
                continue
            entry = link_data.setdefault(url, {"clicks": 0, "cto_rates": []})
            entry["clicks"] += click.get("unique_clicks", 0)
            cto = click.get("click_to_open_rate", 0)
            if cto:
                entry["cto_rates"].append(cto)

    result = []
    for url, data in link_data.items():
        avg_cto = sum(data["cto_rates"]) / len(data["cto_rates"]) if data["cto_rates"] else 0
        result.append((url, data["clicks"], avg_cto))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


# ------------------------------------------------------------------ #
# Benchmark comparison
# ------------------------------------------------------------------ #


def compare_to_benchmarks(summary):
    """Compare aggregate metrics to industry benchmarks.

    Returns a dict mapping metric_name -> {value, benchmark, delta, verdict}.
    """
    comparisons = {}
    mapping = [
        ("avg_open_rate", "open_rate", "Open Rate"),
        ("avg_click_rate", "click_rate", "Click Rate"),
        ("avg_click_to_open_rate", "click_to_open_rate", "Click-to-Open Rate"),
        ("avg_unsubscribe_rate", "unsubscribe_rate", "Unsubscribe Rate"),
    ]
    for key, bench_key, label in mapping:
        value = summary.get(key, 0)
        bench = BENCHMARKS.get(bench_key, 0)
        delta = value - bench
        if bench_key == "unsubscribe_rate":
            # Lower is better for unsubscribes
            verdict = "good" if value <= bench else "needs_attention"
        else:
            if delta >= 0.02:
                verdict = "excellent"
            elif delta >= 0:
                verdict = "good"
            elif delta >= -0.05:
                verdict = "below_average"
            else:
                verdict = "needs_attention"
        comparisons[label] = {
            "value": value,
            "benchmark": bench,
            "delta": delta,
            "verdict": verdict,
        }
    return comparisons


# ------------------------------------------------------------------ #
# Recommendations engine
# ------------------------------------------------------------------ #


def generate_recommendations(summary, subject_analysis, send_time_analysis, benchmark_comparison, trends):
    """Generate actionable recommendations based on the analysis.

    Returns a list of recommendation dicts with priority, category, and text.
    """
    recs = []

    # --- Open Rate Recommendations ---
    opr = summary.get("avg_open_rate", 0)
    if opr < BENCHMARKS["open_rate"]:
        recs.append({
            "priority": "high",
            "category": "Open Rate",
            "title": "Open rate is below industry average",
            "detail": (
                f"Your average open rate ({opr:.1%}) is below the industry benchmark "
                f"({BENCHMARKS['open_rate']:.1%}). Focus on improving subject lines, "
                "preview text, and sender reputation."
            ),
        })

    # Subject line length insights
    sa = subject_analysis
    best_length = None
    best_open = 0
    for bucket, key in [("short", "short_subject_avg_open"),
                        ("medium", "medium_subject_avg_open"),
                        ("long", "long_subject_avg_open")]:
        val = sa.get(key)
        if val is not None and val > best_open:
            best_open = val
            best_length = bucket

    if best_length:
        length_map = {"short": "40 characters or fewer", "medium": "41-60 characters", "long": "over 60 characters"}
        recs.append({
            "priority": "medium",
            "category": "Subject Lines",
            "title": f"Best performing subject line length: {best_length}",
            "detail": (
                f"Subject lines with {length_map[best_length]} had the highest average open rate "
                f"({best_open:.1%}). Consider keeping your subject lines in this range."
            ),
        })

    # Question subjects
    if sa.get("question_count", 0) >= 2:
        q_open = sa.get("question_avg_open", 0)
        if q_open > opr:
            recs.append({
                "priority": "medium",
                "category": "Subject Lines",
                "title": "Questions in subject lines boost opens",
                "detail": (
                    f"Subject lines containing a question mark averaged {q_open:.1%} open rate "
                    f"vs your overall {opr:.1%}. Consider using curiosity-driven questions more often."
                ),
            })

    # Personalization
    if sa.get("personalized_count", 0) >= 2:
        p_open = sa.get("personalized_avg_open", 0)
        if p_open > opr:
            recs.append({
                "priority": "medium",
                "category": "Subject Lines",
                "title": "Personalized subject lines perform better",
                "detail": (
                    f"Subject lines with 'you/your' averaged {p_open:.1%} open rate. "
                    "Consider more second-person language to increase relevance."
                ),
            })

    # --- Click Rate Recommendations ---
    ctr = summary.get("avg_click_rate", 0)
    if ctr < BENCHMARKS["click_rate"]:
        recs.append({
            "priority": "high",
            "category": "Click Rate",
            "title": "Click rate is below industry average",
            "detail": (
                f"Your average click rate ({ctr:.1%}) is below the benchmark "
                f"({BENCHMARKS['click_rate']:.1%}). Try clearer CTAs, fewer links, "
                "and ensuring link placement is above the fold."
            ),
        })

    cto = summary.get("avg_click_to_open_rate", 0)
    if cto < BENCHMARKS["click_to_open_rate"]:
        recs.append({
            "priority": "medium",
            "category": "Content",
            "title": "Click-to-open rate needs improvement",
            "detail": (
                f"Your CTO rate ({cto:.1%}) suggests that while people open your emails, "
                "the content isn't compelling enough clicks. Improve your CTA copy, "
                "make links more prominent, and ensure content matches subject-line promises."
            ),
        })

    # --- Unsubscribe Rate ---
    unsub = summary.get("avg_unsubscribe_rate", 0)
    if unsub > BENCHMARKS["unsubscribe_rate"]:
        recs.append({
            "priority": "high",
            "category": "List Health",
            "title": "Unsubscribe rate is above average",
            "detail": (
                f"Your unsubscribe rate ({unsub:.1%}) exceeds the benchmark "
                f"({BENCHMARKS['unsubscribe_rate']:.1%}). Review email frequency, "
                "content relevance, and subscriber expectations set during signup."
            ),
        })

    # --- Send Time Recommendations ---
    by_day = send_time_analysis.get("by_day", {})
    if by_day:
        best_day = max(by_day.items(), key=lambda x: x[1]["avg_open_rate"])
        worst_day = min(by_day.items(), key=lambda x: x[1]["avg_open_rate"])
        if best_day[1]["avg_open_rate"] - worst_day[1]["avg_open_rate"] > 0.03:
            recs.append({
                "priority": "medium",
                "category": "Send Timing",
                "title": f"Best send day: {best_day[0]}",
                "detail": (
                    f"Emails sent on {best_day[0]} average {best_day[1]['avg_open_rate']:.1%} open rate "
                    f"vs {worst_day[0]} at {worst_day[1]['avg_open_rate']:.1%}. "
                    f"Consider scheduling more campaigns on {best_day[0]}."
                ),
            })

    by_hour = send_time_analysis.get("by_hour", {})
    if by_hour:
        best_hour = max(by_hour.items(), key=lambda x: x[1]["avg_open_rate"])
        if best_hour[1]["count"] >= 2:
            hour_label = f"{best_hour[0]}:00"
            recs.append({
                "priority": "low",
                "category": "Send Timing",
                "title": f"Best performing send hour: {hour_label}",
                "detail": (
                    f"Emails sent around {hour_label} averaged "
                    f"{best_hour[1]['avg_open_rate']:.1%} open rate "
                    f"(based on {best_hour[1]['count']} broadcasts). "
                    "Consider testing this time slot more frequently."
                ),
            })

    # --- Trend Recommendations ---
    if len(trends) >= 4:
        half = len(trends) // 2
        first_half_open = sum(t["open_rate"] for t in trends[:half]) / half
        second_half_open = sum(t["open_rate"] for t in trends[half:]) / (len(trends) - half)
        if second_half_open < first_half_open - 0.03:
            recs.append({
                "priority": "high",
                "category": "Trend",
                "title": "Open rate is declining over time",
                "detail": (
                    f"Your open rate dropped from ~{first_half_open:.1%} in earlier emails "
                    f"to ~{second_half_open:.1%} in recent ones. Consider re-engaging inactive "
                    "subscribers, cleaning your list, or refreshing your content strategy."
                ),
            })
        elif second_half_open > first_half_open + 0.03:
            recs.append({
                "priority": "low",
                "category": "Trend",
                "title": "Open rate is improving — keep it up",
                "detail": (
                    f"Your open rate improved from ~{first_half_open:.1%} to ~{second_half_open:.1%}. "
                    "Whatever changes you made recently are working."
                ),
            })

    # --- General best-practice recommendations ---
    if summary.get("total_broadcasts", 0) < 10:
        recs.append({
            "priority": "low",
            "category": "Data",
            "title": "Limited data for analysis",
            "detail": (
                f"Only {summary['total_broadcasts']} broadcasts analyzed. "
                "Patterns and recommendations will become more reliable as you send more emails."
            ),
        })

    return recs
