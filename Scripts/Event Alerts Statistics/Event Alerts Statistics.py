import json
from datetime import datetime, timedelta
from pymongo import MongoClient

# Get config values
with open("config.json", "r") as file:
    config = json.load(file)
    mongo = config["mongo"]
    database_name = config["database"]
    collection_name = config["collection"]

client = MongoClient(mongo)
database = client[database_name]
collection = database[collection_name]
now = datetime.now()


def calculate_most_events_in_hour(event_type):
    events = list(collection.find({"type": event_type}).sort("created", 1))
    most_events_in_hour = 0
    most_start_time = None
    most_end_time = None
    for i in range(len(events)):
        start_time = events[i]['created']
        end_time = start_time + timedelta(hours=1)
        events_in_hour = sum(1 for event in events if start_time <= event['created'] < end_time)
        if events_in_hour > most_events_in_hour:
            most_events_in_hour = events_in_hour
            most_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
            most_end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
    return {"most_events_in_hour": most_events_in_hour, "start_time": most_start_time, "end_time": most_end_time}


# PARTNER

totalEvents = collection.count_documents({"type": "PARTNER"})
print("PARTNER | Total Events: " + str(totalEvents))

totalHours = (now - collection.find_one({"type": "PARTNER"}, sort=[("created", 1)])['created']).total_seconds() / 3600
print("PARTNER | Total Hours: " + str(totalHours))

averageEventsPerHour = 0 if totalHours == 0 else totalEvents / totalHours
print("PARTNER | Average Events Per Hour: " + str(averageEventsPerHour))

most_events_in_hour_partner = calculate_most_events_in_hour("PARTNER")
print("PARTNER | Most Events In An Hour: " + str(most_events_in_hour_partner['most_events_in_hour']) + " (from " + str(most_events_in_hour_partner['start_time']) + " to " + str(most_events_in_hour_partner['end_time']) + ")")


# COMMUNITY

totalEvents = collection.count_documents({"type": "COMMUNITY"})
print("COMMUNITY | Total Events: " + str(totalEvents))

totalHours = (now - collection.find_one({"type": "COMMUNITY"}, sort=[("created", 1)])['created']).total_seconds() / 3600
print("COMMUNITY | Total Hours: " + str(totalHours))

averageEventsPerHour = 0 if totalHours == 0 else totalEvents / totalHours
print("COMMUNITY | Average Events Per Hour: " + str(averageEventsPerHour))

most_events_in_hour_community = calculate_most_events_in_hour("COMMUNITY")
print("COMMUNITY | Most Events In An Hour: " + str(most_events_in_hour_community['most_events_in_hour']) + " (from " + str(most_events_in_hour_community['start_time']) + " to " + str(most_events_in_hour_community['end_time']) + ")")
