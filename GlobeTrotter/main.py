from decimal import Decimal, InvalidOperation
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from . import db
from .models import Trip, City, Activity, Expense

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    featured = City.query.order_by(City.popularity.desc()).limit(6).all()
    return render_template("landing.html", cities=featured)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.start_date.asc()).all()
    cities = City.query.order_by(City.popularity.desc()).limit(6).all()
    return render_template("dashboard.html", trips=trips, cities=cities)

@main_bp.route("/cities")
@login_required
def cities():
    q = request.args.get("q", "").strip()
    region = request.args.get("region", "all")
    cost = request.args.get("cost", "all")
    sort = request.args.get("sort", "popularity_desc")
    group_by = request.args.get("group_by", "none")
    query = City.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(City.name.ilike(like), City.country.ilike(like), City.region.ilike(like)))
    if region != "all":
        query = query.filter(City.region == region)
    if cost == "low":
        query = query.filter(City.cost_index < 40)
    elif cost == "medium":
        query = query.filter(City.cost_index.between(40, 70))
    elif cost == "high":
        query = query.filter(City.cost_index > 70)
    cities = query.all()
    sort_options = {
        "name_asc": lambda city: city.name.lower(),
        "cost_asc": lambda city: city.cost_index,
        "popularity_desc": lambda city: city.popularity,
    }
    cities.sort(key=sort_options.get(sort, sort_options["popularity_desc"]), reverse=sort == "popularity_desc")
    cities = cities[:30]
    groups = []
    if group_by == "region":
        for label in sorted({city.region or "Other" for city in cities}):
            groups.append((label, [city for city in cities if (city.region or "Other") == label]))
    elif group_by == "country":
        for label in sorted({city.country for city in cities}):
            groups.append((label, [city for city in cities if city.country == label]))
    elif cities:
        groups.append((None, cities))
    regions = [row[0] for row in db.session.query(City.region).filter(City.region.isnot(None)).distinct().order_by(City.region)]
    return render_template("cities.html", city_groups=groups, q=q, region=region, cost=cost,
                           sort=sort, group_by=group_by, regions=regions)

@main_bp.route("/city/<int:city_id>/activities")
@login_required
def activities(city_id):
    city = City.query.get_or_404(city_id)
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "all")
    cost = request.args.get("cost", "all")
    sort = request.args.get("sort", "cost_asc")
    group_by = request.args.get("group_by", "none")
    query = Activity.query.filter_by(city_id=city.id)
    if q:
        query = query.filter(or_(Activity.name.ilike(f"%{q}%"), Activity.category.ilike(f"%{q}%")))
    if category != "all":
        query = query.filter(Activity.category == category)
    if cost == "free":
        query = query.filter(Activity.estimated_cost == 0)
    elif cost == "budget":
        query = query.filter(Activity.estimated_cost.between(1, 1000))
    elif cost == "premium":
        query = query.filter(Activity.estimated_cost > 1000)
    activities = query.all()
    sort_options = {
        "name_asc": lambda activity: activity.name.lower(),
        "duration_desc": lambda activity: activity.duration_hours,
        "cost_asc": lambda activity: activity.estimated_cost,
    }
    activities.sort(key=sort_options.get(sort, sort_options["cost_asc"]), reverse=sort == "duration_desc")
    groups = []
    if group_by == "category":
        for label in sorted({activity.category or "Other" for activity in activities}):
            groups.append((label, [activity for activity in activities if (activity.category or "Other") == label]))
    elif activities:
        groups.append((None, activities))
    categories = [row[0] for row in db.session.query(Activity.category).filter_by(city_id=city.id).filter(Activity.category.isnot(None)).distinct().order_by(Activity.category)]
    return render_template("activities.html", city=city, activity_groups=groups, q=q, category=category,
                           cost=cost, sort=sort, group_by=group_by, categories=categories)

@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        language = request.form.get("language", "English")
        bio = request.form.get("bio", "").strip()
        if not 2 <= len(name) <= 120:
            flash("Name must be between 2 and 120 characters.", "danger")
        elif len(bio) > 500:
            flash("Bio is too long.", "danger")
        else:
            current_user.name, current_user.language, current_user.bio = name, language, bio
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("main.profile"))
    return render_template("profile.html")

@main_bp.route("/community")
@login_required
def community():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all")
    sort = request.args.get("sort", "created_desc")
    group_by = request.args.get("group_by", "none")
    today = date.today()
    query = Trip.query.filter_by(is_public=True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Trip.name.ilike(like), Trip.description.ilike(like)))
    trips = query.all()
    def trip_status(trip):
        if trip.end_date < today:
            return "Completed"
        if trip.start_date > today:
            return "Upcoming"
        return "Ongoing"
    if status != "all":
        trips = [trip for trip in trips if trip_status(trip).lower() == status]
    sort_options = {
        "created_desc": lambda trip: trip.created_at,
        "start_asc": lambda trip: trip.start_date,
        "name_asc": lambda trip: trip.name.lower(),
    }
    trips.sort(key=sort_options.get(sort, sort_options["created_desc"]), reverse=sort == "created_desc")
    trips = trips[:30]
    groups = []
    if group_by == "status":
        for label in ("Ongoing", "Upcoming", "Completed"):
            grouped_trips = [trip for trip in trips if trip_status(trip) == label]
            if grouped_trips:
                groups.append((label, grouped_trips))
    elif group_by == "year":
        for year in sorted({trip.start_date.year for trip in trips}, reverse=True):
            groups.append((str(year), [trip for trip in trips if trip.start_date.year == year]))
    elif trips:
        groups.append((None, trips))
    return render_template("community.html", trip_groups=groups, q=q, status=status, sort=sort, group_by=group_by)

@main_bp.route("/trip/<int:trip_id>/expense", methods=["POST"])
@login_required
def add_expense(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()
    try:
        amount = Decimal(request.form.get("amount", "0"))
    except InvalidOperation:
        amount = Decimal("0")
    category = request.form.get("category", "Other").strip()
    note = request.form.get("note", "").strip()
    allowed = {"Transport", "Stay", "Meals", "Activities", "Other"}
    if amount <= 0 or amount > Decimal("100000000"):
        flash("Enter a valid positive expense amount.", "danger")
    elif category not in allowed:
        flash("Invalid expense category.", "danger")
    elif len(note) > 255:
        flash("Expense note is too long.", "danger")
    else:
        db.session.add(Expense(trip_id=trip.id, category=category, amount=amount, note=note))
        db.session.commit()
        flash("Expense added.", "success")
    return redirect(url_for("trips.budget", trip_id=trip.id))

@main_bp.route("/trip/<int:trip_id>/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(trip_id, expense_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()
    expense = Expense.query.filter_by(id=expense_id, trip_id=trip.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Expense removed.", "success")
    return redirect(url_for("trips.budget", trip_id=trip.id))

@main_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    from flask_login import logout_user
    if request.form.get("confirm") != "DELETE":
        flash("Type DELETE to confirm account deletion.", "danger")
        return redirect(url_for("main.profile"))
    user = current_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Your account has been deleted.", "info")
    return redirect(url_for("main.index"))
