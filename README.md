# 🌍 Travel Itinerary Planner

An AI-powered web application that helps users organize **multi-day trips** by generating smart, customizable daily schedules.  
The app leverages **Google Gemini AI** to suggest activities and create optimized itineraries that users can manually edit and share.

---

## 🚀 Overview

**Travel Itinerary Planner** assists users in planning trips efficiently by:
- Generating AI-based daily itineraries.
- Allowing manual customization of activities.
- Providing shareable read-only trip links.

---

## 🏗️ Architecture

| Layer | Technology | Description |
|-------|-------------|-------------|
| **Backend** | Python (Flask) | Handles routing, AI integration, and database management |
| **Database** | SQLite (via SQLAlchemy ORM) | Stores trips and activities |
| **Frontend** | HTML5, Bootstrap 5, Custom CSS | Responsive and mobile-friendly UI |
| **AI Integration** | Google Gemini API (`google-generativeai`) | Generates activities and day-wise itineraries |

---

## 🔧 Main Components

### 1. Trip Management
- Users create trips by entering **destination**, **start date**, **number of days**, and **notes/interests**.
- Data stored in the `Trip` table.

### 2. Activity Selection
- Activities loaded from a **static JSON file** or **AI-generated suggestions**.
- Users select activities for their trip.
- Stored in the `Activity` table with a `selected` flag.

### 3. AI-Generated Scheduling
- Selected activities are sent to **Gemini AI**.
- AI groups activities by **location**, **duration**, and **category** to create a balanced daily itinerary.
- Results are validated and saved to the database.

### 4. Manual Editing
- Users can reassign activities to different days via the **Edit Itinerary** page.
- Updates are instantly reflected in the database.

### 5. Sharing
- Users can share a **read-only itinerary link**.
- The shared view displays only selected activities with their assigned days.

---

## 🔁 Workflow

1. **Create Trip:** User enters trip details.  
2. **Select Activities:** User browses AI-suggested or static activities.  
3. **Generate Schedule:** AI creates a structured day-by-day plan.  
4. **Edit Itinerary:** User adjusts or reorders activities.  
5. **Share Itinerary:** User shares the read-only itinerary link.

---

## 🧩 Data Model

| Table | Fields |
|--------|--------|
| **Trip** | `id`, `destination`, `start_date`, `num_days`, `notes` |
| **Activity** | `id`, `trip_id`, `name`, `category`, `duration`, `location`, `day`, `selected` |

---

## 🧠 AI Prompts & Behavior

AI prompts are crafted to:
- Generate relevant activities and itineraries based on user inputs.
- Return **strict JSON responses** (validated via `json.loads()`).
- Avoid markdown or free-form text.
- Respect constraints like **max 8 hours/day** and **logical grouping by location**.

**Example prompt snippet:**
```json
[
  {"name": "Eiffel Tower Visit", "category": "Sightseeing", "duration": 2, "location": "Paris"},
  {"name": "Louvre Museum Tour", "category": "Art & Culture", "duration": 3, "location": "Paris"}
]

```







---
---


# 🧭 Project Reflection: Challenges, Validation, and Code Quality

## 🚧 Challenges Faced

- **AI Integration:** Ensuring the Gemini API consistently returned valid, structured JSON for activities and schedules. In some cases, the AI response included explanations, requiring regex extraction and fallback parsing to retrieve clean JSON.
- **User Selection Logic:** Guaranteeing that only user-selected activities were used during scheduling, editing, and sharing by correctly managing the `selected` flag in the database.
- **Day Assignment:** Handling scenarios where total activity durations exceeded the 8-hour daily limit and ensuring each day received a balanced distribution of activities.
- **Manual Editing:** Allowing users to override AI-generated day assignments and persisting those changes accurately in the database.
- **Error Handling:** Providing user-friendly error feedback when AI calls failed or when no activities matched user interests.
- **Workflow Consistency:** Maintaining a seamless flow across all stages — *Create → Select → Schedule → Edit → Share* — to ensure a smooth and intuitive experience.
- **Frontend Synchronization:** Making sure edited itineraries were reflected correctly after saving by redirecting users to an updated shareable summary page.
- **Model Latency & Fallbacks:** Addressing AI latency issues by using static activity data as a backup to prevent empty screens during failures.

---

## ✅ Validation Process

### Functional Validation
Each core route was manually tested step-by-step:
- **Trip Creation:** Verified behavior with and without notes.
- **Activity Selection:** Tested both static and AI-generated activity sources.
- **Schedule Generation:** Checked that activities were logically grouped by location and duration limits.
- **Edit & Share:** Ensured manual edits were saved and the share page reflected changes.

### Data Validation
- Verified that each activity record had correct `trip_id` and `day` values.
- Ensured total activity duration per day did not exceed **8 hours**.
- Confirmed foreign key consistency to avoid orphaned records in the database.

### Edge Case Testing
- Tested with **empty notes**, **no selected activities**, and **insufficient activities** for given days.
- Handled **invalid or mixed-format AI responses** gracefully using regex-based JSON extraction and static fallback.

### Manual Verification
- Compared AI-generated itineraries against human judgment to verify logical grouping and realistic time allocations.
- Inspected SQLite database using DB Browser to confirm correct inserts, updates, and relationships.
- Reviewed frontend layout and responsiveness across devices.

### Debugging & Logging
- Console logs captured AI responses, API status, and validation outputs for debugging.
- Logged malformed responses to assist in refining AI prompts.

---

## 🧱 Code Quality Assurance

- **Modular Design:** Flask routes, AI logic, and templates are well-separated for clarity.
- **Consistent Data Model:** SQLAlchemy models (`Trip`, `Activity`) maintain a clean, normalized structure.
- **Error Handling:** Built-in fallbacks ensure functionality even if AI fails.
- **Code Comments:** Key logic, constraints, and parsing steps are clearly documented.
- **Styling & UX:** Clean and responsive interface using Bootstrap and custom CSS.
- **Naming Conventions:** Consistent, descriptive naming across functions and variables.
- **Version Control:** Git and GitHub were used for incremental commits and validation of changes.

---

## 🔮 Recommendations for Future Improvements

- Add **automated unit and integration tests** for key routes and workflows.  
- Implement **flash messages** or user alerts for clearer feedback during AI or validation failures.  
- Include **screenshots, test evidence**, and **user walkthroughs** in documentation.  
- Add advanced UI features such as **drag-and-drop activity editing** and **calendar visualization**.  
- Document **environment setup** and **API key configuration** for smooth deployment.  
- Introduce **caching or queuing mechanisms** to manage AI response latency efficiently.

---
---

# Travel Itinerary Planner - AI Prompts Documentation

This document lists the main prompts used for Google Gemini AI integration in the Travel Itinerary Planner project.

---

## 1. Activity Generation Prompt
Used to generate activities based on user notes/interests when creating or editing a trip.

```
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
[{"name": "...", "category": "...", "duration": 2, "location": "..."}]
```

---

## 2. Schedule Generation Prompt
Used to generate a day-by-day itinerary from selected activities.

```
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
```

---

## 3. Edit Schedule (Unassigned Activities) Prompt
Used to assign days to activities that have not yet been manually assigned.

```
You are a smart travel planner. I have a trip to {trip.destination} for {trip.num_days} days.
Here are unassigned activities (name, category, duration, location):
{activity_list}

Constraints:
- Max 8 hours/day
- Group nearby activities together
- Mix categories evenly
- Return JSON with day numbers as keys and list of activity names
```

---

## Notes
- Prompts are dynamically formatted with trip details and activity lists.
- Responses are parsed as JSON and used to update the itinerary in the database.
- Prompts can be further refined for improved AI results.

---




### Summary

The **Travel Itinerary Planner** project successfully integrates AI-driven itinerary generation with robust backend validation and an intuitive user interface.  
Despite challenges with AI parsing and synchronization, strong validation, modular design, and careful workflow testing ensured a stable, reliable, and user-friendly application.

---

