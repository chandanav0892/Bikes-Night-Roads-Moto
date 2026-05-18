from flask import Flask, render_template
from dotenv import load_dotenv
import os
import re
import requests

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_NINJAS_KEY")
API_URL = "https://api.api-ninjas.com/v1/motorcycles"

BIKES_MAKE = ["BMW","KTM","Aprilia"]

def get_exact_weight(raw_weight):
    if not raw_weight:
        return 0

    raw_weight = str(raw_weight).lower()

    # First check for pounds
    pounds = re.search(r"(\d+\.?\d*)\s*pounds", raw_weight)

    if pounds:
        return float(pounds.group(1))

    # If pounds is not available, check for kg
    kg = re.search(r"(\d+\.?\d*)\s*kg", raw_weight)

    if kg:
        return float(kg.group(1)) * 2.20462

    return 0

def get_bike_details(make):
    if not API_KEY:
        return [],"No API Key Available in .env file"
    
    headers = {
        'X-Api-Key': API_KEY
    }

    params = {
        "make": make
    }

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return [], f"API error for {make}: {response.status_code}"

        data = response.json()

        bikes = []
        for item in data:
            weight = {
                item.get("dry_weight") or
                item.get("total_weight") or
                item.get("weight")
            }
            exact_weight = get_exact_weight(weight)

            if exact_weight == 0:
                continue

            bike = {
                "make": item.get("make"),
                "model": item.get("model"),
                "engine": item.get("engine"),
                "weight": f"{exact_weight} pounds",
                "exact_weight": exact_weight
            }

            bikes.append(bike)

            if len(bikes) == 5:
                break

        return bikes, None   

    except requests.exceptions.RequestException as error:
        return [], f"Request failed to fetch details: {error}"
    
def get_all_bikes():
    all_bikes = []
    errors = []

    for make in BIKES_MAKE:
        bikes, error = get_bike_details(make)

        if error:
            errors.append(f"{make}:{error}")

        all_bikes.extend(bikes)

    all_bikes.sort(key=lambda bike: bike["exact_weight"])
    return all_bikes, errors

@app.route("/")
def home():
    bikes, errors = get_all_bikes()
    return render_template(
        "index.html",
        bikes = bikes,
        errors = errors
        )

if __name__ == "__main__":
    app.run(debug=True)