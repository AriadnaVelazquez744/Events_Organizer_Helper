# src/crawler/__init__.py
"""
Crawler package for web scraping and data extraction.

This package provides a comprehensive web crawling system with:
- Core crawling functionality
- Data extraction and processing
- Quality validation and enrichment
- Knowledge graph storage
"""

# Core imports
from .core.core import AdvancedCrawlerAgent
from .core.manager import CrawlerManager
from .core.policy import CrawlPolicy

# Extraction imports
from .extraction.scrapper import scrape_page, setup_driver
from .extraction.llm_extract_openrouter import llm_extract_openrouter
from .extraction.expert import ExpertSystemInterface
from .extraction.graph import KnowledgeGraphInterface

# Quality imports
from .quality.quality_validator import DataQualityValidator
from .quality.enrichment_engine import DynamicEnrichmentEngine
from .quality.monitoring import DataQualityMonitor

__version__ = "1.0.0"
__author__ = "Events Organizer Helper Team"

__all__ = [
    # Core
    "AdvancedCrawlerAgent",
    "CrawlerManager", 
    "CrawlPolicy",
    
    # Extraction
    "scrape_page",
    "setup_driver",
    "llm_extract_openrouter",
    "ExpertSystemInterface",
    "KnowledgeGraphInterface",
    
    # Quality
    "DataQualityValidator",
    "DynamicEnrichmentEngine",
    "DataQualityMonitor",
] 