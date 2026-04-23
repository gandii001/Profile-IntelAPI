"""
File: api/query_parser.py
Natural language query parser for demographic filtering
"""

import re
import pycountry


class NaturalLanguageQueryParser:
    """Parse natural language queries into filter parameters"""
    
    # Pseudo age groups (map to age ranges but NOT stored in DB)
    PSEUDO_GROUPS = ['young', 'youth', 'old', 'older', 'middle-aged', 'mature']
    
    # Real age groups (stored in database)
    REAL_GROUPS = ['child', 'teenager', 'adult', 'senior']
    
    # Age group mappings
    AGE_GROUPS = {
        'child': (0, 12),
        'children': (0, 12),
        'kid': (0, 12),
        'kids': (0, 12),
        'young': (16, 24),
        'youth': (16, 24),
        'teen': (13, 19),
        'teenager': (13, 19),
        'teenagers': (13, 19),
        'adolescent': (13, 19),
        'adolescents': (13, 19),
        'adult': (18, 59),
        'adults': (18, 59),
        'middle-aged': (40, 59),
        'mature': (40, 59),
        'senior': (60, 150),
        'seniors': (60, 150),
        'elderly': (60, 150),
        'old': (60, 150),
        'older': (60, 150),
    }
    
    # Gender keywords
    GENDER_KEYWORDS = {
        'male': 'male',
        'males': 'male',
        'man': 'male',
        'men': 'male',
        'boy': 'male',
        'boys': 'male',
        'guy': 'male',
        'guys': 'male',
        'female': 'female',
        'females': 'female',
        'woman': 'female',
        'women': 'female',
        'girl': 'female',
        'girls': 'female',
        'lady': 'female',
        'ladies': 'female',
    }
    
    def __init__(self, query):
        self.query = query.lower().strip()
        self.filters = {}
        
    def parse(self):
        """
        Parse the query and return (filters_dict, error_message)
        error_message is None if successful
        """
        
        if not self.query:
            return {}, "Unable to interpret query"
        
        try:
            # Extract components
            genders = self._extract_gender()
            age_info = self._extract_age()
            country = self._extract_country()
            
            # Build filters
            if genders:
                # If multiple genders found (e.g., "male and female"), don't filter by gender
                if len(genders) == 1:
                    self.filters['gender'] = genders[0]
            
            if age_info:
                if 'min_age' in age_info:
                    self.filters['min_age'] = age_info['min_age']
                if 'max_age' in age_info:
                    self.filters['max_age'] = age_info['max_age']
                if 'age_group' in age_info:
                    self.filters['age_group'] = age_info['age_group']
            
            if country:
                self.filters['country_id'] = country
            
            # If we couldn't extract anything meaningful, return error
            if not self.filters:
                return {}, "Unable to interpret query"
            
            return self.filters, None
        
        except Exception as e:
            return {}, "Unable to interpret query"
    
    def _extract_gender(self):
        """Extract gender from query"""
        genders = set()
        
        for keyword, gender_value in self.GENDER_KEYWORDS.items():
            if keyword in self.query:
                genders.add(gender_value)
        
        return list(genders)
    
    def _extract_age(self):
        """Extract age/age_group from query"""
        age_info = {}
        
        # Check for explicit age groups first
        for group_keyword, (min_age, max_age) in self.AGE_GROUPS.items():
            if group_keyword in self.query:
                # Only add age_group if it's a REAL database group, not pseudo
                if group_keyword in self.REAL_GROUPS:
                    age_info['age_group'] = group_keyword
                
                # Always add age range
                age_info['min_age'] = min_age
                age_info['max_age'] = max_age
                
                # Special handling for "above", "over", "below", "under"
                # Extract number patterns like "above 30", "over 40"
                above_match = re.search(r'(above|over)\s+(\d+)', self.query)
                if above_match:
                    age_info['min_age'] = int(above_match.group(2))
                
                below_match = re.search(r'(below|under)\s+(\d+)', self.query)
                if below_match:
                    age_info['max_age'] = int(below_match.group(2))
                
                return age_info
        
        # Extract numeric ages with patterns (if no group keyword matched)
        # Pattern: "above X", "over X", "older than X"
        above_match = re.search(r'(above|over|older than)\s+(\d+)', self.query)
        if above_match:
            age_info['min_age'] = int(above_match.group(2))
        
        # Pattern: "below X", "under X", "younger than X"
        below_match = re.search(r'(below|under|younger than)\s+(\d+)', self.query)
        if below_match:
            age_info['max_age'] = int(below_match.group(2))
        
        # Pattern: "between X and Y"
        between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', self.query)
        if between_match:
            age_info['min_age'] = int(between_match.group(1))
            age_info['max_age'] = int(between_match.group(2))
        
        # Pattern: "X years old", "X year old"
        year_match = re.search(r'(\d+)\s+years?\s+old', self.query)
        if year_match and 'min_age' not in age_info and 'max_age' not in age_info:
            age = int(year_match.group(1))
            age_info['min_age'] = age
            age_info['max_age'] = age
        
        return age_info if age_info else {}
    
    def _extract_country(self):
        """Extract country from query using pycountry"""
        
        try:
            # Try to match by full country name first
            for country in pycountry.countries:
                country_name = country.name.lower()
                
                # Exact match for full country name
                if country_name in self.query:
                    return country.alpha_2
                
                # Match first part (handles "United States" when query has "united states")
                country_first_part = country_name.split(',')[0].lower()
                if country_first_part in self.query and len(country_first_part) > 3:
                    return country.alpha_2
        except:
            pass
        
        # Fallback: hardcoded country variations for common misspellings/variations
        country_variations = {
            'nigeria': 'NG',
            'ghana': 'GH',
            'kenya': 'KE',
            'tanzania': 'TZ',
            'uganda': 'UG',
            'sudan': 'SD',
            'egypt': 'EG',
            'south africa': 'ZA',
            'southafrica': 'ZA',
            'cameroon': 'CM',
            'cameroun': 'CM',
            'senegal': 'SN',
            'ivory coast': 'CI',
            'ivorycoast': 'CI',
            'côte d\'ivoire': 'CI',
            'benin': 'BJ',
            'ethiopia': 'ET',
            'angola': 'AO',
            'mozambique': 'MZ',
            'zambia': 'ZM',
            'zimbabwe': 'ZW',
            'malawi': 'MW',
            'rwanda': 'RW',
            'botswana': 'BW',
            'namibia': 'NA',
            'lesotho': 'LS',
            'mauritius': 'MU',
            'madagascar': 'MG',
            'cape verde': 'CV',
            'gambia': 'GM',
            'guinea': 'GN',
            'liberia': 'LR',
            'sierra leone': 'SL',
            'togo': 'TG',
            'niger': 'NE',
            'mali': 'ML',
            'mauritania': 'MR',
            'western sahara': 'EH',
            'united states': 'US',
            'usa': 'US',
            'america': 'US',
            'united kingdom': 'GB',
            'uk': 'GB',
            'england': 'GB',
            'scotland': 'GB',
            'wales': 'GB',
            'france': 'FR',
            'germany': 'DE',
            'italy': 'IT',
            'spain': 'ES',
            'portugal': 'PT',
            'netherlands': 'NL',
            'belgium': 'BE',
            'switzerland': 'CH',
            'austria': 'AT',
            'sweden': 'SE',
            'norway': 'NO',
            'denmark': 'DK',
            'finland': 'FI',
            'poland': 'PL',
            'russia': 'RU',
            'india': 'IN',
            'pakistan': 'PK',
            'bangladesh': 'BD',
            'china': 'CN',
            'japan': 'JP',
            'south korea': 'KR',
            'korea': 'KR',
            'thailand': 'TH',
            'vietnam': 'VN',
            'philippines': 'PH',
            'indonesia': 'ID',
            'malaysia': 'MY',
            'singapore': 'SG',
            'australia': 'AU',
            'new zealand': 'NZ',
            'canada': 'CA',
            'mexico': 'MX',
            'brazil': 'BR',
            'argentina': 'AR',
            'chile': 'CL',
            'colombia': 'CO',
            'peru': 'PE',
            'venezuela': 'VE',
        }
        
        for country_name, code in country_variations.items():
            if country_name in self.query:
                return code
        
        return None