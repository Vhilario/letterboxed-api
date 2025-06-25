import requests
import json

from time import time
from functools import wraps
import logging

import datetime
import itertools
import asyncio
from bs4 import BeautifulSoup
from fastapi import FastAPI
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[letterboxed-api] %(levelname)s: %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('letterboxed.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

def timing(func):
    @wraps(func)
    def wrap(*args, **kw):
        ts = time()
        result = func(*args, **kw)
        te = time()
        logger.info(f'{func.__name__} took: {te-ts} seconds')
        return result
    return wrap

# Initialize letter_boxed_data from file if it exists
try:
    with open('letter_boxed_data.json', 'r') as f:
        letter_boxed_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    letter_boxed_data = None

# Background task to fetch new data when the current data expires
async def schedule_next_fetch():
    global letter_boxed_data
    
    while True:  # Continuous loop instead of recursion
        try:
            if letter_boxed_data is None:
                logger.info('No data available, waiting 60 seconds before retry')
                await asyncio.sleep(60)
                continue
            
            expiration = letter_boxed_data.get('expiration', 0)
            current_time = datetime.now().timestamp()
            
            if expiration > current_time:
                delay = expiration - current_time
                logger.info(f'Scheduling next fetch in {delay} seconds')
                await asyncio.sleep(delay)
            else:
                logger.info('Data expired, fetching immediately')
            
            logger.info('Fetching new data')
            letter_boxed_data = scrape_data("https://www.nytimes.com/puzzles/letter-boxed")
            logger.info('Successfully fetched and saved new data')
            
        except Exception as e:
            logger.error(f'Error in background task: {e}')
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)

#I don't know how FastAPI does this now, apparently the on_event is deprecated, but this is the only way I know how to do it
@app.on_event("startup")
async def startup_event():
    # On every startup, run the read_root function
    logger.info('Startup: getting initial data')
    await read_root()

    # Start the background task when the app starts
    logger.info('Starting background task')
    asyncio.create_task(schedule_next_fetch())

@app.get("/get_letter_boxed_data")
@timing
async def read_root():
    global letter_boxed_data
    current_timestamp = int(datetime.now().timestamp())
    
    # Check if we have data and it hasn't expired
    if letter_boxed_data is not None and current_timestamp < letter_boxed_data.get('expiration', 0):
        logger.info(f'Returning cached data, for puzzle {letter_boxed_data["printDate"]}')
        solve_letter_boxed_data(letter_boxed_data)
        return letter_boxed_data
    
    # If we get here, we need new data immediately
    reason = 'Puzzle has expired' if letter_boxed_data is not None else 'No data found'
    logger.info(f'Returning new data, for reason: {reason}')
    letter_boxed_data = scrape_data("https://www.nytimes.com/puzzles/letter-boxed")
    
    # Schedule the next fetch
    await schedule_next_fetch()
    
    return letter_boxed_data

@timing
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

    validate_data(letter_boxed_data)
    (all_solutions, one_word_solutions, perfect_solutions) = solve_letter_boxed_data(letter_boxed_data)
    letter_boxed_data['allSolutions'] = all_solutions
    letter_boxed_data['oneWordSolutions'] = one_word_solutions
    letter_boxed_data['perfectSolutions'] = perfect_solutions

    with open('letter_boxed_data.json', 'w') as f:
        json.dump(letter_boxed_data, f)
    return letter_boxed_data

@timing
def validate_data(letter_boxed_data):
    required_keys = ['ourSolution', 'printDate', 'sides', 'date', 'dictionary']
    for key in required_keys:
        if key not in letter_boxed_data:
            raise ValueError(f"Missing required key: {key}")
    return True

@timing
def solve_letter_boxed_data(letter_boxed_data):
    words = letter_boxed_data['dictionary']
    letters = set(''.join(letter_boxed_data['sides']))
    all_solutions = []

    # Extremely rare, but possible
    one_word_solutions = []
    # Two word solutions that use all letters, without repeating any letters
    perfect_solutions = []
    # find one word solutions
    for word in words:
        if letters.issubset(set(word)):
            logger.info(f'ALERT: {word} is a one word solution')
            one_word_solutions.append([word])
            all_solutions.append([word])
            if len(word) == 12:
                perfect_solutions.append([word])
            # remove the one word solution from the dictionary, because there will be many trivial solutions
            words.remove(word)

    # find two word solutions
    for pair in itertools.permutations(words, 2):
        # check if the pair is valid solution (last letter of first word is the first letter of the second word)
        if not pair[0][-1] == pair[1][0]:
            continue
            
        solution_letters = set(pair[0] + pair[1])
        
        # check if all letters in the pair are valid letters from the puzzle
        if not solution_letters.issubset(letters):
            continue
            
        # check if the pair uses all required letters
        if not solution_letters.issuperset(letters):
            continue
        
        # check if the pair uses all letters without repeating any letters
        perfect_check = pair[0] + pair[1][1:]
        if len(perfect_check) == len(set(perfect_check)):
            perfect_solutions.append(list(pair))
            
        all_solutions.append(list(pair))
    
    return (all_solutions, one_word_solutions, perfect_solutions)