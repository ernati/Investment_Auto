# KIS API Utilities Documentation

## Overview

The **kis_api_utils.py** module provides shared utility functions for interacting with the Korea Investment & Securities (KIS) Open API. This module was created as part of a refactoring effort to eliminate code duplication across the portfolio management system.

## Problem Solved

This refactoring addressed the following code duplication issues:

1. **Header Construction Duplication**: Both `kis_portfolio_fetcher.py` and `order_executor.py` had identical `_get_headers()` methods
2. **API Response Validation Duplication**: Both modules checked `data.get('rt_cd') == '0'` for API success
3. **Error Handling Duplication**: Both modules implemented similar try-catch patterns for API calls
4. **Order Placement Duplication**: `order_executor.py` had two nearly identical methods (`_place_market_order` and `_place_limit_order`)

## Module Functions

### build_api_headers()

**Purpose**: Generate request headers for KIS API calls

```python
def build_api_headers(
    kis_auth: KISAuth,
    tr_id: str,
    tr_cont: str = ""
) -> Dict[str, str]:
```

**Parameters**:
- `kis_auth` (KISAuth): Authentication information with API credentials
- `tr_id` (str): Transaction ID (e.g., 'TTTC8434R', 'FHKST01010100')
- `tr_cont` (str, optional): Transaction continue code for pagination

**Returns**: Dictionary containing properly formatted HTTP headers for KIS API requests

**Features**:
- Automatically authenticates and retrieves Bearer token
- Includes all required headers (Content-Type, Authorization, appKey, appSecret, tr_id)
- Normalizes TR IDs for demo accounts (e.g., TTTC → VTTC)
- Sets custtype to 'P' for individual customers
- Handles pagination with optional tr_cont parameter

**Example**:
```python
headers = build_api_headers(kis_auth, 'TTTC8434R')
```

---

### validate_api_response()

**Purpose**: Validate KIS API response format

```python
def validate_api_response(
    response_data: Dict[str, Any],
    context: str = "KIS API"
) -> tuple[bool, Optional[str]]:
```

**Parameters**:
- `response_data` (Dict): Raw response data from KIS API
- `context` (str, optional): Context information for error logging

**Returns**: Tuple of (success_bool, error_message_or_none)

**Features**:
- Checks if response rt_cd equals '0' (success)
- Logs error messages from failed responses
- Provides context in error logs for debugging

**Example**:
```python
success, error_msg = validate_api_response(response_data, "Fetch portfolio balance")
if success:
    # Process response
else:
    # Handle error: error_msg contains details
```

---

### execute_api_request()

**Purpose**: Execute HTTP request against KIS API with proper error handling

```python
def execute_api_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    context: str = "KIS API"
) -> Dict[str, Any]:
```

**Parameters**:
- `method` (str): HTTP method ('GET', 'POST', 'DELETE')
- `url` (str): API endpoint URL
- `headers` (Dict): Request headers (typically from `build_api_headers()`)
- `params` (Dict, optional): URL parameters (for GET requests)
- `json_data` (Dict, optional): JSON body (for POST requests)
- `timeout` (int): Request timeout in seconds
- `context` (str, optional): Context for error logging

**Returns**: Parsed JSON response data

**Raises**:
- `requests.exceptions.RequestException`: Network/HTTP errors
- `RuntimeError`: KIS API returned error status

**Features**:
- Supports GET, POST, DELETE methods
- Automatic response validation
- Detailed error logging with context
- Handles various exception types (Timeout, ConnectionError, HTTPError, etc.)
- JSON parsing with error handling

**Example**:
```python
headers = build_api_headers(kis_auth, 'TTTC8434R')
data = execute_api_request(
    'GET',
    'https://api.kisdata.com/uapi/domestic-stock/v1/trading/inquire-balance',
    headers,
    params={'cano': '12345678', 'acnt_prdt_cd': '01'},
    context='Fetch account balance'
)
```

---

### place_stock_order()

**Purpose**: Execute a stock order (buy/sell) with market or limit price

```python
def place_stock_order(
    kis_auth: KISAuth,
    base_url: str,
    order_type: str,
    action: str,
    ticker: str,
    quantity: int,
    price: Optional[float] = None,
    order_dvsn: Optional[str] = None,
    exchange_id: str = "KRX",
    sell_type: str = "01",
    condition_price: str = ""
) -> Dict[str, Any]:
```

**Parameters**:
- `kis_auth` (KISAuth): Authentication information
- `base_url` (str): KIS API base URL
- `order_type` (str): 'market' or 'limit'
- `action` (str): 'buy' or 'sell'
- `ticker` (str): Stock ticker code
- `quantity` (int): Order quantity
- `price` (float, optional): Order price (required for limit orders)
- `order_dvsn` (str, optional): Order division (e.g., "00" limit, "01" market)
- `exchange_id` (str, optional): Exchange ID (default: "KRX")
- `sell_type` (str, optional): Sell type for sell orders (default: "01")
- `condition_price` (str, optional): Conditional price for special order types

**Returns**: Order result dictionary

**Result Format**:
```python
{
    'success': bool,
    'message': str,
    'order_id': str,          # Only if successful
    'ticker': str,
    'action': str,
    'quantity': int,
    'price': float,
    'timestamp': str          # ISO format
}
```

**Features**:
- Unified interface for market and limit orders
- Uses order-cash endpoint with `ORD_DVSN` for market/limit selection
- Automatic TR ID selection (buy/sell) and demo normalization
- Validates quantity and limit price inputs
- Error handling with detailed messages
- Never raises exceptions (returns error dict instead)
- Logs all operations for audit trail

**Example**:
```python
# Market order
result = place_stock_order(
    kis_auth,
    'https://api.kisdata.com',
    'market',
    'buy',
    '005930',      # Samsung Electronics
    100
)

# Limit order
result = place_stock_order(
    kis_auth,
    'https://api.kisdata.com',
    'limit',
    'sell',
    '005930',
    50,
    price=70000,
    order_dvsn="00",
    exchange_id="KRX"
)
```

---

## Usage Examples

### Example 1: Fetch Portfolio Data

```python
from Scripts.modules.kis_auth import KISAuth
from Scripts.modules.kis_api_utils import build_api_headers, execute_api_request

kis_auth = KISAuth(appkey='your_key', appsecret='your_secret', account='12345678', product='01')

# Fetch account balance
headers = build_api_headers(kis_auth, 'TTTC8434R')
balance_data = execute_api_request(
    'GET',
    f'{kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-balance',
    headers,
    params={'cano': kis_auth.account[:8], 'acnt_prdt_cd': kis_auth.product},
    context='Fetch account balance'
)

cash = float(balance_data['output1']['nxdy_excc_amt'])
```

### Example 2: Place Orders

```python
from Scripts.modules.kis_api_utils import place_stock_order

# Buy 100 shares at market price
buy_result = place_stock_order(
    kis_auth,
    kis_auth.base_url,
    'market',
    'buy',
    '005930',
    100
)

if buy_result['success']:
    print(f"Buy order placed: {buy_result['order_id']}")
else:
    print(f"Order failed: {buy_result['message']}")
```

### Example 3: Refactored Module Usage

Both `kis_portfolio_fetcher.py` and `order_executor.py` have been refactored to use these utilities:

**kis_portfolio_fetcher.py**:
```python
# Before: Custom _get_headers() and try-catch blocks
# After: Uses build_api_headers() and execute_api_request()

headers = build_api_headers(self.kis_auth, 'TTTC8434R')
data = execute_api_request(
    'GET',
    url,
    headers,
    params=params,
    context='Fetch account balance'
)
```

**order_executor.py**:
```python
# Before: Separate _place_market_order() and _place_limit_order()
# After: Uses unified place_stock_order()

order_result = place_stock_order(
    self.kis_auth,
    self.base_url,
    self.order_type,
    order.action,
    order.ticker,
    order.estimated_quantity,
    price=order.estimated_price
)
```

## API Response Format

KIS API responses follow this format:

```json
{
    "rt_cd": "0",              // "0" = success, others = failure
    "msg": "Success",          // Response message
    "output1": {...},          // Primary output
    "output2": [...],          // Secondary output (typically list)
    "output": {...}            // Alternative output format
}
```

## Error Handling Strategy

The utilities implement comprehensive error handling:

1. **Network Errors**: Caught separately (Timeout, ConnectionError)
2. **HTTP Errors**: Logged with detailed information
3. **JSON Parse Errors**: Handled with context
4. **API Error Status**: Validated via rt_cd check
5. **Unexpected Errors**: Caught as fallback

All errors are logged with context information for debugging.

## Performance Considerations

- **Token Caching**: KISAuth handles token caching internally; new headers always get fresh tokens
- **Timeout**: Default 10 seconds; adjustable per request
- **Error Retry**: Not implemented in utilities (caller's responsibility)
- **Rate Limiting**: Not implemented (KIS API rate limits apply)

## Best Practices

1. **Always provide context**: Use context parameter for better error logging
2. **Check success flag**: For `place_stock_order()`, always check the 'success' key
3. **Handle exceptions**: `execute_api_request()` can raise exceptions; use try-catch
4. **Log results**: All functions log their operations for audit trail
5. **Validate inputs**: Caller responsible for input validation (ticker codes, quantities, etc.)

## Related Modules

- [kis_auth.py](kis_auth.md): Authentication management
- [kis_portfolio_fetcher.py](kis_portfolio_fetcher.md): Portfolio data retrieval (refactored to use these utilities)
- [order_executor.py](order_executor.md): Order execution (refactored to use these utilities)

## Testing

To test these utilities:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Test header generation
headers = build_api_headers(kis_auth, 'TTTC8434R')
assert 'Authorization' in headers
assert headers['tr_id'] == 'TTTC8434R'

# Test response validation
test_response = {'rt_cd': '0', 'msg': 'Success', 'output': {}}
success, error = validate_api_response(test_response)
assert success == True
assert error == None

# Test API call
data = execute_api_request('GET', url, headers, params=params)
assert 'rt_cd' in data
assert data['rt_cd'] == '0'
```

## Changelog

### Version 1.0 (Initial Release)
- Created `build_api_headers()` function
- Created `validate_api_response()` function
- Created `execute_api_request()` function
- Created `place_stock_order()` function
- Refactored `kis_portfolio_fetcher.py` to use utilities
- Refactored `order_executor.py` to use utilities
- Reduced code duplication by ~40%

### Version 2.0 (Bug Fixes - 2026-02-16)

**Major Bug Fixes:**
1. **Fixed TR_ID Issue**: 
   - Fixed incorrect TR_ID usage in `place_stock_order()`
   - Changed from legacy TR_ID (TTTC0802U/0801U) to new TR_ID (TTTC0012U/0011U)
   - This resolves RT_CD=1 errors in stock order placement

2. **Account Number Processing**:
   - Removed unnecessary account number slicing `account[:8]`
   - Account numbers from config are already 8 digits

3. **Enhanced Error Handling**:
   - Improved `validate_api_response()` to extract detailed error information
   - Added MSG_CD and MSG1 field processing
   - Added debug logging for response output

4. **Rate Limiting Improvements**:
   - Added `execute_api_request_with_retry()` with backoff strategy
   - Implemented exponential backoff with jitter
   - Enhanced rate limiting for demo vs real environments

**New Features:**
- Added comprehensive error message extraction
- Enhanced logging capabilities
- Improved retry mechanism with better error handling

**TR_ID Reference (Updated)**:
| Environment | Action | TR_ID |
|-------------|--------|-------|
| Real | Buy | TTTC0012U |
| Real | Sell | TTTC0011U |
| Demo | Buy | VTTC0012U |
| Demo | Sell | VTTC0011U |

## Future Improvements

1. **Retry Logic**: ✅ **COMPLETED** - Added exponential backoff for transient failures
2. **Rate Limiting**: ✅ **COMPLETED** - Implement token-bucket rate limiter
3. **Response Caching**: Cache price and balance data briefly
4. **Batch Operations**: Support batch order placement
5. **Async Support**: Add async/await versions of functions
