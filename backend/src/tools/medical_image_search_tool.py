"""
Medical Image Search Tool with approved medical image sources and relevance scoring.
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import aiohttp
import asyncio

from ..models.core import MedicalImage

logger = logging.getLogger(__name__)


class MedicalImageSource:
    """Represents a medical image source with metadata."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        trust_score: float = 1.0,
        license_type: str = "unknown",
        rate_limit: int = 100
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.trust_score = trust_score
        self.license_type = license_type
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_reset = datetime.utcnow()


class ApprovedImageSources:
    """Registry of approved medical image sources."""
    
    def __init__(self):
        """Initialize approved image sources."""
        self.sources = {
            "nih_nlm": MedicalImageSource(
                name="NIH National Library of Medicine",
                base_url="https://api.nlm.nih.gov/medlineplus/",
                trust_score=1.0,
                license_type="public_domain",
                rate_limit=100
            ),
            "who_images": MedicalImageSource(
                name="World Health Organization",
                base_url="https://www.who.int/images/",
                trust_score=0.95,
                license_type="cc_by_nc_sa",
                rate_limit=50
            ),
            "cdc_images": MedicalImageSource(
                name="Centers for Disease Control",
                base_url="https://www.cdc.gov/media/",
                trust_score=0.95,
                license_type="public_domain",
                rate_limit=75
            ),
            "mayo_clinic": MedicalImageSource(
                name="Mayo Clinic",
                base_url="https://www.mayoclinic.org/",
                trust_score=0.9,
                license_type="educational_use",
                rate_limit=25
            ),
            "medlineplus": MedicalImageSource(
                name="MedlinePlus",
                base_url="https://medlineplus.gov/",
                trust_score=0.9,
                license_type="public_domain",
                rate_limit=50
            )
        }
    
    def get_source(self, source_name: str) -> Optional[MedicalImageSource]:
        """Get image source by name."""
        return self.sources.get(source_name)
    
    def get_all_sources(self) -> List[MedicalImageSource]:
        """Get all approved sources."""
        return list(self.sources.values())
    
    def get_sources_by_trust_score(self, min_score: float = 0.8) -> List[MedicalImageSource]:
        """Get sources with minimum trust score."""
        return [source for source in self.sources.values() if source.trust_score >= min_score]


class ImageRelevanceScorer:
    """Scores image relevance to medical queries."""
    
    def __init__(self):
        """Initialize relevance scorer."""
        self.medical_categories = {
            "anatomy": ["brain", "heart", "lung", "liver", "kidney", "bone", "muscle"],
            "symptoms": ["rash", "swelling", "inflammation", "lesion", "bruise"],
            "conditions": ["depression", "anxiety", "diabetes", "hypertension", "cancer"],
            "treatments": ["surgery", "therapy", "medication", "exercise", "diet"],
            "diagnostics": ["xray", "mri", "ct scan", "ultrasound", "blood test"]
        }
    
    def calculate_relevance(
        self,
        query: str,
        image_metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score for an image.
        
        Args:
            query: Search query
            image_metadata: Image metadata including title, description, tags
            
        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()
        
        # Base relevance from title match
        title = image_metadata.get("title", "").lower()
        title_score = self._calculate_text_similarity(query_lower, title) * 0.4
        
        # Relevance from description match
        description = image_metadata.get("description", "").lower()
        description_score = self._calculate_text_similarity(query_lower, description) * 0.3
        
        # Relevance from tags/keywords
        tags = image_metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tags_text = " ".join(str(tag).lower() for tag in tags)
        tags_score = self._calculate_text_similarity(query_lower, tags_text) * 0.2
        
        # Category relevance
        category_score = self._calculate_category_relevance(query_lower, image_metadata) * 0.1
        
        total_score = title_score + description_score + tags_score + category_score
        
        return min(1.0, max(0.0, total_score))
    
    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """Calculate simple text similarity."""
        if not query or not text:
            return 0.0
        
        query_words = set(query.split())
        text_words = set(text.split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        return len(intersection) / len(query_words)
    
    def _calculate_category_relevance(self, query: str, metadata: Dict[str, Any]) -> float:
        """Calculate relevance based on medical categories."""
        category_score = 0.0
        
        for category, keywords in self.medical_categories.items():
            category_match = any(keyword in query for keyword in keywords)
            metadata_category = metadata.get("category", "").lower()
            
            if category_match and category in metadata_category:
                category_score = 1.0
                break
            elif category_match:
                category_score = max(category_score, 0.5)
        
        return category_score


class ImageContentValidator:
    """Validates medical image content for appropriateness."""
    
    def __init__(self):
        """Initialize content validator."""
        self.blocked_content = [
            "graphic", "disturbing", "explicit", "gore", "violence",
            "inappropriate", "nsfw", "adult content"
        ]
        
        self.warning_content = [
            "surgical", "blood", "wound", "injury", "medical procedure",
            "autopsy", "dissection", "pathology"
        ]
    
    def validate_image(self, image_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate image content.
        
        Args:
            image_metadata: Image metadata
            
        Returns:
            Validation result with safety flags
        """
        title = image_metadata.get("title", "").lower()
        description = image_metadata.get("description", "").lower()
        tags = " ".join(str(tag).lower() for tag in image_metadata.get("tags", []))
        
        content_text = f"{title} {description} {tags}"
        
        # Check for blocked content
        is_blocked = any(blocked in content_text for blocked in self.blocked_content)
        
        # Check for warning content
        needs_warning = any(warning in content_text for warning in self.warning_content)
        
        # Determine safety level
        if is_blocked:
            safety_level = "blocked"
        elif needs_warning:
            safety_level = "warning"
        else:
            safety_level = "safe"
        
        return {
            "is_safe": not is_blocked,
            "safety_level": safety_level,
            "needs_warning": needs_warning,
            "content_warnings": self._extract_warnings(content_text) if needs_warning else []
        }
    
    def _extract_warnings(self, content_text: str) -> List[str]:
        """Extract specific content warnings."""
        warnings = []
        
        warning_map = {
            "surgical": "Contains surgical imagery",
            "blood": "Contains blood or bodily fluids",
            "wound": "Contains wound or injury imagery",
            "medical procedure": "Contains medical procedure imagery"
        }
        
        for keyword, warning in warning_map.items():
            if keyword in content_text:
                warnings.append(warning)
        
        return warnings


class MedicalImageSearchTool:
    """Main medical image search tool with approved sources."""
    
    def __init__(
        self,
        enable_caching: bool = True,
        cache_ttl: int = 3600,
        max_results_per_source: int = 5
    ):
        """
        Initialize medical image search tool.
        
        Args:
            enable_caching: Whether to enable result caching
            cache_ttl: Cache time-to-live in seconds
            max_results_per_source: Maximum results per source
        """
        self.approved_sources = ApprovedImageSources()
        self.relevance_scorer = ImageRelevanceScorer()
        self.content_validator = ImageContentValidator()
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.max_results_per_source = max_results_per_source
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Medical Image Search Tool initialized")
    
    async def search_medical_images(
        self,
        query: str,
        max_results: int = 10,
        min_relevance_score: float = 0.3,
        sources: Optional[List[str]] = None,
        include_warnings: bool = False
    ) -> List[MedicalImage]:
        """
        Search for medical images across approved sources.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            min_relevance_score: Minimum relevance score
            sources: Specific sources to search (None for all)
            include_warnings: Whether to include images with content warnings
            
        Returns:
            List of medical images with metadata
        """
        # Check cache first
        cache_key = self._create_cache_key(query, max_results, min_relevance_score, sources)
        if self.enable_caching and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if datetime.utcnow().timestamp() - cached_result["timestamp"] < self.cache_ttl:
                logger.debug(f"Cache hit for medical image search: {query}")
                return cached_result["results"]
        
        # Determine sources to search
        if sources:
            search_sources = [
                self.approved_sources.get_source(source) 
                for source in sources
                if self.approved_sources.get_source(source)
            ]
        else:
            search_sources = self.approved_sources.get_sources_by_trust_score(0.8)
        
        # Search across sources
        all_results = []
        
        for source in search_sources:
            try:
                source_results = await self._search_source(source, query)
                all_results.extend(source_results)
            except Exception as e:
                logger.error(f"Error searching source {source.name}: {e}")
                continue
        
        # Process and filter results
        processed_results = []
        
        for result in all_results:
            # Validate content
            validation = self.content_validator.validate_image(result)
            
            if not validation["is_safe"]:
                continue
            
            if validation["needs_warning"] and not include_warnings:
                continue
            
            # Calculate relevance
            relevance_score = self.relevance_scorer.calculate_relevance(query, result)
            
            if relevance_score < min_relevance_score:
                continue
            
            # Create MedicalImage object
            medical_image = MedicalImage(
                url=result.get("url", ""),
                caption=result.get("title", ""),
                source=result.get("source", "unknown"),
                license=result.get("license", "unknown"),
                alt_text=result.get("description", result.get("title", "")),
                relevance_score=relevance_score
            )
            
            processed_results.append(medical_image)
        
        # Sort by relevance score
        processed_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        final_results = processed_results[:max_results]
        
        # Cache results
        if self.enable_caching:
            self.cache[cache_key] = {
                "results": final_results,
                "timestamp": datetime.utcnow().timestamp()
            }
        
        logger.info(f"Medical image search completed: {len(final_results)} results for '{query}'")
        return final_results
    
    async def _search_source(
        self,
        source: MedicalImageSource,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search a specific image source.
        
        Args:
            source: Image source to search
            query: Search query
            
        Returns:
            List of image results
        """
        # This is a simplified implementation
        # In production, each source would have its own API integration
        
        # Simulate API search results
        mock_results = [
            {
                "url": f"{source.base_url}/image1.jpg",
                "title": f"Medical illustration related to {query}",
                "description": f"Educational medical image showing {query} from {source.name}",
                "source": source.name,
                "license": source.license_type,
                "tags": [query, "medical", "educational"],
                "category": "medical_illustration"
            },
            {
                "url": f"{source.base_url}/image2.jpg", 
                "title": f"Clinical photo of {query}",
                "description": f"Clinical documentation image from {source.name}",
                "source": source.name,
                "license": source.license_type,
                "tags": [query, "clinical", "documentation"],
                "category": "clinical_photo"
            }
        ]
        
        # In production, this would make actual API calls
        # await self._make_api_request(source, query)
        
        return mock_results[:self.max_results_per_source]
    
    def _create_cache_key(
        self,
        query: str,
        max_results: int,
        min_relevance_score: float,
        sources: Optional[List[str]]
    ) -> str:
        """Create cache key for search parameters."""
        key_data = {
            "query": query.lower(),
            "max_results": max_results,
            "min_relevance_score": min_relevance_score,
            "sources": sorted(sources) if sources else None
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_image_by_url(self, url: str) -> Optional[MedicalImage]:
        """
        Get medical image by URL with validation.
        
        Args:
            url: Image URL
            
        Returns:
            MedicalImage object if valid, None otherwise
        """
        try:
            # Validate URL is from approved source
            is_approved = any(
                source.base_url in url 
                for source in self.approved_sources.get_all_sources()
            )
            
            if not is_approved:
                logger.warning(f"Image URL not from approved source: {url}")
                return None
            
            # Create basic medical image object
            # In production, would fetch metadata from source
            return MedicalImage(
                url=url,
                caption="Medical image",
                source="approved_source",
                license="educational_use",
                alt_text="Medical educational image",
                relevance_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Error getting image by URL: {e}")
            return None
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about approved sources."""
        sources_info = {}
        
        for name, source in self.approved_sources.sources.items():
            sources_info[name] = {
                "name": source.name,
                "trust_score": source.trust_score,
                "license_type": source.license_type,
                "rate_limit": source.rate_limit
            }
        
        return sources_info
    
    def clear_cache(self):
        """Clear the image search cache."""
        self.cache.clear()
        logger.info("Medical image search cache cleared")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            "cache_size": len(self.cache),
            "approved_sources_count": len(self.approved_sources.sources),
            "cache_enabled": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "max_results_per_source": self.max_results_per_source
        }
