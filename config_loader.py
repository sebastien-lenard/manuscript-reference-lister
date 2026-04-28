import os
from dotenv import load_dotenv

load_dotenv()

# Main output directory
OUTPUT_DIR = os.getenv("OUTPUT_PATH", "output")
# Dedicated test directory
TEST_OUTPUT_DIR = os.getenv("TEST_OUTPUT_PATH", "tests_output")

CROSSREF_EMAIL = os.getenv("CROSSREF_EMAIL", "default@example.com")

MAX_RESULTS = os.getenv("MAX_RESULTS", 6)

CONTEXT_KEYWORDS = os.getenv("CONTEXT_KEYWORDS", "")

# Ensure both directories exist
for d in [OUTPUT_DIR, TEST_OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

API_DELAY = 0.5