"""API for Alibaba Cloud."""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from alibabacloud_bssopenapi20171214.client import Client as BssOpenApi20171214Client
from alibabacloud_bssopenapi20171214.models import DescribeInstanceBillRequest
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util.models import RuntimeOptions
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class AliyunApiError(Exception):
    """Exception to indicate a general API error."""

class AliyunAuthError(Exception):
    """Exception to indicate an authentication error."""

class AliyunBssApiClient:
    """Alibaba Cloud BSS OpenAPI Client."""

    def __init__(self, access_key_id: str, access_key_secret: str, hass: HomeAssistant):
        """Initialize the API client."""
        self._config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id="cn-hangzhou",
        )
        self._client = BssOpenApi20171214Client(self._config)
        self._hass = hass

    async def _execute_api_call(self, call, *args, **kwargs):
        """Wrap SDK calls to run them in the executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, call, *args, **kwargs)

    async def test_authentication(self) -> bool:
        """Test if the provided credentials are valid."""
        try:
            request = DescribeInstanceBillRequest(billing_cycle="2020-01", max_results=1)
            await self._execute_api_call(self._client.describe_instance_bill_with_options, request, RuntimeOptions())
        except Exception as e:
            if "InvalidAccessKeyId" in str(e) or "Forbidden" in str(e):
                raise AliyunAuthError("Invalid AccessKey ID or Secret") from e
            raise AliyunApiError(f"API test call failed: {e}") from e
        return True

    async def _fetch_all_bill_details(self, billing_cycle: str) -> List[Dict[str, Any]]:
        """Fetch all bill details for a given cycle, handling pagination."""
        all_items = []
        tasks = [
            self._fetch_bill_details_by_type(billing_cycle, 'PayAsYouGo'),
            self._fetch_bill_details_by_type(billing_cycle, 'Subscription')
        ]
        results = await asyncio.gather(*tasks)
        for result_list in results:
            all_items.extend(result_list)
        return all_items

    async def _fetch_bill_details_by_type(self, billing_cycle: str, sub_type: str) -> List[Dict[str, Any]]:
        """Fetch paged bill details for a specific subscription type."""
        all_items = []
        next_token = None
        while True:
            request = DescribeInstanceBillRequest(
                billing_cycle=billing_cycle,
                subscription_type=sub_type,
                is_billing_item=True,
                max_results=300,
                next_token=next_token,
            )
            try:
                response = await self._execute_api_call(self._client.describe_instance_bill, request)
                response_dict = response.body.to_map()
                data = response_dict.get('Data', {})
                if not data:
                    break
                items_list = []
                if isinstance(data, dict):
                    items_list = data.get('Items', [])
                elif isinstance(data, list):
                    items_list = data
                else:
                    items_list = []

                all_items.extend(items_list)
                # 只在 data 是 dict 时才继续，否则直接 break
                if isinstance(data, dict):
                    next_token = data.get('NextToken')
                    if not next_token:
                        break
                else:
                    break
            except Exception as e:
                _LOGGER.error("Failed to fetch billing details for %s: %s", sub_type, e)
                break
        return all_items

    async def get_current_month_data(self) -> Dict[str, Any]:
        """Fetch and process data for the current billing cycle."""
        current_cycle = datetime.now().strftime("%Y-%m")
        all_items = await self._fetch_all_bill_details(current_cycle)

        if not all_items:
            return {"total_cost": 0.0, "total_traffic_gb": 0.0, "cost_by_service": {}}

        # Calculate total cost and group by service
        total_cost = 0.0
        cost_by_service = {}
        for item in all_items:
            amount = float(item.get('PretaxAmount', 0.0))
            total_cost += amount
            product_code = item.get('ProductCode', 'Unknown')
            cost_by_service.setdefault(product_code, 0.0)
            cost_by_service[product_code] += amount

        # Calculate total traffic
        total_traffic_gb = self._calculate_traffic(all_items)

        result = {
            "total_cost": round(total_cost, 2),
            "total_traffic_gb": round(total_traffic_gb, 4),
            "cost_by_service": {k: round(v, 2) for k, v in cost_by_service.items()},
            # "raw_data": all_items
        }
        return result

    def _calculate_traffic(self, all_items: List[Dict[str, Any]]) -> float:
        """Calculate total outbound traffic in GB from a list of bill items."""
        total_usage_bytes = 0.0
        traffic_items_codes = [
            "ECS_Out_Bytes", "Eip_Out_Bytes", "Cdn_domestic_flow",
            "Cdn_overseas_flow", "OSS_Out_Traffic"
        ]
        for item in all_items:
            if item.get('BillingItemCode') in traffic_items_codes:
                usage_str = item.get('Usage')
                unit = (item.get('UsageUnit') or '').upper()
                if usage_str:
                    try:
                        usage = float(usage_str)
                        if unit == 'GB':
                            total_usage_bytes += usage * 1024**3
                        elif unit == 'MB':
                            total_usage_bytes += usage * 1024**2
                        elif unit == 'KB':
                            total_usage_bytes += usage * 1024
                        elif unit == 'B':
                            total_usage_bytes += usage
                    except (ValueError, TypeError):
                        continue
        return total_usage_bytes / (1024**3)
