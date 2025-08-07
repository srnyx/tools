import json
import requests

# Get config values
with open("config.json", "r") as file:
    config = json.load(file)
    token = config["token"]
    website = config["website"]

headers = {"Authorization": f"Basic {token}"}

# Get groups (make request to first endpoint to get service IDs)
url_groups = f"https://app.crisp.chat/api/v1/website/{website}/status/services/1"
response_groups = requests.get(url_groups, headers=headers)
if response_groups.status_code >= 400:
    print(f"Failed to fetch groups: {response_groups.status_code} - {response_groups.text}")
    exit(1)
groups = response_groups.json().get("data", [])
print(f"Found {len(groups)} groups to process")
if len(groups) == 0:
    exit(0)

# Update each node in each group
for group in groups:
    group_id = group["service_id"]
    group_name = group["name"]

    has_page = True
    i = 1
    while has_page:
        url_nodes = f"https://app.crisp.chat/api/v1/website/{website}/status/service/{group_id}/nodes/{i}"
        response_nodes = requests.get(url_nodes, headers=headers)
        if response_nodes.status_code >= 400:
            print(f"Failed to fetch nodes for group {group_name}: {response_nodes.status_code} - {response_nodes.text}")
            has_page = False
            continue

        nodes = response_nodes.json().get("data", [])
        if len(nodes) == 0:
            has_page = False
            continue
        print(f"Processing group {group_name} with {len(nodes)} nodes")

        # Update each node
        for node in nodes:
            node_label = node["label"]

            # Check if already updated
            healthy_above = node["http"]["status"]["healthy_above"]
            if healthy_above is None or healthy_above == 400:
                print(f"Node {node_label} in group {group_name} is already updated. Skipping!")
                continue

            print(f"Updating node {node_label} in group {group_name}: {node}")

            node_id = node["node_id"]
            url_update = f"https://app.crisp.chat/api/v1/website/{website}/status/service/{group_id}/node/{node_id}"
            payload = {"label": node_label, "order": node["order"], "replicas": node["replicas"],
                       "http": {"status": {"healthy_above": 400, "healthy_below": 410}}}
            response_update = requests.put(url_update, headers=headers, json=payload)
            if response_update.status_code >= 400:
                print(f"Failed to update node {node_label} in group {group_name}: {response_update.status_code} - {response_update.text}")
                continue

            print(f"Successfully updated node {node_label} in group {group_name}")

            # Update replica
            url_replicas = f"https://app.crisp.chat/api/v1/website/{website}/status/service/{group_id}/node/{node_id}/replicas"
            response_replicas = requests.delete(url_replicas, headers=headers)
            if response_replicas.status_code >= 400:
                print(f"Failed to delete replicas for node {node_label} in group {group_name}: {response_replicas.status_code} - {response_replicas.text}")
                continue

            print(f"Successfully deleted replicas for node {node_label} in group {group_name}")

        i += 1
