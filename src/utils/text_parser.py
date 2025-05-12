from typing import Dict, Optional, List
import json
from openai import AzureOpenAI
from concurrent.futures import ThreadPoolExecutor
from src.core.custom_logger import CustomLogger
from src.core.config import Config
 
class TextParser:
    """Optimized text parser using EPAM DIAL API with Azure OpenAI."""
 
    def __init__(self, logger: Optional[CustomLogger] = None):

        self.logger = logger or CustomLogger("TextParcer")
        self.client = AzureOpenAI(
            api_version=Config.DIAL_API_VERSION,
            azure_endpoint=Config.DIAL_API_ENDPOINT,
            api_key=Config.DIAL_API_KEY,
        )
        self.model = "gpt-35-turbo"  # or "gpt-4" if available
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of workers as needed
 
    def _call_dial_api(self, text: str, parse_type: str = "resume") -> Optional[str]:
        """Optimized API call to DIAL."""
        try:
            template = {
                "resume": {
                    "system_role": "You are a professional resume parser.",
                    "format": {
                        "personal_info": {"name":"","email":"","phone":"","location":""},
                        "experience": [{"title":"","company":"","period":"","responsibilities":[]}],
                        "education": [{"degree":"","institution":"","period":""}],
                        "skills": {"technical":[],"soft":[]},
                        "certifications": [],
                        "languages": []
                    }
                },
                "job": {
                    "system_role": "You are a professional job description parser.",
                    "format": {
                        "skills": {"technical":[],"soft":[]},
                        "job_title": "",
                        "job_role": "",
                        "location": "",
                        "experience": 0,
                        "qualifications": [],
                        "responsibilities": []
                    }
                }
            }
 
            messages = [
                {
                    "role": "system",
                    "content": f"{template[parse_type]['system_role']} Extract information in the specified JSON format."
                },
                {
                    "role": "user",
                    "content": f"""Extract {parse_type} info as JSON:
                    {json.dumps(template[parse_type]['format'], indent=2)}
 
                    Text to parse: {text}"""
                }
            ]
 
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
           
            return response.choices[0].message.content
 
        except Exception as e:
            self.logger.error(f"Error calling DIAL API: {str(e)}")
            return None
 
    def parse_text(self, text: str, parse_type: str = "resume") -> Optional[Dict]:
        """Parse text using DIAL API."""
        try:
            if not text:
                self.logger.error("Empty text provided")
                return None
 
            response = self._call_dial_api(text, parse_type)
            if not response:
                return None
 
            try:
                # Clean up response to ensure valid JSON
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:-3]
                parsed_info = json.loads(json_str)
                self.logger.info(f"{parse_type.capitalize()} parsed successfully")
                return parsed_info
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {str(e)}")
                return None
               
        except Exception as e:
            self.logger.error(f"Parse error: {str(e)}")
            return None
 
    def parse_batch(self, texts: List[str], parse_type: str = "resume") -> List[Optional[Dict]]:
        """Batch process multiple texts concurrently."""
        return list(self.executor.map(lambda x: self.parse_text(x, parse_type), texts))
    
    def calculate_total_experience(self, parsed_resume: dict) -> float:
        """
        Calculate total experience in years from parsed resume data.
        Returns float value (e.g., 0.5 for 6 months).
        """
        try:
            experiences = parsed_resume.get("experience", [])
            if not experiences:
                return 0.0

            prompt = """Calculate the total years of experience from these work periods:
            {}
            IMPORTANT: Return ONLY a number with up to 2 decimal places (e.g., 5.5, 2.0, or 0.5). 
            For experience less than a year, return decimal (e.g., 0.5 for 6 months).""".format(
                json.dumps(experiences)
            )

            messages = [
                {"role": "system", "content": "You are a calculator that only outputs decimal numbers."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=50
            )

            total_years = round(float(response.choices[0].message.content.strip()), 2)
            self.logger.info(f"Total experience calculated: {total_years} years")
            return total_years

        except Exception as e:
            self.logger.error(f"Error calculating experience: {str(e)}")
            return 0.0
   
def test_text_parser(text: str, parse_type: str = "resume") -> Optional[Dict]:
    """Test function for TextParcer."""
    parser = TextParser()
   
    parsed_info = parser.parse_text(text, parse_type)
   
    if parsed_info:
        parser.logger.info(f"{parse_type.capitalize()} parsed successfully")
        return parsed_info
    else:
        parser.logger.error(f"Failed to parse {parse_type}")
        return None