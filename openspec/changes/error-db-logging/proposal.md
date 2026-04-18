## Why

In a k3s environment, checking stdout logs for every pod execution is cumbersome. Errors (API failures, order failures, unhandled exceptions) should be queryable directly from the database so operators can monitor the system without accessing pod logs.

## What Changes

- `run_once()` exception handler now writes a `rebalancing_logs` row with `status="failed"` and the exception traceback when an unhandled error occurs before any result exists
- `save_system_log()` in `db_manager.py` is called at key failure points: portfolio fetch failure, order execution failure, and scheduler-level exceptions
- `db_manager.py` DB save methods no longer call `sys.exit(1)` on `psycopg2.DatabaseError` — they log and continue instead, preventing CrashLoopBackOff from DB write failures
- Individual order failures are recorded in `trading_history` with `status="failed"` regardless of overall rebalancing success/failure

## Capabilities

### New Capabilities
- `error-db-logging`: Persisting application errors (unhandled exceptions, order failures, fetch failures) into existing DB tables (`rebalancing_logs`, `system_logs`, `trading_history`) so they are queryable without pod log access

### Modified Capabilities
- `scheduling`: Scheduler-level exceptions are now caught and written to `system_logs` before re-raising or continuing
- `order-execution`: Individual failed orders are written to `trading_history` with `status="failed"` immediately, not deferred to overall result
- `portfolio-fetching`: Fetch-level exceptions are written to `system_logs` before propagating

## Impact

- `Scripts/apps/portfolio_rebalancing.py`: `run_once()` outer `except` block, `_save_to_database()`
- `Scripts/modules/db_manager.py`: remove `sys.exit(1)` from all save methods; no new tables or schema changes
- `Scripts/modules/order_executor.py`: call `save_system_log()` on order failure
- `Scripts/modules/unified_portfolio_fetcher.py`: call `save_system_log()` on fetch failure
- `Scripts/modules/scheduler.py`: call `save_system_log()` on scheduler exception
- No schema migrations required — `system_logs` and `trading_history` tables already exist
