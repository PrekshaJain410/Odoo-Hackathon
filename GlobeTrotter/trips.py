from datetime import date, datetime
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_ 
from . import db
from .models import Trip, City, TripStop, Activity, TripActivity

trips_bp = Blueprint("trips", __name__)

def owned_trip(trip_id):
    return Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

@trips_bp.route("/trips")
@login_required
def list_trips():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "all")
    sort = request.args.get("sort", "start_desc")
    group_by = request.args.get("group_by", "none")
    today = date.today()

    query = Trip.query.filter_by(user_id=current_user.id)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Trip.name.ilike(term), Trip.description.ilike(term)))
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
        "start_asc": lambda trip: trip.start_date,
        "name_asc": lambda trip: trip.name.lower(),
        "duration_desc": lambda trip: (trip.end_date - trip.start_date).days,
        "start_desc": lambda trip: trip.start_date,
    }
    trips.sort(key=sort_options.get(sort, sort_options["start_desc"]), reverse=sort in {"start_desc", "duration_desc"})

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

    return render_template("trips.html", trip_groups=groups, q=search, status=status,
                           sort=sort, group_by=group_by)

@trips_bp.route("/trip/new", methods=["GET", "POST"])
@login_required
def new_trip():
    # Check if editing an existing trip
    edit_trip_id = request.args.get('edit', type=int)
    edit_trip = None
    
    if edit_trip_id:
        edit_trip = owned_trip(edit_trip_id)
    
    if request.method == "POST":
        # Check if we're editing or creating
        is_edit = request.form.get('edit_trip_id')
        trip_id = int(is_edit) if is_edit else None
        
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        start = parse_date(request.form.get("start_date"))
        end = parse_date(request.form.get("end_date"))
        
        if not 2 <= len(name) <= 180:
            flash("Trip name must be 2–180 characters.", "danger")
        elif not start or not end or end < start:
            flash("Please enter a valid date range.", "danger")
        elif (end - start).days > 365:
            flash("Trip duration cannot exceed one year.", "danger")
        elif len(description) > 5000:
            flash("Description is too long.", "danger")
        else:
            if trip_id:
                # Update existing trip
                trip = owned_trip(trip_id)
                trip.name = name
                trip.description = description
                trip.start_date = start
                trip.end_date = end
                flash("Trip updated successfully.", "success")
            else:
                # Create new trip
                trip = Trip(
                    name=name, 
                    description=description, 
                    start_date=start, 
                    end_date=end,
                    user_id=current_user.id, 
                    share_token=uuid4().hex
                )
                db.session.add(trip)
                flash("Trip created. Now add your stops.", "success")
            
            db.session.commit()
            return redirect(url_for("trips.itinerary", trip_id=trip.id))
    
    return render_template("new_trip.html", edit_trip=edit_trip)

@trips_bp.route("/trip/<int:trip_id>")
@login_required
def itinerary(trip_id):
    trip = owned_trip(trip_id)
    return render_template("itinerary.html", trip=trip)

@trips_bp.route("/trip/<int:trip_id>/stop", methods=["POST"])
@login_required
def add_stop(trip_id):
    trip = owned_trip(trip_id)
    
    # Check if it's a dynamic city or existing city
    city_id = request.form.get("city_id", type=int)
    dynamic_city_name = request.form.get("dynamic_city_name", "").strip()
    dynamic_country = request.form.get("dynamic_country", "").strip()
    dynamic_region = request.form.get("dynamic_region", "").strip()
    
    start, end = parse_date(request.form.get("start_date")), parse_date(request.form.get("end_date"))
    
    if not start or not end or end < start:
        flash("Invalid stop dates.", "danger")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))
    elif start < trip.start_date or end > trip.end_date:
        flash("Stop dates must be inside the trip dates.", "danger")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))
    
    # Handle dynamic city creation
    if dynamic_city_name and dynamic_country:
        # Check if city already exists
        existing_city = City.query.filter(
            or_(
                and_(City.name.ilike(dynamic_city_name), City.country.ilike(dynamic_country)),
                City.name.ilike(dynamic_city_name)
            )
        ).first()
        
        if existing_city:
            city = existing_city
            flash(f"Using existing city: {city.name}, {city.country}", "info")
        else:
            # Create new city
            city = City(
                name=dynamic_city_name,
                country=dynamic_country,
                region=dynamic_region or "Other",
                cost_index=50,
                popularity=30,
                description=f"A custom destination added by {current_user.name}"
            )
            db.session.add(city)
            db.session.flush()  # Get the ID without committing
            flash(f"New city '{city.name}' added to the database!", "success")
    elif city_id:
        city = City.query.get_or_404(city_id)
    else:
        flash("Please select or add a city.", "danger")
        return redirect(url_for("trips.itinerary", trip_id=trip.id))
    
    # Add the stop
    db.session.add(TripStop(
        trip_id=trip.id, 
        city_id=city.id, 
        start_date=start, 
        end_date=end,
        position=len(trip.stops)
    ))
    db.session.commit()
    flash(f"{city.name} added to your itinerary.", "success")
    return redirect(url_for("trips.itinerary", trip_id=trip.id))

@trips_bp.route("/trip/<int:trip_id>/stop/<int:stop_id>/delete", methods=["POST"])
@login_required
def delete_stop(trip_id, stop_id):
    trip = owned_trip(trip_id)
    stop = TripStop.query.filter_by(id=stop_id, trip_id=trip.id).first_or_404()
    db.session.delete(stop)
    db.session.commit()
    flash("Stop removed.", "success")
    return redirect(url_for("trips.itinerary", trip_id=trip.id))

@trips_bp.route("/trip/<int:trip_id>/activity", methods=["POST"])
@login_required
def add_activity(trip_id):
    trip = owned_trip(trip_id)
    stop = TripStop.query.filter_by(id=request.form.get("stop_id", type=int), trip_id=trip.id).first_or_404()
    activity = Activity.query.get_or_404(request.form.get("activity_id", type=int))
    day = parse_date(request.form.get("date"))
    time = request.form.get("start_time", "10:00").strip()
    if not day or not (stop.start_date <= day <= stop.end_date):
        flash("Activity date must be within the selected stop.", "danger")
    elif len(time) > 10:
        flash("Invalid start time.", "danger")
    else:
        db.session.add(TripActivity(stop_id=stop.id, activity_id=activity.id, date=day, start_time=time))
        db.session.commit()
        flash("Activity added.", "success")
    return redirect(url_for("trips.itinerary", trip_id=trip.id))

@trips_bp.route("/trip/<int:trip_id>/activity/<int:activity_id>/delete", methods=["POST"])
@login_required
def delete_activity(trip_id, activity_id):
    trip = owned_trip(trip_id)
    item = TripActivity.query.join(TripStop).filter(TripActivity.id == activity_id, TripStop.trip_id == trip.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Activity removed.", "success")
    return redirect(url_for("trips.itinerary", trip_id=trip.id))

@trips_bp.route("/trip/<int:trip_id>/budget")
@login_required
def budget(trip_id):
    trip = owned_trip(trip_id)
    totals = {}
    for e in trip.expenses:
        totals[e.category] = totals.get(e.category, 0) + float(e.amount)
    activity_total = sum(float(ta.activity.estimated_cost) for s in trip.stops for ta in s.activities)
    totals["Activities"] = totals.get("Activities", 0) + activity_total
    return render_template("budget.html", trip=trip, totals=totals, total=sum(totals.values()))

@trips_bp.route("/trip/<int:trip_id>/calendar")
@login_required
def calendar(trip_id):
    return render_template("calendar.html", trip=owned_trip(trip_id))

@trips_bp.route("/trip/<int:trip_id>/publish", methods=["POST"])
@login_required
def publish(trip_id):
    trip = owned_trip(trip_id)
    trip.is_public = True
    db.session.commit()
    flash("Trip published to the community.", "success")
    return redirect(url_for("trips.public_trip", token=trip.share_token))

@trips_bp.route("/trip/<int:trip_id>/unpublish", methods=["POST"])
@login_required
def unpublish(trip_id):
    trip = owned_trip(trip_id)
    trip.is_public = False
    db.session.commit()
    flash("Trip is now private.", "info")
    return redirect(url_for("trips.itinerary", trip_id=trip.id))

@trips_bp.route("/trip/<int:trip_id>/delete", methods=["POST"])
@login_required
def delete_trip(trip_id):
    trip = owned_trip(trip_id)
    db.session.delete(trip)
    db.session.commit()
    flash("Trip deleted.", "success")
    return redirect(url_for("trips.list_trips"))

@trips_bp.route("/share/<token>")
def public_trip(token):
    trip = Trip.query.filter_by(share_token=token, is_public=True).first_or_404()
    return render_template("public_trip.html", trip=trip)

# New route for searching cities (for autocomplete)
@trips_bp.route("/api/cities/search")
@login_required
def search_cities():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    
    cities = City.query.filter(
        or_(
            City.name.ilike(f"%{query}%"),
            City.country.ilike(f"%{query}%")
        )
    ).limit(10).all()
    
    results = [{
        "id": city.id,
        "name": city.name,
        "country": city.country,
        "region": city.region
    } for city in cities]
    
    return jsonify(results)