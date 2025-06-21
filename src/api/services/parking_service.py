import httpx
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ParkingService:
    """Service for NYC parking meter data and violation lookup"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.nyc_parking_api_url = "https://data.cityofnewyork.us/resource/693u-uax6.json"
        self.street_name_dict_url = "https://catalog.data.gov/dataset/street-name-dictionary/resource/7ee42120-8d02-42a2-8cab-76653375cd5b"
        
    async def get_parking_info_by_zone(self, zone_number: str) -> Dict[str, Any]:
        """
        Get parking meter information by zone number (pay_by_cell_number)
        
        Args:
            zone_number: The zone/pay-by-cell number from the parking sign
            
        Returns:
            Parking meter information including location and hours
        """
        try:
            params = {"pay_by_cell_number": zone_number}
            response = await self.client.get(self.nyc_parking_api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return {
                    "success": False,
                    "error": f"No parking meter found for zone number: {zone_number}",
                    "zone_number": zone_number
                }
            
            # Return the first result (most relevant)
            meter_info = data[0]
            
            return {
                "success": True,
                "zone_number": zone_number,
                "meter_info": {
                    "meter_number": meter_info.get("meter_number"),
                    "status": meter_info.get("status"),
                    "meter_hours": meter_info.get("meter_hours"),
                    "facility": meter_info.get("facility"),
                    "borough": meter_info.get("borough"),
                    "on_street": meter_info.get("on_street"),
                    "side_of_street": meter_info.get("side_of_street"),
                    "from_street": meter_info.get("from_street"),
                    "to_street": meter_info.get("to_street"),
                    "latitude": meter_info.get("lat"),
                    "longitude": meter_info.get("long"),
                    "location": meter_info.get("location")
                },
                "all_meters": data,  # Include all meters for this zone
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch parking data: {str(e)}",
                "zone_number": zone_number,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_parking_info_by_street(self, street_name: str) -> Dict[str, Any]:
        """
        Get parking meter information by street name
        
        Args:
            street_name: The street name to search for
            
        Returns:
            Parking meter information for the street
        """
        try:
            # Clean and normalize street name
            normalized_street = self._normalize_street_name(street_name)
            
            params = {"on_street": normalized_street}
            response = await self.client.get(self.nyc_parking_api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return {
                    "success": False,
                    "error": f"No parking meters found for street: {street_name}",
                    "street_name": street_name
                }
            
            return {
                "success": True,
                "street_name": street_name,
                "normalized_street": normalized_street,
                "meters": data,
                "meter_count": len(data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch parking data: {str(e)}",
                "street_name": street_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_violation_statistics(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get parking violation statistics for a location
        This is a placeholder for the violation lookup functionality
        
        Args:
            location_data: Location information from parking meter lookup
            
        Returns:
            Violation statistics and information
        """
        try:
            # For now, return mock violation data
            # In production, this would query the NYC parking violations dataset
            
            street_name = location_data.get("on_street", "Unknown Street")
            borough = location_data.get("borough", "Unknown Borough")
            
            # Mock violation statistics
            violation_stats = {
                "total_violations": 150,
                "violations_last_30_days": 12,
                "violations_last_7_days": 3,
                "common_violation_types": [
                    {"type": "Expired Meter", "count": 45, "percentage": 30},
                    {"type": "No Parking Zone", "count": 32, "percentage": 21},
                    {"type": "Double Parking", "count": 28, "percentage": 19},
                    {"type": "Blocking Driveway", "count": 25, "percentage": 17},
                    {"type": "Fire Hydrant", "count": 20, "percentage": 13}
                ],
                "average_fine": 115.50,
                "total_fines": 17325.00,
                "enforcement_hours": "Mon-Fri 7AM-7PM, Sat 7AM-7PM",
                "risk_level": "Medium"  # Low, Medium, High
            }
            
            return {
                "success": True,
                "location": {
                    "street_name": street_name,
                    "borough": borough,
                    "coordinates": location_data.get("location")
                },
                "violation_statistics": violation_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch violation statistics: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _normalize_street_name(self, street_name: str) -> str:
        """
        Normalize street name for API queries
        Convert common variations to standard NYC format
        """
        if not street_name:
            return ""
        
        # Convert to uppercase and trim whitespace
        normalized = street_name.upper().strip()
        
        # Only do minimal normalization - don't replace existing full words
        # This prevents corruption of already correct street names
        replacements = {
            "ST.": "STREET",
            "AVE.": "AVENUE",
            "BLVD.": "BOULEVARD",
            "RD.": "ROAD",
            "DR.": "DRIVE",
            "PL.": "PLACE"
        }
        
        # Apply only abbreviation replacements
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def extract_zone_number_from_text(self, text: str) -> Optional[str]:
        """
        Extract zone number from OCR text
        
        Args:
            text: OCR text from parking sign
            
        Returns:
            Zone number if found, None otherwise
        """
        if not text:
            return None
        
        # Look for patterns like "Zone 123456" or "Pay by Cell 123456"
        patterns = [
            r"zone\s*#?\s*(\d+)",
            r"pay\s*by\s*cell\s*#?\s*(\d+)",
            r"zone\s*(\d+)",
            r"(\d{5,6})",  # 5-6 digit numbers (common zone number length)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_street_name_from_text(self, text: str) -> Optional[str]:
        """
        Extract street name from OCR text
        
        Args:
            text: OCR text from parking sign
            
        Returns:
            Street name if found, None otherwise
        """
        if not text:
            return None
        
        # Look for street name patterns
        # This is a simplified version - you might want to use NLP or more sophisticated parsing
        street_patterns = [
            r"(\w+\s+(?:STREET|ST|AVENUE|AVE|BOULEVARD|BLVD|ROAD|RD|DRIVE|DR|PLACE|PL))",
            r"(\d+\s+\w+\s+(?:STREET|ST|AVENUE|AVE|BOULEVARD|BLVD|ROAD|RD|DRIVE|DR|PLACE|PL))",
        ]
        
        for pattern in street_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def analyze_parking_sign(self, ocr_text: str) -> Dict[str, Any]:
        """
        Analyze OCR text from parking sign and get parking information
        
        Args:
            ocr_text: Text extracted from parking sign image
            
        Returns:
            Comprehensive parking analysis
        """
        try:
            # Extract zone number and street name
            zone_number = self.extract_zone_number_from_text(ocr_text)
            street_name = self.extract_street_name_from_text(ocr_text)
            
            result = {
                "success": True,
                "ocr_text": ocr_text,
                "extracted_data": {
                    "zone_number": zone_number,
                    "street_name": street_name
                },
                "parking_info": None,
                "violation_stats": None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Get parking information by zone number (preferred)
            if zone_number:
                parking_info = await self.get_parking_info_by_zone(zone_number)
                result["parking_info"] = parking_info
                
                # Get violation statistics if parking info is available
                if parking_info.get("success") and parking_info.get("meter_info"):
                    violation_stats = await self.get_violation_statistics(parking_info["meter_info"])
                    result["violation_stats"] = violation_stats
            
            # Fallback to street name if no zone number or zone lookup failed
            elif street_name and (not result["parking_info"] or not result["parking_info"].get("success")):
                parking_info = await self.get_parking_info_by_street(street_name)
                result["parking_info"] = parking_info
                
                # Get violation statistics for the first meter found
                if parking_info.get("success") and parking_info.get("meters"):
                    first_meter = parking_info["meters"][0]
                    violation_stats = await self.get_violation_statistics(first_meter)
                    result["violation_stats"] = violation_stats
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze parking sign: {str(e)}",
                "ocr_text": ocr_text,
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_violation_count_by_street(self, street_name: str) -> Dict[str, Any]:
        """
        Get parking violation count for a street name using NYC Open Data API
        
        Note: This dataset contains historical violation data from 2023.
        It is not real-time current data.
        
        Args:
            street_name: The street name to search for
            
        Returns:
            Violation count and metadata
        """
        try:
            # Normalize street name for violations API
            normalized_street = self._normalize_for_violations(street_name)
            
            url = "https://data.cityofnewyork.us/resource/pvqr-7yc4.json"
            params = {
                "$select": "count(*)",
                "street_name": normalized_street
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0 and "count" in data[0]:
                violation_count = int(data[0]["count"])
                return {
                    "success": True,
                    "street_name": street_name,
                    "normalized_street": normalized_street,
                    "violation_count": violation_count,
                    "data_freshness": "Historical data from 2023 (not real-time)",
                    "data_source": "NYC Open Data - Parking Violations Dataset",
                    "dataset_url": "https://data.cityofnewyork.us/City-Government/Parking-Violations-Issued-Fiscal-Year-2024/pvqr-7yc4",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": True,
                    "street_name": street_name,
                    "normalized_street": normalized_street,
                    "violation_count": 0,
                    "data_freshness": "Historical data from 2023 (not real-time)",
                    "data_source": "NYC Open Data - Parking Violations Dataset",
                    "dataset_url": "https://data.cityofnewyork.us/City-Government/Parking-Violations-Issued-Fiscal-Year-2024/pvqr-7yc4",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch violation count: {str(e)}",
                "street_name": street_name,
                "data_freshness": "Historical data from 2023 (not real-time)",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_violations_by_zone(self, zone_number: str) -> Dict[str, Any]:
        """
        Get parking violations count by zone number (pay-by-cell number)
        
        This method:
        1. Gets the street address from the zone number
        2. Uses that address to get the violation count
        
        Args:
            zone_number: The pay-by-cell number
            
        Returns:
            Complete analysis with zone info, address, and violation count
        """
        try:
            # Step 1: Get parking info by zone number
            zone_info = await self.get_parking_info_by_zone(zone_number)
            
            if not zone_info.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get parking info for zone {zone_number}",
                    "zone_number": zone_number,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract street name from zone info
            meter_info = zone_info.get("meter_info", {})
            street_name = meter_info.get("on_street")
            
            if not street_name:
                return {
                    "success": False,
                    "error": f"No street name found for zone {zone_number}",
                    "zone_number": zone_number,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Get violation count for the street
            violation_info = await self.get_violation_count_by_street(street_name)
            
            # Combine the results
            return {
                "success": True,
                "zone_number": zone_number,
                "parking_info": zone_info,
                "street_name": street_name,
                "violation_info": violation_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get violations by zone: {str(e)}",
                "zone_number": zone_number,
                "timestamp": datetime.now().isoformat()
            }
    
    def _normalize_for_violations(self, street_name: str) -> str:
        """
        Normalize street name specifically for the violations API
        The violations API uses ALL CAPS and specific abbreviations
        """
        if not street_name:
            return ""
        
        # Convert to uppercase and trim whitespace
        normalized = street_name.upper().strip()
        
        # Replace full words with standard abbreviations used in violations dataset
        replacements = {
            "STREET": "ST",
            "AVENUE": "AVE", 
            "BOULEVARD": "BLVD",
            "PLACE": "PL",
            "ROAD": "RD",
            "DRIVE": "DR",
            "LANE": "LN",
            "TERRACE": "TER",
            "COURT": "CT",
            "WAY": "WAY",
            "PARKWAY": "PKWY",
            "EXPRESSWAY": "EXPY"
        }
        
        # Apply replacements
        for long, short in replacements.items():
            normalized = normalized.replace(long, short)
        
        # Remove periods
        normalized = normalized.replace(".", "")
        
        return normalized
    
    async def get_violation_count_by_zone(self, zone_number: str) -> Dict[str, Any]:
        """
        Get just the violation count for a zone number (pay-by-cell number)
        
        This method:
        1. Gets the street address from the zone number
        2. Uses that address to get the violation count
        3. Returns a simplified response with just the count
        
        Args:
            zone_number: The pay-by-cell number
            
        Returns:
            Simplified response with zone number, street name, and violation count
        """
        try:
            # Step 1: Get parking info by zone number
            zone_info = await self.get_parking_info_by_zone(zone_number)
            
            if not zone_info.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get parking info for zone {zone_number}",
                    "zone_number": zone_number,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract street name from zone info
            meter_info = zone_info.get("meter_info", {})
            street_name = meter_info.get("on_street")
            
            if not street_name:
                return {
                    "success": False,
                    "error": f"No street name found for zone {zone_number}",
                    "zone_number": zone_number,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Get violation count for the street
            violation_info = await self.get_violation_count_by_street(street_name)
            
            if not violation_info.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to get violation count: {violation_info.get('error')}",
                    "zone_number": zone_number,
                    "street_name": street_name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Return simplified response with just the count
            return {
                "success": True,
                "zone_number": zone_number,
                "street_name": street_name,
                "violation_count": violation_info.get("violation_count", 0),
                "data_freshness": violation_info.get("data_freshness"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get violation count by zone: {str(e)}",
                "zone_number": zone_number,
                "timestamp": datetime.now().isoformat()
            } 