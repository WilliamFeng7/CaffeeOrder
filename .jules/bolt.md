## 2024-03-24 - N+1 Query in Order Fetching
**Learning:** SQLModel/SQLAlchemy code iterating over results and fetching related data inside the loop causes massive N+1 query issues. `sync_orders` also had a logic bug where it queried transactions by `user_id` instead of `order_id`, likely returning incorrect transaction data for users with multiple orders.
**Action:** Always batch fetch related data using `.in_()` clauses and reconstruct relationships in memory using dictionaries. This reduces query count from O(N) to O(1).
