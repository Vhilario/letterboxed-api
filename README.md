# Letter Boxed API

This is a simple API for the Letter Boxed puzzle from the New York Times. It's built with FastAPI and uses a JSON file to store the data.

## Usage

To run the API, you need to have FastAPI, Uvicorn, requests, and beautifulsoup4 installed. You can easily install these packages using pip, and the requirements.txt file.

```bash
pip install -r requirements.txt
```

To run the API, you can use the following command:
```bash
uvicorn main:app --reload
```

This will start the API and you can access the data at: ```http://127.0.0.1:8000/get_letter_boxed_data```

### Data

The data is returned to the client in JSON format, and locally stored in the `letter_boxed_data.json` file. The data is also validated and solved by the API. The `apiSolutions` key is the list of two-word solutions returned by the API, while everything else is data scraped from the NYT website.

#### Solution Types

| Solution Type | Description |
|--------------|-------------|
| allSolutions | All valid solutions.|
| oneWordSolutions | Extremely rare solutions where a single word uses all required letters from the puzzle. These are removed from the dictionary to prevent trivial two-word solutions. |
| perfectSolutions | Any (one or two-word) solutions that use all required letters exactly once (no repeated letters). These unnecessary for winning, but some people take pride in finding them. |

For example, if the puzzle letters are ["GIY", "XHA", "ERC", "LOC"]:
- A oneWordSolution might be: ["LEXICOGRAPHY"]



