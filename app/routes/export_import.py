import csv
import io
import json
from datetime import datetime
from flask import Blueprint, Response, request, redirect, url_for, flash, jsonify, g
from app.routes.auth import login_required
from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription

export_import_bp = Blueprint('export_import', __name__)

@export_import_bp.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    subscriptions = SubscriptionService.get_subscriptions(user_id=g.user.id, sort_by='nearest_expiry')

    output = io.StringIO()
    writer = csv.writer(output)

    # Write Header
    writer.writerow([
        'Company Name',
        'Subscription Name',
        'Account Identifier',
        'Start Date',
        'End Date',
        'Is Sponsored',
        'Sponsor Company',
        'Sponsor Account',
        'Status',
        'Note'
    ])

    for sub in subscriptions:
        writer.writerow([
            sub.company_name,
            sub.subscription_name,
            sub.account,
            sub.start_date.isoformat() if sub.start_date else '',
            sub.end_date.isoformat() if sub.end_date else '',
            'Yes' if sub.is_sponsored else 'No',
            sub.sponsor_company or '',
            sub.sponsor_account or '',
            sub.status,
            sub.note or ''
        ])

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"subscriptions_export_{timestamp}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@export_import_bp.route('/export/json', methods=['GET'])
@login_required
def export_json():
    subscriptions = SubscriptionService.get_subscriptions(user_id=g.user.id, sort_by='nearest_expiry')
    data = [sub.to_dict() for sub in subscriptions]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"subscriptions_backup_{timestamp}.json"

    json_str = json.dumps(data, indent=2)
    return Response(
        json_str,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@export_import_bp.route('/import/json', methods=['POST'])
@login_required
def import_json():
    raw_data = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            try:
                raw_data = json.load(file)
            except Exception as e:
                flash(f"Invalid JSON file format: {str(e)}", "error")
                return redirect(url_for('dashboard.index'))
    elif request.is_json:
        raw_data = request.get_json(silent=True)

    if not raw_data or not isinstance(raw_data, list):
        flash("Import failed. Expected a JSON array of subscription objects.", "error")
        return redirect(url_for('dashboard.index'))

    imported_count = 0
    errors = []

    for idx, item in enumerate(raw_data):
        if not isinstance(item, dict):
            errors.append(f"Item #{idx + 1} is not a valid object.")
            continue
        try:
            # Force user_id to currently logged-in user
            SubscriptionService.create_subscription(g.user.id, item)
            imported_count += 1
        except ValueError as val_err:
            errors.append(f"Item #{idx + 1} ('{item.get('company_name', 'Unknown')}'): {str(val_err)}")

    if imported_count > 0:
        flash(f"Successfully imported {imported_count} subscription(s).", "success")
    if errors:
        flash(f"Skipped {len(errors)} item(s) due to validation errors. First error: {errors[0]}", "warning")

    return redirect(url_for('dashboard.index'))
