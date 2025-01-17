import requests
import json
from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()

@app.get("/get_letter_boxed_data")
def read_root():
    return scrape_data("https://www.nytimes.com/puzzles/letter-boxed")

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
    game_data = json.loads(json_string)
    return game_data
