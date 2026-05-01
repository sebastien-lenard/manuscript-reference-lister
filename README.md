## Installation
This project uses **"uv"** by [https://astral.sh/](https://astral.sh/), a Python package and project manager.
### 1. Install uv
Install uv on your system using the official standalone installer:

Windows
```
powershell -c "irm https://astral.sh | iex"
```

macOS & Linux
```
curl -LsSf https://astral.sh | sh
```

### 2. Setup the Project
Once uv is installed, you can set up the entire environment (including the correct Python version and all dependencies) with a single command:

Clone the repository
```
git clone [https://github.com/sebastien-lenard/manuscript-reference-lister](https://github.com/sebastien-lenard/manuscript-reference-lister)
cd manuscript-reference-lister
```
Sync the environment
```
uv sync
```

### 3. Usage
To run your scripts or tests within the virtual environment, prefix your commands with uv run:

Run the main script
```
uv run python main.py
```

Run tests
```
uv run pytest
```

### 4. Configuration
The application uses environment variables for path management and API settings.

Copy the template file:

Windows
```
copy .env.example .env
```

macOS & Linux
```
cp .env.example .env
```

2. Edit the .env file:
Open the .env file in your editor and update the following:
* Paths: Update WORK_DIR_PATH and OUTPUT_DIR_PATH to point to your local folders.
* Crossref API: Ensure CROSSREF_API_EMAIL is set to your valid email. Crossref requests this so they can contact you if there are issues, which places your requests in their "Polite Pool" (better reliability).

[!IMPORTANT]
Never commit your .env file to version control. It is already included in the .gitignore.
