from flask import Flask, jsonify, request
from flask_cors import CORS  # Import the CORS module
import requests
import threading
import time
from datetime import datetime
import pytz  # Import the pytz library

app = Flask(__name__)
CORS(app) 

# Global array to store total_rank from each API response
total_ranks_simplified = []

def calculate_minutes_from_reference_time(finish_time_ist):
    reference_time_08 = finish_time_ist.replace(hour=8, minute=0, second=0, microsecond=0)
    reference_time_20 = finish_time_ist.replace(hour=20, minute=0, second=0, microsecond=0)

    if finish_time_ist.hour >= 20:
        # If finish_time is on or after 20:00, calculate minutes from 20:00
        minutes_elapsed = (finish_time_ist - reference_time_20).seconds // 60
    else:
        # If finish_time is before 20:00, calculate minutes from 08:00
        minutes_elapsed = (finish_time_ist - reference_time_08).seconds // 60

    return minutes_elapsed

def fetch_data(pagination, contest):
    url = f'https://leetcode.com/contest/api/ranking/{contest}/?pagination={pagination}&region=global'
    response = requests.get(url)

    if response.status_code == 200:
        try:
            json_data = response.json()
            total_ranks = json_data.get('total_rank', [])

            for entry in total_ranks:
                # Extracting required information
                username = entry.get('username')
                rank = entry.get('rank')
                score = entry.get('score')
                finish_time_seconds = entry.get('finish_time')

                # Convert finish_time to UTC
                finish_time_utc = datetime.utcfromtimestamp(finish_time_seconds)

                # Define the source and target time zones
                source_timezone = pytz.utc
                target_timezone = pytz.timezone('Asia/Kolkata')  # Indian Standard Time (IST)

                # Convert finish_time to Indian Standard Time
                finish_time_ist = finish_time_utc.replace(tzinfo=source_timezone).astimezone(target_timezone)

                # Extract hour and minute part from finish_time
                finish_time_formatted = finish_time_ist.strftime('%H:%M')

                # Calculate minutes elapsed from 08:00 or 20:00
                minutes_elapsed = calculate_minutes_from_reference_time(finish_time_ist)

                # Storing the extracted information in a simplified format
                simplified_entry = {
                    'username': username,
                    'rank': rank,
                    'score': score,
                    'finish_time': finish_time_formatted,
                    'minutes_elapsed': minutes_elapsed
                }

                # Append the simplified entry to the global array
                total_ranks_simplified.append(simplified_entry)
        except Exception as e:
            print(f"Error parsing response for pagination {pagination} in contest {contest}: {e}")
    else:
        print(f"Error fetching data for pagination {pagination} in contest {contest}. Status code: {response.status_code}")

@app.route('/')
def index():
    # Get the 'contest' parameter from the query string
    contest = request.args.get('contest', 'weekly-contest-379')
    
    num_pages = 200

    start_time = time.time()  # Record start time
    
    threads = []
    for pagination in range(1, num_pages + 1):
        thread = threading.Thread(target=fetch_data, args=(pagination, contest))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # total_ranks_simplified.sort(key=lambda x: x['rank'])

    end_time = time.time()  # Record end time
    total_time = end_time - start_time
    print(f"Total time taken: {total_time} seconds")

    return jsonify({'total_ranks_simplified': total_ranks_simplified})

if __name__ == '__main__':
    app.run(debug=True)
