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


def calculate_most_events_in_hour(channel_id):
    events = list(collection.find({"channel": channel_id}).sort("created", 1))
    most_events_in_hour = 0
    for i in range(len(events)):
        start_time = events[i]['created']
        end_time = start_time + timedelta(hours=1)
        events_in_hour = sum(1 for event in events if start_time <= event['created'] < end_time)
        most_events_in_hour = max(most_events_in_hour, events_in_hour)
    return most_events_in_hour


# PARTNER

totalEvents = collection.count_documents({"channel": 980956946075115570})
print("PARTNER | Total Events: " + str(totalEvents))

totalHours = (now - collection.find_one({"channel": 980956946075115570}, sort=[("created", 1)])['created']).total_seconds() / 3600
print("PARTNER | Total Hours: " + str(totalHours))

averageEventsPerHour = 0 if totalHours == 0 else totalEvents / totalHours
print("PARTNER | Average Events Per Hour: " + str(averageEventsPerHour))

print("PARTNER | Most Events In An Hour: " + str(calculate_most_events_in_hour(980956946075115570)))


# COMMUNITY

totalEvents = collection.count_documents({"channel": 980635360184905810})
print("COMMUNITY | Total Events: " + str(totalEvents))

totalHours = (now - collection.find_one({"channel": 980635360184905810}, sort=[("created", 1)])['created']).total_seconds() / 3600
print("COMMUNITY | Total Hours: " + str(totalHours))

averageEventsPerHour = 0 if totalHours == 0 else totalEvents / totalHours
print("COMMUNITY | Average Events Per Hour: " + str(averageEventsPerHour))

print("COMMUNITY | Most Events In An Hour: " + str(calculate_most_events_in_hour(980635360184905810)))