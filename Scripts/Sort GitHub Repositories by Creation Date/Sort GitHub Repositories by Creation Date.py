import json
import requests


# Get config values
with open("config.json", "r") as file:
    config = json.load(file)
    username = config["username"]
    token = config["token"]
    direction = config["direction"]

# Make GraphQL query to fetch repositories sorted by creation date
repositories = requests.post(
    "https://api.github.com/graphql",
    headers={"Authorization": f"bearer {token}"},
    json={
        "query": f"""query {{ 
            user(login: "{username}") {{ 
                repositories(first: 100, orderBy: {{field: CREATED_AT, direction: {direction}}}) {{ 
                    nodes {{ 
                        createdAt 
                        name 
                    }} 
                }} 
            }} 
        }}"""
    }
).json()["data"]["user"]["repositories"]["nodes"]

# Print repositories sorted by creation date
for repo in repositories:
    print(f"{repo['createdAt']}: {repo['name']}")
