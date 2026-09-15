from flask import Blueprint, render_template, request, g
from app.routes.auth import login_required
from app.services.subscription_service import SubscriptionService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@login_required
def index():
    user = g.user
    search_query = request.args.get('q', '').strip()
    filter_status = request.args.get('filter', 'All').strip()
    sort_by = request.args.get('sort', 'nearest_expiry').strip()

    summary_counts = SubscriptionService.get_user_summary_counts(user.id)
    subscriptions = SubscriptionService.get_subscriptions(
        user_id=user.id,
        search_query=search_query,
        filter_status=filter_status,
        sort_by=sort_by
    )

    return render_template(
        'dashboard/index.html',
        user=user,
        summary=summary_counts,
        subscriptions=subscriptions,
        search_query=search_query,
        current_filter=filter_status,
        current_sort=sort_by
    )

@dashboard_bp.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200
