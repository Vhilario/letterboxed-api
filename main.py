import requests
import json
import datetime
from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()

# Initialize letter_boxed_data from file if it exists
try:
    with open('letter_boxed_data.json', 'r') as f:
        letter_boxed_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    letter_boxed_data = None

@app.get("/get_letter_boxed_data")
def read_root():
    global letter_boxed_data
    current_timestamp = int(datetime.datetime.now().timestamp())
    
    # Check if we have data and it hasn't expired
    if letter_boxed_data is not None and current_timestamp < letter_boxed_data.get('expiration', 0):
        print(f'returning cached data, for puzzle {letter_boxed_data["printDate"]}')
        return letter_boxed_data
        
    # If we get here, we need new data
    letter_boxed_data = scrape_data("https://www.nytimes.com/puzzles/letter-boxed")
    return letter_boxed_data

def scrape_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the specific div first
    game_div = soup.find('div', id='js-hook-pz-moment__game')
    if not game_div:
        raise ValueError("Could not find game div")
    
    # Find the script tag within that div
    script_element = game_div.find('script', type='text/javascript')
    if not script_element:
        raise ValueError("Could not find script element in game div")
    
    script_content = script_element.string.strip()
    json_string = script_content.replace('window.gameData = ', '').replace(';', '')
    letter_boxed_data = json.loads(json_string)

    # Test the validate_data function with the sample_bad_data.json file
    # with open('sample_bad_data.json', 'r') as f:
    #     temp = json.load(f)
    #     validate_data(temp)

    validate_data(letter_boxed_data)

    with open('letter_boxed_data.json', 'w') as f:
        json.dump(letter_boxed_data, f)
    return letter_boxed_data

def validate_data(letter_boxed_data):
    required_keys = ['ourSolution', 'printDate', 'sides', 'date', 'dictionary']
    for key in required_keys:
        if key not in letter_boxed_data:
            raise ValueError(f"Missing required key: {key}")
    return True
