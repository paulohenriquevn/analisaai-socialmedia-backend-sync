import httpx
import asyncio
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import structlog
from app.config.settings import settings
from app.utils.rate_limit import rate_limited
from app.utils.errors import ExternalAPIError

# Set up logger
logger = structlog.get_logger("analisaai-sync")

class ApifyService:
    """
    Service for interacting with Apify API
    """
    
    def __init__(self):
        """Initialize the Apify service"""
        self.base_url = settings.APIFY_BASE_URL
        self.api_token = settings.APIFY_API_TOKEN
        self.timeout = 60  # seconds
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        Make a request to the Apify API
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Dict, optional): Request data. Defaults to None.
        
        Returns:
            Dict: Response data
        
        Raises:
            ExternalAPIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=data)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check for successful response
                response.raise_for_status()
                
                # Parse response
                return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "Apify API HTTP error", 
                status_code=e.response.status_code, 
                response=e.response.text,
                method=method,
                url=url
            )
            raise ExternalAPIError(
                detail=f"Apify API returned {e.response.status_code}: {e.response.text}",
                error_code="apify_http_error"
            )
        except httpx.RequestError as e:
            logger.error(
                "Apify API request error", 
                error=str(e),
                method=method,
                url=url
            )
            raise ExternalAPIError(
                detail=f"Request to Apify API failed: {str(e)}",
                error_code="apify_request_error"
            )
    
    @rate_limited
    async def get_instagram_profile(self, username: str) -> Dict:
        """
        Get Instagram profile data using Apify
        
        Args:
            username (str): Instagram username
        
        Returns:
            Dict: Instagram profile data
        """
        logger.info("Fetching Instagram profile data", username=username)
        
        # Create task configuration
        task_input = {
            "username": username,
            "resultsLimit": 1,
            "resultsType": "details",
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        # Run the actor
        run_data = await self._make_request(
            "POST", 
            "/acts/apify~instagram-profile-scraper/runs", 
            data={
                "runInput": task_input
            }
        )
        
        # Get run ID
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            raise ExternalAPIError(
                detail="Failed to start Instagram profile scraper",
                error_code="apify_run_error"
            )
        
        # Wait for run to finish
        run_status = "RUNNING"
        max_attempts = 30
        attempts = 0
        
        while run_status in ["RUNNING", "READY"] and attempts < max_attempts:
            # Get run status
            run_info = await self._make_request("GET", f"/actor-runs/{run_id}")
            run_status = run_info.get("data", {}).get("status")
            
            # If still running, wait and try again
            if run_status in ["RUNNING", "READY"]:
                await asyncio.sleep(2)
                attempts += 1
        
        # Check if run finished successfully
        if run_status != "SUCCEEDED":
            raise ExternalAPIError(
                detail=f"Instagram profile scraper run failed with status: {run_status}",
                error_code="apify_run_failed"
            )
        
        # Get the dataset items
        dataset_id = run_info.get("data", {}).get("defaultDatasetId")
        if not dataset_id:
            raise ExternalAPIError(
                detail="Failed to get dataset ID from Instagram profile scraper run",
                error_code="apify_dataset_error"
            )
        
        # Get dataset items
        dataset = await self._make_request("GET", f"/datasets/{dataset_id}/items")
        
        # Check if data was retrieved
        items = dataset.get("data", {}).get("items", [])
        if not items:
            logger.warning("No Instagram profile data found", username=username)
            return {}
        
        # Return first item
        return items[0]
    
    @rate_limited
    async def get_instagram_posts(self, username: str, limit: int = 30) -> List[Dict]:
        """
        Get Instagram posts data using Apify
        
        Args:
            username (str): Instagram username
            limit (int, optional): Maximum number of posts to fetch. Defaults to 30.
        
        Returns:
            List[Dict]: List of Instagram posts
        """
        logger.info("Fetching Instagram posts data", username=username, limit=limit)
        
        # Create task configuration
        task_input = {
            "username": username,
            "resultsLimit": limit,
            "resultsType": "posts",
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        # Run the actor
        run_data = await self._make_request(
            "POST", 
            "/acts/apify~instagram-profile-scraper/runs", 
            data={
                "runInput": task_input
            }
        )
        
        # Get run ID
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            raise ExternalAPIError(
                detail="Failed to start Instagram posts scraper",
                error_code="apify_run_error"
            )
        
        # Wait for run to finish
        run_status = "RUNNING"
        max_attempts = 30
        attempts = 0
        
        while run_status in ["RUNNING", "READY"] and attempts < max_attempts:
            # Get run status
            run_info = await self._make_request("GET", f"/actor-runs/{run_id}")
            run_status = run_info.get("data", {}).get("status")
            
            # If still running, wait and try again
            if run_status in ["RUNNING", "READY"]:
                await asyncio.sleep(2)
                attempts += 1
        
        # Check if run finished successfully
        if run_status != "SUCCEEDED":
            raise ExternalAPIError(
                detail=f"Instagram posts scraper run failed with status: {run_status}",
                error_code="apify_run_failed"
            )
        
        # Get the dataset items
        dataset_id = run_info.get("data", {}).get("defaultDatasetId")
        if not dataset_id:
            raise ExternalAPIError(
                detail="Failed to get dataset ID from Instagram posts scraper run",
                error_code="apify_dataset_error"
            )
        
        # Get dataset items
        dataset = await self._make_request("GET", f"/datasets/{dataset_id}/items")
        
        # Check if data was retrieved
        items = dataset.get("data", {}).get("items", [])
        if not items:
            logger.warning("No Instagram posts data found", username=username)
            return []
        
        # Return items
        return items
        
    @rate_limited
    async def get_facebook_page(self, page_name: str) -> Dict:
        """
        Get Facebook page data using Apify
        
        Args:
            page_name (str): Facebook page name or ID
        
        Returns:
            Dict: Facebook page data
        """
        logger.info("Fetching Facebook page data", page_name=page_name)
        
        # Create task configuration
        task_input = {
            "startUrls": [
                {
                    "url": f"https://www.facebook.com/{page_name}"
                }
            ],
            "resultsType": "details",
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        # Run the actor
        run_data = await self._make_request(
            "POST", 
            "/acts/apify~facebook-page-scraper/runs", 
            data={
                "runInput": task_input
            }
        )
        
        # Get run ID
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            raise ExternalAPIError(
                detail="Failed to start Facebook page scraper",
                error_code="apify_run_error"
            )
        
        # Wait for run to finish
        run_status = "RUNNING"
        max_attempts = 30
        attempts = 0
        
        while run_status in ["RUNNING", "READY"] and attempts < max_attempts:
            # Get run status
            run_info = await self._make_request("GET", f"/actor-runs/{run_id}")
            run_status = run_info.get("data", {}).get("status")
            
            # If still running, wait and try again
            if run_status in ["RUNNING", "READY"]:
                await asyncio.sleep(2)
                attempts += 1
        
        # Check if run finished successfully
        if run_status != "SUCCEEDED":
            raise ExternalAPIError(
                detail=f"Facebook page scraper run failed with status: {run_status}",
                error_code="apify_run_failed"
            )
        
        # Get the dataset items
        dataset_id = run_info.get("data", {}).get("defaultDatasetId")
        if not dataset_id:
            raise ExternalAPIError(
                detail="Failed to get dataset ID from Facebook page scraper run",
                error_code="apify_dataset_error"
            )
        
        # Get dataset items
        dataset = await self._make_request("GET", f"/datasets/{dataset_id}/items")
        
        # Check if data was retrieved
        items = dataset.get("data", {}).get("items", [])
        if not items:
            logger.warning("No Facebook page data found", page_name=page_name)
            return {}
        
        # Return first item
        return items[0]
    
    @rate_limited
    async def get_tiktok_profile(self, username: str) -> Dict:
        """
        Get TikTok profile data using Apify
        
        Args:
            username (str): TikTok username
        
        Returns:
            Dict: TikTok profile data
        """
        logger.info("Fetching TikTok profile data", username=username)
        
        # Create task configuration
        task_input = {
            "username": username,
            "scrollTimeout": 10,
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        # Run the actor
        run_data = await self._make_request(
            "POST", 
            "/acts/clockworks~tiktok-profile-scraper/runs", 
            data={
                "runInput": task_input
            }
        )
        
        # Get run ID
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            raise ExternalAPIError(
                detail="Failed to start TikTok profile scraper",
                error_code="apify_run_error"
            )
        
        # Wait for run to finish
        run_status = "RUNNING"
        max_attempts = 30
        attempts = 0
        
        while run_status in ["RUNNING", "READY"] and attempts < max_attempts:
            # Get run status
            run_info = await self._make_request("GET", f"/actor-runs/{run_id}")
            run_status = run_info.get("data", {}).get("status")
            
            # If still running, wait and try again
            if run_status in ["RUNNING", "READY"]:
                await asyncio.sleep(2)
                attempts += 1
        
        # Check if run finished successfully
        if run_status != "SUCCEEDED":
            raise ExternalAPIError(
                detail=f"TikTok profile scraper run failed with status: {run_status}",
                error_code="apify_run_failed"
            )
        
        # Get the dataset items
        dataset_id = run_info.get("data", {}).get("defaultDatasetId")
        if not dataset_id:
            raise ExternalAPIError(
                detail="Failed to get dataset ID from TikTok profile scraper run",
                error_code="apify_dataset_error"
            )
        
        # Get dataset items
        dataset = await self._make_request("GET", f"/datasets/{dataset_id}/items")
        
        # Check if data was retrieved
        items = dataset.get("data", {}).get("items", [])
        if not items:
            logger.warning("No TikTok profile data found", username=username)
            return {}
        
        # Return first item
        return items[0]