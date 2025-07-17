"""
Electronic Health Record (EHR) Integration for Mental Health Agent
FHIR-compliant integration with major EHR systems.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import httpx
from urllib.parse import urljoin

from ..models.core import UserInput, AgentResponse
from ..monitoring.logging_config import get_logger

logger = get_logger("enterprise.ehr")


class EHRSystem(str, Enum):
    """Supported EHR systems."""
    EPIC = "epic"
    CERNER = "cerner"
    ALLSCRIPTS = "allscripts"
    ATHENAHEALTH = "athenahealth"
    ECLINICALWORKS = "eclinicalworks"
    GENERIC_FHIR = "generic_fhir"


class FHIRVersion(str, Enum):
    """FHIR specification versions."""
    R4 = "4.0.1"
    STU3 = "3.0.2"
    DSTU2 = "1.0.2"


@dataclass
class EHRConfig:
    """EHR system configuration."""
    
    system_type: EHRSystem
    base_url: str
    fhir_version: FHIRVersion
    client_id: str
    client_secret: str
    scope: str
    redirect_uri: str
    tenant_id: Optional[str] = None
    sandbox_mode: bool = True
    timeout: int = 30


@dataclass
class PatientInfo:
    """Patient information from EHR."""
    
    patient_id: str
    mrn: str  # Medical Record Number
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    emergency_contact: Optional[Dict[str, str]] = None
    primary_care_provider: Optional[str] = None
    insurance_info: Optional[Dict[str, str]] = None


@dataclass
class MentalHealthRecord:
    """Mental health record for EHR integration."""
    
    patient_id: str
    encounter_id: str
    session_date: datetime
    session_type: str  # "ai_chat", "crisis_intervention", "assessment"
    duration_minutes: int
    chief_complaint: Optional[str] = None
    assessment: Optional[str] = None
    interventions: List[str] = None
    risk_level: Optional[str] = None  # "low", "moderate", "high", "critical"
    follow_up_needed: bool = False
    provider_notes: Optional[str] = None
    crisis_resources_provided: List[str] = None
    safety_plan_updated: bool = False


class EHRIntegration:
    """EHR integration manager."""
    
    def __init__(self, config: EHRConfig):
        """Initialize EHR integration."""
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=config.timeout)
        self.access_token = None
        self.token_expires_at = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with EHR system using OAuth 2.0.
        
        Returns:
            Authentication success status
        """
        try:
            if self.config.system_type == EHRSystem.EPIC:
                return await self._authenticate_epic()
            elif self.config.system_type == EHRSystem.CERNER:
                return await self._authenticate_cerner()
            else:
                return await self._authenticate_generic_fhir()
                
        except Exception as e:
            logger.error(f"EHR authentication failed: {e}")
            return False
    
    async def get_patient_info(self, patient_id: str) -> Optional[PatientInfo]:
        """
        Get patient information from EHR.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Patient information if found
        """
        try:
            await self._ensure_authenticated()
            
            # FHIR Patient resource endpoint
            url = urljoin(self.config.base_url, f"Patient/{patient_id}")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            }
            
            response = await self.http_client.get(url, headers=headers)
            
            if response.status_code == 200:
                patient_data = response.json()
                return self._parse_patient_fhir(patient_data)
            elif response.status_code == 404:
                logger.warning(f"Patient not found: {patient_id}")
                return None
            else:
                logger.error(f"Failed to get patient info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting patient info: {e}")
            return None
    
    async def create_mental_health_encounter(
        self,
        patient_id: str,
        record: MentalHealthRecord
    ) -> Optional[str]:
        """
        Create mental health encounter in EHR.
        
        Args:
            patient_id: Patient identifier
            record: Mental health record
            
        Returns:
            Encounter ID if successful
        """
        try:
            await self._ensure_authenticated()
            
            # Create FHIR Encounter resource
            encounter_resource = self._create_encounter_fhir(patient_id, record)
            
            url = urljoin(self.config.base_url, "Encounter")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            }
            
            response = await self.http_client.post(
                url,
                headers=headers,
                json=encounter_resource
            )
            
            if response.status_code in [200, 201]:
                encounter_data = response.json()
                encounter_id = encounter_data.get("id")
                
                # Create associated observations and notes
                await self._create_mental_health_observations(patient_id, encounter_id, record)
                
                logger.info(f"Mental health encounter created: {encounter_id}")
                return encounter_id
            else:
                logger.error(f"Failed to create encounter: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating mental health encounter: {e}")
            return None
    
    async def update_safety_plan(
        self,
        patient_id: str,
        safety_plan: Dict[str, Any]
    ) -> bool:
        """
        Update patient safety plan in EHR.
        
        Args:
            patient_id: Patient identifier
            safety_plan: Safety plan information
            
        Returns:
            Update success status
        """
        try:
            await self._ensure_authenticated()
            
            # Create FHIR CarePlan resource for safety plan
            care_plan_resource = self._create_safety_plan_fhir(patient_id, safety_plan)
            
            url = urljoin(self.config.base_url, "CarePlan")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            }
            
            response = await self.http_client.post(
                url,
                headers=headers,
                json=care_plan_resource
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Safety plan updated for patient: {patient_id}")
                return True
            else:
                logger.error(f"Failed to update safety plan: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating safety plan: {e}")
            return False
    
    async def get_mental_health_history(
        self,
        patient_id: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get patient's mental health history from EHR.
        
        Args:
            patient_id: Patient identifier
            days_back: Number of days to look back
            
        Returns:
            List of mental health encounters
        """
        try:
            await self._ensure_authenticated()
            
            # Search for mental health encounters
            since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            
            url = urljoin(self.config.base_url, "Encounter")
            params = {
                "patient": patient_id,
                "class": "AMB",  # Ambulatory
                "type": "mental-health",
                "date": f"ge{since_date}",
                "_sort": "-date"
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json"
            }
            
            response = await self.http_client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                bundle = response.json()
                encounters = []
                
                for entry in bundle.get("entry", []):
                    encounter = entry.get("resource", {})
                    encounters.append(self._parse_encounter_fhir(encounter))
                
                return encounters
            else:
                logger.error(f"Failed to get mental health history: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting mental health history: {e}")
            return []
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at and datetime.utcnow() >= self.token_expires_at):
            await self.authenticate()
    
    async def _authenticate_epic(self) -> bool:
        """Authenticate with Epic EHR system."""
        try:
            # Epic uses OAuth 2.0 with client credentials flow
            token_url = urljoin(self.config.base_url, "oauth2/token")
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope
            }
            
            response = await self.http_client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                logger.info("Epic authentication successful")
                return True
            else:
                logger.error(f"Epic authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Epic authentication error: {e}")
            return False
    
    async def _authenticate_cerner(self) -> bool:
        """Authenticate with Cerner EHR system."""
        try:
            # Cerner uses OAuth 2.0 with client credentials flow
            token_url = urljoin(self.config.base_url, "token")
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope
            }
            
            response = await self.http_client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                logger.info("Cerner authentication successful")
                return True
            else:
                logger.error(f"Cerner authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Cerner authentication error: {e}")
            return False
    
    async def _authenticate_generic_fhir(self) -> bool:
        """Authenticate with generic FHIR server."""
        try:
            # Generic FHIR OAuth 2.0 authentication
            token_url = urljoin(self.config.base_url, "auth/token")
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope
            }
            
            response = await self.http_client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                logger.info("Generic FHIR authentication successful")
                return True
            else:
                logger.error(f"Generic FHIR authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Generic FHIR authentication error: {e}")
            return False
    
    def _parse_patient_fhir(self, patient_data: Dict[str, Any]) -> PatientInfo:
        """Parse FHIR Patient resource."""
        try:
            # Extract basic information
            patient_id = patient_data.get("id")
            
            # Get identifiers (MRN)
            mrn = None
            for identifier in patient_data.get("identifier", []):
                if identifier.get("type", {}).get("coding", [{}])[0].get("code") == "MR":
                    mrn = identifier.get("value")
                    break
            
            # Get name
            name = patient_data.get("name", [{}])[0]
            first_name = " ".join(name.get("given", []))
            last_name = name.get("family", "")
            
            # Get birth date
            birth_date_str = patient_data.get("birthDate")
            birth_date = datetime.fromisoformat(birth_date_str) if birth_date_str else None
            
            # Get gender
            gender = patient_data.get("gender", "unknown")
            
            # Get contact information
            email = None
            phone = None
            for telecom in patient_data.get("telecom", []):
                if telecom.get("system") == "email":
                    email = telecom.get("value")
                elif telecom.get("system") == "phone":
                    phone = telecom.get("value")
            
            # Get address
            address = None
            if patient_data.get("address"):
                addr = patient_data["address"][0]
                address = {
                    "line": " ".join(addr.get("line", [])),
                    "city": addr.get("city"),
                    "state": addr.get("state"),
                    "postal_code": addr.get("postalCode"),
                    "country": addr.get("country")
                }
            
            return PatientInfo(
                patient_id=patient_id,
                mrn=mrn or patient_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=birth_date,
                gender=gender,
                email=email,
                phone=phone,
                address=address
            )
            
        except Exception as e:
            logger.error(f"Error parsing patient FHIR data: {e}")
            raise
    
    def _create_encounter_fhir(
        self,
        patient_id: str,
        record: MentalHealthRecord
    ) -> Dict[str, Any]:
        """Create FHIR Encounter resource."""
        return {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "type": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "185349003",
                    "display": "Mental health consultation"
                }]
            }],
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "period": {
                "start": record.session_date.isoformat(),
                "end": (record.session_date + timedelta(minutes=record.duration_minutes)).isoformat()
            },
            "reasonCode": [{
                "text": record.chief_complaint or "Mental health support session"
            }] if record.chief_complaint else [],
            "serviceProvider": {
                "display": "Mental Health Agent AI System"
            }
        }
    
    def _create_safety_plan_fhir(
        self,
        patient_id: str,
        safety_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create FHIR CarePlan resource for safety plan."""
        return {
            "resourceType": "CarePlan",
            "status": "active",
            "intent": "plan",
            "category": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "734163000",
                    "display": "Care plan"
                }]
            }],
            "title": "Mental Health Safety Plan",
            "description": "AI-generated safety plan for mental health crisis prevention",
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "created": datetime.utcnow().isoformat(),
            "activity": [
                {
                    "detail": {
                        "description": step,
                        "status": "not-started"
                    }
                }
                for step in safety_plan.get("steps", [])
            ]
        }
    
    async def _create_mental_health_observations(
        self,
        patient_id: str,
        encounter_id: str,
        record: MentalHealthRecord
    ):
        """Create FHIR Observation resources for mental health data."""
        try:
            observations = []
            
            # Risk level observation
            if record.risk_level:
                observations.append({
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "survey",
                            "display": "Survey"
                        }]
                    }],
                    "code": {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "225336008",
                            "display": "Suicide risk assessment"
                        }]
                    },
                    "subject": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "encounter": {
                        "reference": f"Encounter/{encounter_id}"
                    },
                    "effectiveDateTime": record.session_date.isoformat(),
                    "valueString": record.risk_level
                })
            
            # Create observations
            for observation in observations:
                url = urljoin(self.config.base_url, "Observation")
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json"
                }
                
                await self.http_client.post(url, headers=headers, json=observation)
                
        except Exception as e:
            logger.error(f"Error creating mental health observations: {e}")
    
    def _parse_encounter_fhir(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Encounter resource."""
        return {
            "encounter_id": encounter_data.get("id"),
            "status": encounter_data.get("status"),
            "type": encounter_data.get("type", [{}])[0].get("coding", [{}])[0].get("display"),
            "start_time": encounter_data.get("period", {}).get("start"),
            "end_time": encounter_data.get("period", {}).get("end"),
            "reason": encounter_data.get("reasonCode", [{}])[0].get("text")
        }


# EHR integration factory
class EHRIntegrationFactory:
    """Factory for creating EHR integrations."""
    
    @staticmethod
    def create_integration(config: EHRConfig) -> EHRIntegration:
        """Create EHR integration instance."""
        return EHRIntegration(config)
    
    @staticmethod
    def get_supported_systems() -> List[str]:
        """Get list of supported EHR systems."""
        return [system.value for system in EHRSystem]
