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

