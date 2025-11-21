"""
Main routes for the web platform
"""
from flask import Blueprint, render_template, jsonify

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@bp.route('/campaigns')
def campaigns_page():
    """Campaigns management page"""
    return render_template('campaigns.html')

@bp.route('/contacts')
def contacts_page():
    """Contacts management page"""
    return render_template('contacts.html')

@bp.route('/templates')
def templates_page():
    """Templates management page"""
    return render_template('templates.html')

@bp.route('/accounts')
def accounts_page():
    """SMTP accounts management page"""
    return render_template('accounts.html')

@bp.route('/settings')
def settings_page():
    """Settings page"""
    return render_template('settings.html')

