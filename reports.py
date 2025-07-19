from flask import Blueprint
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response, current_app, session)
from flask_session import Session

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def homeReports():
    return render_template('reports.home.html')