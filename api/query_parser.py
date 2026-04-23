"""
File: api/query_parser.py
Natural language query parser for demographic filtering
"""

import re
import pycountry


class NaturalLanguageQueryParser:
    """Parse natural language queries into filter parameters"""
    
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
                age_info['age_group'] = group_keyword
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
        
        # Extract numeric ages with patterns
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
        """Extract country from query"""
        
        # Remove common stop words
        cleaned_query = self.query
        stop_words = ['from', 'in', 'of', 'the', 'and', 'or', 'a', 'an']
        for word in stop_words:
            cleaned_query = cleaned_query.replace(word, ' ')
        
        # Try to find country by name
        # Get all country names from pycountry
        try:
            for country in pycountry.countries:
                country_name = country.name.lower()
                
                # Check if country name appears in query
                if country_name in self.query:
                    return country.alpha_2
                
                # Check common variations
                if country_name.split(',')[0] in self.query:  # Handle "country, region"
                    return country.alpha_2
        except:
            pass
        
        # Common country name variations
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
            'senegal': 'SN',
            'ivory coast': 'CI',
            'ivorycoast': 'CI',
            'benin': 'BJ',
            'ethiopia': 'ET',
            'angola': 'AO',
            'mozambique': 'MZ',
            'zambia': 'ZM',
            'zimbabwe': 'ZW',
            'malawi': 'MW',
            'rwanda': 'RW',
            'united states': 'US',
            'usa': 'US',
            'america': 'US',
            'united kingdom': 'GB',
            'uk': 'GB',
            'england': 'GB',
            'france': 'FR',
            'germany': 'DE',
            'italy': 'IT',
            'spain': 'ES',
            'india': 'IN',
            'china': 'CN',
            'japan': 'JP',
            'australia': 'AU',
            'canada': 'CA',
            'mexico': 'MX',
            'brazil': 'BR',
            'argentina': 'AR',
        }
        
        for country_name, code in country_variations.items():
            if country_name in self.query:
                return code
        
        return None