# Implement mini chatbot

This project fetches support articles, processes them, and uploads them to a vector store and DigitalOcean Spaces Object Storage.

## Setup

1. **Clone the repository:**
   ```sh
   git clone git@github.com:khangnl24112002/my-takehome-test.git
   cd my-takehome-test
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.sample` to `.env` and fill in your credentials:
     ```sh
     cp .env.sample .env
     ```
   - Required variables:
     - `VECTOR_STORE_ID`
     - `SPACES_BUCKET`, `SPACES_KEY`, `SPACES_SECRET`, `SPACES_REGION`
     - `OPENAI_API_KEY`
     - (Optional) `MAX_ARTICLES` to limit articles fetched

## How to Run Locally

```sh
python main.py
```

## Daily Job Logs

https://my-test-space-obj-storage.sgp1.cdn.digitaloceanspaces.com/last_run.json

## Playground Answer Screenshot

![Alt text](https://my-test-space-obj-storage.sgp1.cdn.digitaloceanspaces.com/Screenshot%202025-09-20%20at%2015.02.09.png)

---
For questions, open an issue or contact the maintainer.
