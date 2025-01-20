import requests
import json
import datetime
import itertools
import asyncio
from bs4 import BeautifulSoup
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

# Initialize letter_boxed_data from file if it exists
try:
    with open('letter_boxed_data.json', 'r') as f:
        letter_boxed_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    letter_boxed_data = None

# Background task to fetch new data when the current data expires
async def schedule_next_fetch():
    global letter_boxed_data
    
    if letter_boxed_data is None:
        return
    
    expiration = letter_boxed_data.get('expiration', 0)
    current_time = datetime.now().timestamp()
    
    if expiration > current_time:
        delay = expiration - current_time
        print(f'Scheduling next fetch in {delay} seconds')
        
        # Wait until expiration then fetch new data
        await asyncio.sleep(delay)
        letter_boxed_data = scrape_data("https://www.nytimes.com/puzzles/letter-boxed")
        
        # Schedule the next fetch
        asyncio.create_task(schedule_next_fetch())

#I don't know how FastAPI does this now, apparently the on_event is deprecated, but this is the only way I know how to do it
@app.on_event("startup")
async def startup_event():
    # Start the background task when the app starts
    asyncio.create_task(schedule_next_fetch())

@app.get("/get_letter_boxed_data")
async def read_root():
    global letter_boxed_data
    current_timestamp = int(datetime.now().timestamp())
    
    # Check if we have data and it hasn't expired
    if letter_boxed_data is not None and current_timestamp < letter_boxed_data.get('expiration', 0):
        print(f'returning cached data, for puzzle {letter_boxed_data["printDate"]}')
        solve_letter_boxed_data(letter_boxed_data)
        return letter_boxed_data
    
    # If we get here, we need new data immediately
    reason = 'puzzle expired' if letter_boxed_data is not None else 'no data found'
    print(f'returning new data, for reason: {reason}')
    letter_boxed_data = scrape_data("https://www.nytimes.com/puzzles/letter-boxed")
    
    # Schedule the next fetch
    await schedule_next_fetch()
    
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
    solutions = solve_letter_boxed_data(letter_boxed_data)
    letter_boxed_data['apiSolutions'] = solutions

    with open('letter_boxed_data.json', 'w') as f:
        json.dump(letter_boxed_data, f)
    return letter_boxed_data

def validate_data(letter_boxed_data):
    required_keys = ['ourSolution', 'printDate', 'sides', 'date', 'dictionary']
    for key in required_keys:
        if key not in letter_boxed_data:
            raise ValueError(f"Missing required key: {key}")
    return True

def solve_letter_boxed_data(letter_boxed_data):
    words = letter_boxed_data['dictionary']
    letters =  set(''.join(letter_boxed_data['sides']))
    sides = letter_boxed_data['sides']
    solutions = []
    for pair in itertools.combinations(words, 2):
        #check if the pair is valid solution (last letter of first word is the first letter of the second word)
        if not pair[0][-1] == pair[1][0]:
            continue
        #check if the pair is valid solution (all letters in the pair are in the letters set)
        solution_letters = set(pair[0] + pair[1])
        if not solution_letters <= letters:
            continue
        #check if the pair is valid solution (all letters in the pair are in the sides set)
        if not solution_letters.issuperset(letters):
            continue
        solutions.append(pair)
    print(f'solutions: {solutions}')
    return solutions


