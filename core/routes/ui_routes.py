"""
UI routes blueprint - serves the single-page app with distinct bookmarkable URLs.

Each route renders `templates/index.html` with an `active_tab` hint so
the frontend can show the correct section immediately.
"""
from flask import Blueprint, render_template


ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def index():
    return render_template("index.html", active_tab="tally-upload")


@ui_bp.route("/tally-upload")
def tally_upload():
    return render_template("index.html", active_tab="tally-upload")


@ui_bp.route("/reconciliation")
def reconciliation():
    return render_template("index.html", active_tab="reconciliation")


@ui_bp.route("/data-table")
def data_table():
    return render_template("index.html", active_tab="data-table")


@ui_bp.route("/pairs-table")
def pairs_table():
    return render_template("index.html", active_tab="pairs-table")


@ui_bp.route("/matched-results")
def matched_results():
    return render_template("index.html", active_tab="matched-results")


@ui_bp.route("/unmatched-results")
def unmatched_results():
    return render_template("index.html", active_tab="unmatched-results")


@ui_bp.route("/database-tools")
def database_tools():
    return render_template("index.html", active_tab="database-tools")


