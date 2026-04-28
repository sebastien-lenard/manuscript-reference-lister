import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WORK_DIR_PATH = os.getenv("WORK_DIR_PATH", "output")
# Main output directory
OUTPUT_DIR_PATH = os.getenv("OUTPUT_DIR_PATH", "output")
# Dedicated test directory
TEST_OUTPUT_DIR_PATH = os.getenv("TEST_OUTPUT_DIR_PATH", "tests_output")

CROSSREF_API_DELAY = os.getenv("CROSSREF_API_DELAY", "0.5")
CROSSREF_API_EMAIL = os.getenv("CROSSREF_EMAIL", "default@example.com")
CROSSREF_API_JOURNALS_URL = os.getenv("CROSSREF_API_JOURNALS_URL", "")
CROSSREF_API_WORKS_URL = os.getenv("CROSSREF_API_WORKS_URL", "")
CROSSREF_API_MAX_RESULTS = os.getenv("CROSSREF_API_MAX_RESULTS", 6)

CONTEXT_KEYWORDS = os.getenv("CONTEXT_KEYWORDS", "")

PARSER_DEFAULT_BLACKLIST = ['Fig', 'Figs', 'Figure', 'Figures', 'Tab', 
                            'Table', 'Eq', 'Plate', 'Section', 'See', 'e.g.', 'i.e.', 
                            'January', 'February', 'March', 'April', 'May', 'June',
                            'July', 'August', 'September', 'October', 'November',
                            'December']

# Ensure directories exist
for d in [WORK_DIR_PATH, OUTPUT_DIR_PATH, TEST_OUTPUT_DIR_PATH]:
    if not Path(d).is_dir():
        os.makedirs(d)