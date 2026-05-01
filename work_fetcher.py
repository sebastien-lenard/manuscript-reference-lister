from unidecode import unidecode
from requests_wrapper import RequestsWrapper
from work import Work
from config_loader import CROSSREF_API_DELAY, CROSSREF_API_EMAIL, CROSSREF_API_TIMEOUT
from config_loader import CROSSREF_API_WORKS_URL
from config_loader import CROSSREF_API_MAX_RESULTS, CROSSREF_API_MAX_RETRY
from config_loader import DOI_API_URL

class WorkFetcher:
    """
    Handles API calls to Crossref about article references
    with multi-result support.
    """
    def __init__(self):
        self.email = CROSSREF_API_EMAIL
        self.headers = {'User-Agent': f'ManuscriptRefLister/1.0 (mailto:{self.email})'}
        self.base_url = CROSSREF_API_WORKS_URL
        self.doi_url = DOI_API_URL
        self.max_results = CROSSREF_API_MAX_RESULTS
        self.requests_wrapper = RequestsWrapper(CROSSREF_API_EMAIL,
                                                timeout=CROSSREF_API_TIMEOUT,
                                                max_retries=CROSSREF_API_MAX_RETRY,
                                                delay=CROSSREF_API_DELAY)

    def fetch_dois_for_this_info(self, author: str, year: str, issn: str | None = None,
                         keywords: str = "", max_results: int | None = None
                         ) -> list[Work]:
        """
        Searches for references and returns a list of potential matches.
        year: str (1600-2099), with possible suffix (a, b, etc.).
        issn: valid issn of a journal. Without it, crossref will have troubles
            retrieving relevant candidates.
        keywords: either a reference or some specific words of the title. Generic
            keywords not in the title (e.g. geosciences) will dilute crossref output.
        Warning: these remarks are because the project uses the crossref rest api, which
            is mostly based on article metadata, and doesn't work like google scholar,
            which is based more on content.
        """
        if not issn:
            raise ValueError("issn is an obligatory argument (valid issn of a journal)")
        year_int = int(''.join(filter(str.isdigit, year)))
        if year_int < 1600 or year_int > 2099:
            raise ValueError(f"year {year_int} must be in the 1600-2099 range")
        max_results = int(max_results) if max_results else self.max_results


        # Clean author string and determine the expected number of authors
        # Logic: 
        # 1. "A et al." -> Many authors (no upper limit check)
        # 2. "A and B" or "A & B" -> Exactly 2 authors
        # 3. "A" -> Exactly 1 author
        is_et_al = " et al." in author
        raw_authors = author.split(" et al.")[0].replace(' et ', ' and ').split(" and ")
        expected_count = len(raw_authors) if not is_et_al else None

        params = {
            'query': f"{author} {keywords}",
            'rows': max_results,
            'filter': f'from-pub-date:{year_int},until-pub-date:{year_int},issn:{issn}'
        }

        response = self.requests_wrapper.get(
            self.base_url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()

        items = data['message'].get('items', [])
        candidates = []

        for item in items:
            if not self._validate_first_author(item, raw_authors, expected_count):
                continue
            doi = item.get('DOI')
            if doi:
                candidates.append({
                    'req_author': author,
                    'req_year': year,
                    'req_issn': issn,
                    'req_keywords': keywords,
                    'reference': "",
                    'style': "",
                    'doi': self.doi_url.replace("{doi}", str(doi)),
                    'type': item.get('type', 'unknown')
                })
        return candidates
    
    def _normalize_string(self, text: str) -> str:
        """
        Transliterates any unicode string to its closest ASCII representation in lowercase.
        Example: 'Lénárd' becomes 'lenard', 'Łukasiewicz' becomes 'lukasiewicz'.
        Warning: ü becomes u and not ue (as sometimes found in bibliographies)
        """
        if not text:
            return ""
        return unidecode(text).lower().strip()
    
    def _validate_first_author(self, item: dict, expected_authors: list[str], expected_count: int | None = None) -> bool:
        """
        Validates the authors based on the expected list and count.
        Validates if the first author of the Crossref item matches the expected author.
        Warning: strict comparison, case insensitive. If name slightly differs (e.g.
        VanDijk vs Van Dijk, comparison returns False)
        
        Args:
            item: The work item dictionary from Crossref.
            expected_author: The surname/name of the author to match.
            
        Returns:
            bool: True if a match is found, False otherwise.
        """
        authors = item.get('author', [])
        if not authors:
            return False
        
        # 1. Strict count validation if not an "et al." citation
        if expected_count is not None and len(authors) != expected_count:
            return False
        
        norm_expected = [self._normalize_string(a) for a in expected_authors]


        # 2. Validate the primary (first) author.
        # Fallback to the first element in the list if 'sequence' key is missing.
        first_author_obj = next((a for a in authors if a.get('sequence') == 'first'), authors[0])
        norm_first_family = self._normalize_string(first_author_obj.get('family', first_author_obj.get('name', '')))
        
        if norm_expected[0] != norm_first_family:
            # Fallback check on given name
            norm_first_given = self._normalize_string(first_author_obj.get('given', ''))
            if norm_expected[0] != norm_first_given:
                return False
        
        # 3. Validate second author if exactly two are expected
        if expected_count == 2:
            # The second author is the one that is NOT the first_author_obj
            second_author_obj = [a for a in authors if a != first_author_obj][0]
            norm_second_family = self._normalize_string(second_author_obj.get('family', second_author_obj.get('name', '')))
            if norm_expected[1] != norm_second_family:
                return False

        return True

