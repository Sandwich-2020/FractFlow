"""
Tests for the weather forecast tools.
"""

import pytest
from unittest import mock
import json
import asyncio
from typing import Dict, Any

from src.tools.weather.forecast import (
    make_nws_request,
    format_alert,
    get_alerts,
    get_forecast,
    assess_running_condition
)

class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        
    def json(self):
        return self.data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

class TestWeatherForecast:
    """Test the weather forecast tools."""
    
    @pytest.mark.asyncio
    @mock.patch("src.tools.weather.forecast.httpx.AsyncClient")
    async def test_make_nws_request_success(self, mock_client):
        """Test the NWS API request function with a successful response."""
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get.return_value = MockResponse({"test": "data"})
        
        result = await make_nws_request("https://test.url")
        
        assert result == {"test": "data"}
        mock_instance.get.assert_called_once()
    
    @pytest.mark.asyncio
    @mock.patch("src.tools.weather.forecast.httpx.AsyncClient")
    async def test_make_nws_request_failure(self, mock_client):
        """Test the NWS API request function with a failed response."""
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get.side_effect = Exception("Network error")
        
        result = await make_nws_request("https://test.url")
        
        assert result is None
        mock_instance.get.assert_called_once()
        
    def test_format_alert(self):
        """Test the alert formatting function."""
        test_feature = {
            "properties": {
                "event": "Test Alert",
                "areaDesc": "Test Area",
                "severity": "Moderate",
                "description": "This is a test alert",
                "instruction": "Stay indoors"
            }
        }
        
        result = format_alert(test_feature)
        
        assert "Test Alert" in result
        assert "Test Area" in result
        assert "Moderate" in result
        assert "This is a test alert" in result
        assert "Stay indoors" in result
        
    @pytest.mark.asyncio
    @mock.patch("src.tools.weather.forecast.make_nws_request")
    async def test_get_alerts(self, mock_make_request):
        """Test the get_alerts function."""
        mock_make_request.return_value = {
            "features": [
                {
                    "properties": {
                        "event": "Test Alert",
                        "areaDesc": "Test Area",
                        "severity": "Moderate",
                        "description": "This is a test alert",
                        "instruction": "Stay indoors"
                    }
                }
            ]
        }
        
        result = await get_alerts("CA")
        
        assert "Test Alert" in result
        assert "Test Area" in result
        mock_make_request.assert_called_once()
        
    @pytest.mark.asyncio
    @mock.patch("src.tools.weather.forecast.make_nws_request")
    async def test_get_forecast(self, mock_make_request):
        """Test the get_forecast function."""
        # Mock the points response
        mock_make_request.side_effect = [
            {
                "properties": {
                    "forecast": "https://test.forecast.url"
                }
            },
            {
                "properties": {
                    "periods": [
                        {
                            "name": "Tonight",
                            "temperature": 72,
                            "temperatureUnit": "F",
                            "windSpeed": "5 mph",
                            "windDirection": "SW",
                            "detailedForecast": "Clear and cool"
                        }
                    ]
                }
            }
        ]
        
        result = await get_forecast(37.7749, -122.4194)
        
        assert "Tonight" in result
        assert "72°F" in result
        assert "5 mph SW" in result
        assert "Clear and cool" in result
        assert mock_make_request.call_count == 2
        
    def test_assess_running_condition(self):
        """Test the running condition assessment function."""
        test_weather = {
            "condition": "sunny",
            "temperature_low": 18,
            "temperature_high": 24,
            "air_quality": "excellent",
            "wind_speed": "light breeze"
        }
        
        result = asyncio.run(assess_running_condition(test_weather))
        
        assert "跑步适宜度评分" in result or "Running Conditions Score" in result
        assert result
        assert len(result) > 10 