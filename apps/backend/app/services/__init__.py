"""Domain services layer.

Business logic (money movement, order lifecycle, menu caching) lives here rather
than inside FastAPI route functions. The routers under `app/api/endpoints/` are
meant to be thin: parse the request, call a service, shape the response.

Why this exists
---------------
Previously every rule was written inside `endpoints/*.py`, which caused concrete
problems rather than aesthetic ones:

* `endpoints/admin.py` imported `process_refund` out of `endpoints/order.py`, so
  the refund rule had two call sites in two routers and the role check had to be
  duplicated at each - which is exactly how a barista was able to refund through
  the `/admin` route after the `/orders` route was tightened.
* The "batch fetch transactions + items, then map to OrderResponse" block was
  copy-pasted four times, and the copies had already drifted (some selected
  `type == "order"`, one selected the refund row).
* Money arithmetic appeared in `order.py`, `users.py` and `admin.py` with
  different locking assumptions.
"""
