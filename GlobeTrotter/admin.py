from functools import wraps
from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from . import db
from .models import User, Trip, City, Activity, Expense, TripStop, TripActivity

admin_bp = Blueprint("admin", __name__)

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper

@admin_bp.route("/")
@admin_required
def dashboard():
    # Get filter parameters
    user_filter = request.args.get("user_filter", "all")
    sort_by = request.args.get("sort_by", "created_desc")
    
    # Basic stats
    total_users = User.query.count()
    total_trips = Trip.query.count()
    total_cities = City.query.count()
    total_activities = Activity.query.count()
    public_trips = Trip.query.filter_by(is_public=True).count()
    
    # Users who have created at least one trip
    users_with_trips = db.session.query(User.id).join(Trip).distinct().count()
    
    # Average trips per user - FIXED
    # Get total trips and total users, then calculate average manually
    if total_users > 0:
        avg_trips_per_user = total_trips / total_users
    else:
        avg_trips_per_user = 0
    
    # Total expenses across all trips
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    
    # Most active users (by trip count)
    top_users = db.session.query(
        User.id,
        User.name,
        User.email,
        User.created_at,
        func.count(Trip.id).label('trip_count')
    ).outerjoin(Trip).group_by(User.id).order_by(func.count(Trip.id).desc()).limit(10).all()
    
    # New users this month
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = User.query.filter(User.created_at >= month_start).count()
    
    # Trips by status
    today = datetime.now().date()
    upcoming_trips = Trip.query.filter(Trip.start_date > today).count()
    ongoing_trips = Trip.query.filter(and_(Trip.start_date <= today, Trip.end_date >= today)).count()
    completed_trips = Trip.query.filter(Trip.end_date < today).count()
    
    # Activity categories distribution
    category_counts = db.session.query(
        Activity.category, 
        func.count(Activity.id).label('count')
    ).filter(Activity.category.isnot(None)).group_by(Activity.category).order_by(func.count(Activity.id).desc()).all()
    
    # Top cities by trip stops
    top_cities = db.session.query(
        City.id,
        City.name,
        City.country,
        City.popularity,
        func.count(TripStop.id).label('stop_count')
    ).outerjoin(TripStop).group_by(City.id).order_by(func.count(TripStop.id).desc()).limit(10).all()
    
    # Monthly signups for the last 6 months
    monthly_signups = []
    for i in range(6):
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1)
        count = User.query.filter(and_(
            User.created_at >= month_start,
            User.created_at < month_end
        )).count()
        monthly_signups.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    monthly_signups.reverse()
    
    # User list with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build user query with filters
    user_query = User.query
    if user_filter == "active":
        user_query = user_query.join(Trip).distinct()
    elif user_filter == "inactive":
        user_query = user_query.outerjoin(Trip).group_by(User.id).having(func.count(Trip.id) == 0)
    
    # Apply sorting
    if sort_by == "created_desc":
        user_query = user_query.order_by(User.created_at.desc())
    elif sort_by == "created_asc":
        user_query = user_query.order_by(User.created_at.asc())
    elif sort_by == "name_asc":
        user_query = user_query.order_by(User.name.asc())
    elif sort_by == "name_desc":
        user_query = user_query.order_by(User.name.desc())
    elif sort_by == "trips_desc":
        user_query = user_query.outerjoin(Trip).group_by(User.id).order_by(func.count(Trip.id).desc())
    
    # Paginate users
    users_pagination = user_query.paginate(page=page, per_page=per_page, error_out=False)
    users = users_pagination.items
    
    # Get trip count for each user in the current page
    user_ids = [u.id for u in users]
    user_trip_counts = {}
    if user_ids:
        trip_counts = db.session.query(
            Trip.user_id,
            func.count(Trip.id).label('count')
        ).filter(Trip.user_id.in_(user_ids)).group_by(Trip.user_id).all()
        user_trip_counts = {tc[0]: tc[1] for tc in trip_counts}
    
    stats = {
        "users": total_users,
        "trips": total_trips,
        "cities": total_cities,
        "activities": total_activities,
        "public_trips": public_trips,
        "users_with_trips": users_with_trips,
        "avg_trips_per_user": round(avg_trips_per_user, 1),
        "total_expenses": round(total_expenses, 2),
        "new_users_this_month": new_users_this_month,
        "upcoming_trips": upcoming_trips,
        "ongoing_trips": ongoing_trips,
        "completed_trips": completed_trips
    }
    
    return render_template("admin.html", 
                         stats=stats, 
                         top_cities=top_cities,
                         top_users=top_users,
                         category_counts=category_counts,
                         monthly_signups=monthly_signups,
                         users=users,
                         user_trip_counts=user_trip_counts,
                         users_pagination=users_pagination,
                         user_filter=user_filter,
                         sort_by=sort_by)