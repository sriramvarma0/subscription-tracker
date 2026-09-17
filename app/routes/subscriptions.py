from flask import Blueprint, request, redirect, url_for, flash, jsonify, g
from app.routes.auth import login_required
from app.services.subscription_service import SubscriptionService

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/subscriptions')

@subscriptions_bp.route('', methods=['POST'])
@login_required
def create():
    data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    try:
        subscription = SubscriptionService.create_subscription(g.user.id, data)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'subscription': subscription.to_dict()}), 201
        flash(f"Subscription for '{subscription.company_name}' added successfully.", "success")
        return redirect(url_for('dashboard.index'))
    except ValueError as e:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(str(e), "error")
        return redirect(url_for('dashboard.index'))

@subscriptions_bp.route('/<int:sub_id>', methods=['GET'])
@login_required
def get_one(sub_id):
    subscription = SubscriptionService.get_user_subscription(g.user.id, sub_id)
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    return jsonify({'subscription': subscription.to_dict()})

@subscriptions_bp.route('/<int:sub_id>/edit', methods=['POST'])
@login_required
def update(sub_id):
    data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    try:
        subscription = SubscriptionService.update_subscription(g.user.id, sub_id, data)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'subscription': subscription.to_dict()})
        flash(f"Subscription '{subscription.company_name}' updated successfully.", "success")
        return redirect(url_for('dashboard.index'))
    except KeyError:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Subscription not found or access denied.'}), 404
        flash("Subscription not found or access denied.", "error")
        return redirect(url_for('dashboard.index'))
    except ValueError as e:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(str(e), "error")
        return redirect(url_for('dashboard.index'))

@subscriptions_bp.route('/<int:sub_id>/renew', methods=['POST'])
@login_required
def renew(sub_id):
    data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    try:
        renewal_type = data.get('renewal_type', 'MANUAL')
        subscription = SubscriptionService.renew_subscription(g.user.id, sub_id, data, default_renewal_type=renewal_type)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'subscription': subscription.to_dict()})
        flash(f"Subscription '{subscription.company_name}' renewed successfully.", "success")
        return redirect(url_for('dashboard.index'))
    except KeyError:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Subscription not found or access denied.'}), 404
        flash("Subscription not found or access denied.", "error")
        return redirect(url_for('dashboard.index'))
    except ValueError as e:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(str(e), "error")
        return redirect(url_for('dashboard.index'))

@subscriptions_bp.route('/<int:sub_id>/delete', methods=['POST'])
@login_required
def delete(sub_id):
    try:
        SubscriptionService.delete_subscription(g.user.id, sub_id)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        flash("Subscription deleted successfully.", "success")
        return redirect(url_for('dashboard.index'))
    except KeyError:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Subscription not found or access denied.'}), 404
        flash("Subscription not found or access denied.", "error")
        return redirect(url_for('dashboard.index'))
