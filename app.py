from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import json,re
import google.generativeai as genai
genai.configure(api_key="AIzaSyCfUi_g9bHXkZBBX5ZaJJ5wddy3icbZ2Ho")  


app = Flask(__name__)

# ------------------ CONFIG ------------------
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ DATABASE MODELS ------------------
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100))
    start_date = db.Column(db.String(50))
    num_days = db.Column(db.Integer)
    notes = db.Column(db.String(300))

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    location = db.Column(db.String(100))
    day = db.Column(db.Integer, default=None)  
    selected = db.Column(db.Boolean, default=False) 

# Create all tables
with app.app_context():
    db.create_all()

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create_trip', methods=['POST'])
def create_trip():
    destination = request.form['destination']
    start_date = request.form['start_date']
    num_days = request.form['num_days']
    notes = request.form.get('notes', '')

    trip = Trip(destination=destination, start_date=start_date, num_days=num_days, notes=notes)
    db.session.add(trip)
    db.session.commit()

    return redirect(url_for('activities', trip_id=trip.id))

@app.route('/activities/<int:trip_id>', methods=['GET', 'POST'])
def activities(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    import json, re

    if request.method == 'POST':
        selected_names = request.form.getlist('activities')
        all_activities = Activity.query.filter_by(trip_id=trip.id).all()

        # Mark only selected activities
        for act in all_activities:
            act.selected = act.name in selected_names
        db.session.commit()

        return redirect(url_for('generate_schedule', trip_id=trip.id))

    # GET: Show activities
    existing_activities = Activity.query.filter_by(trip_id=trip.id).all()

    if not existing_activities:
        activities_data = []

        # If notes exist, call AI
        if trip.notes and trip.notes.strip():
            prompt = f"""
You are a travel planner. The user is visiting {trip.destination}.
User notes / interests: {trip.notes}
Give more weight to user notes when generating activities.

Generate a list of 6-9 activities with:
- name
- category (Culture, Nature, Food, Leisure, Shopping)
- duration in hours
- location (city area)
- ensure all fields are present
- return at least 6 activities
- ensure that the response is valid JSON
Return JSON only:
[{{"name": "...", "category": "...", "duration": 2, "location": "..."}}]
"""
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            raw = response.text
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                try:
                    activities_data = json.loads(match.group(0))
                    # ensure duration is numeric
                    for act in activities_data:
                        if isinstance(act['duration'], str):
                            act['duration'] = float(re.findall(r"[\d.]+", act['duration'])[0])
                except:
                    activities_data = []

        # fallback to static activities
        if not activities_data:
            with open(os.path.join('data', 'activities.json')) as f:
                activities_data = json.load(f)

        # Save to DB (all unselected by default)
        for act in activities_data:
            new_act = Activity(
                trip_id=trip.id,
                name=act['name'],
                category=act['category'],
                duration=float(act['duration']),
                location=act['location'],
                selected=False
            )
            db.session.add(new_act)
        db.session.commit()

    # Fetch activities for template (only those that exist)
    activities = Activity.query.filter_by(trip_id=trip.id).all()
    activities_for_template = [
        {
            "name": a.name,
            "category": a.category,
            "duration": a.duration,
            "location": a.location,
            "selected": a.selected
        } for a in activities
    ]

    return render_template('activities.html', trip=trip, activities=activities_for_template)

@app.route('/generate_schedule/<int:trip_id>')
def generate_schedule(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    activities = Activity.query.filter_by(trip_id=trip.id, selected=True).all()

    # Build activity list for AI prompt
    activity_list = "\n".join([f"- {a.name}, {a.category}, {a.duration} hrs, {a.location}" for a in activities])

    # AI prompt
    prompt = f"""
You are a professional travel planner.

Trip: {trip.destination}, {trip.num_days} days
Activities:
{activity_list}

Your task:
1. Distribute activities across {trip.num_days} days logically.
2. Group activities that are close by (by location).
3. Mix categories reasonably.
4. Max 8 hours/day.
5. If {trip.num_days} equals number of activities, assign one per day.
6. Return TWO sections:

SCHEDULE:
JSON object, keys=day numbers, values=list of activity names in order.

JUSTIFICATION:
Explain in 2–3 lines per day why these activities were grouped.
"""

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    response_text = response.text
    print("AI Response:", response_text)

    # ---------------- Extract JSON and justification ----------------
    import re, json

    if "JUSTIFICATION:" in response_text:
        schedule_part, justification_part = response_text.split("JUSTIFICATION:", 1)
    else:
        schedule_part, justification_part = response_text, "No justification provided."

    # Extract JSON using regex
    schedule_match = re.search(r'\{.*\}', schedule_part, re.DOTALL)
    if schedule_match:
        try:
            raw_day_plan = json.loads(schedule_match.group())
        except json.JSONDecodeError:
            raw_day_plan = {}
    else:
        raw_day_plan = {}

    # Convert keys like "Day 1" to integers
    day_plan_json = {}
    for k, v in raw_day_plan.items():
        try:
            day_num = int(re.search(r'\d+', str(k)).group())
            if 1 <= day_num <= trip.num_days:
                day_plan_json[day_num] = v
        except:
            continue

    # ---------------- Assign days to activities ----------------
    day_hours = {d: 0 for d in range(1, trip.num_days + 1)}

    for day, act_names in day_plan_json.items():
        for name in act_names:
            act = next((a for a in activities if a.name == name), None)
            if act:
                # If adding activity exceeds 8 hours, move to next day
                if day_hours[day] + act.duration > 8:
                    next_day = day + 1 if day < trip.num_days else day
                    act.day = next_day
                    day_hours[next_day] += act.duration
                else:
                    act.day = day
                    day_hours[day] += act.duration
    db.session.commit()

    # ---------------- Ensure all days have at least one activity ----------------
    assigned_days = {a.day for a in activities if a.day}
    for d in range(1, trip.num_days + 1):
        if d not in assigned_days:
            # move first unassigned activity to this day
            act_to_move = next((a for a in activities if a.day != d), None)
            if act_to_move:
                act_to_move.day = d
    db.session.commit()

    # Prepare day_plan for template
    day_plan = {d: [a for a in activities if a.day == d] for d in range(1, trip.num_days + 1)}
    justification_text = justification_part.strip()

    return render_template('itinerary.html', trip=trip, day_plan=day_plan, justification=justification_text)



@app.route('/edit_schedule/<int:trip_id>', methods=['GET', 'POST'])
def generate_schedule_edit(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    activities = Activity.query.filter_by(trip_id=trip.id, selected=True).all()
    if request.method == 'POST':
        for act in activities:
            new_day = request.form.get(f'day_{act.id}')
            if new_day:
                act.day = int(new_day)
        db.session.commit()
        return redirect(url_for('share_itinerary', trip_id=trip.id))

    # Only include activities without user-assigned day
    unassigned_activities = [a for a in activities if not a.day]

    if unassigned_activities:
        activity_list = "\n".join(
            [f"- {a.name}, {a.category}, {a.duration} hrs, {a.location}" for a in unassigned_activities]
        )

        prompt = f"""
You are a smart travel planner. I have a trip to {trip.destination} for {trip.num_days} days.
Here are unassigned activities (name, category, duration, location):
{activity_list}

Constraints:
- Max 8 hours/day
- Group nearby activities together
- Mix categories evenly
- Return JSON with day numbers as keys and list of activity names
"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        import json
        try:
            ai_schedule = json.loads(response.text)
        except:
            ai_schedule = {str(day): [] for day in range(1, trip.num_days+1)}
            for i, act in enumerate(unassigned_activities):
                ai_schedule[str((i % trip.num_days) + 1)].append(act.name)

        # Apply AI suggestions without overwriting user days
        for day_str, acts in ai_schedule.items():
            for name in acts:
                act = next((a for a in unassigned_activities if a.name == name), None)
                if act:
                    act.day = int(day_str)
        db.session.commit()

    # Prepare day_plan for template
    day_plan = {day: [a for a in activities if a.day == day] for day in range(1, trip.num_days+1)}
    return render_template('edit_itinerary.html', trip=trip, day_plan=day_plan, activities=activities)




@app.route('/share/<int:trip_id>')
def share_itinerary(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    activities = Activity.query.filter_by(trip_id=trip.id, selected=True).all()

    # Use assigned days, fallback to day 1 if not set
    day_plan = {day: [] for day in range(1, trip.num_days + 1)}
    for act in activities:
        day = act.day if act.day else 1
        day_plan[day].append(act)

    return render_template('share_itinerary.html', trip=trip, day_plan=day_plan)






# ------------------ RUN APP ------------------
if __name__ == '__main__':
    app.run(debug=True)
