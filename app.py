"""Kit.com Email Performance Analyzer — Web App."""

from flask import Flask, render_template, request, redirect, url_for, session
import os

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

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))


@app.route("/")
def index():
    """Landing page where the user enters their API key."""
    error = request.args.get("error")
    return render_template("index.html", error=error)


@app.route("/analyze", methods=["POST"])
def analyze():
    """Fetch data from Kit.com and run the analysis."""
    api_key = request.form.get("api_key", "").strip()
    if not api_key:
        return redirect(url_for("index", error="Please enter your API key."))

    # Store key in session so we don't lose it on page refresh
    session["api_key"] = api_key

    try:
        client = KitClient(api_key=api_key)
        broadcasts = client.get_all_broadcast_data()
    except KitAPIError as exc:
        return redirect(url_for("index", error=f"Kit API error: {exc.message}"))
    except ValueError as exc:
        return redirect(url_for("index", error=str(exc)))

    if not broadcasts:
        return redirect(
            url_for("index", error="No broadcasts found in your Kit.com account.")
        )

    summary = compute_summary(broadcasts)
    if summary.get("error"):
        return redirect(url_for("index", error=summary["error"]))

    top_n = 5
    top_open, bottom_open = rank_broadcasts(broadcasts, metric="open_rate", top_n=top_n)
    top_click, bottom_click = rank_broadcasts(
        broadcasts, metric="click_rate", top_n=top_n
    )
    subject_analysis = analyze_subject_lines(broadcasts)
    send_time_analysis = analyze_send_times(broadcasts)
    trends = analyze_trends(broadcasts)
    links = analyze_links(broadcasts)
    benchmarks = compare_to_benchmarks(summary)
    recommendations = generate_recommendations(
        summary, subject_analysis, send_time_analysis, benchmarks, trends
    )

    return render_template(
        "report.html",
        summary=summary,
        benchmarks=benchmarks,
        top_open=top_open,
        bottom_open=bottom_open,
        top_click=top_click,
        bottom_click=bottom_click,
        subject_analysis=subject_analysis,
        send_time_analysis=send_time_analysis,
        trends=trends,
        links=links[:10],
        recommendations=recommendations,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
