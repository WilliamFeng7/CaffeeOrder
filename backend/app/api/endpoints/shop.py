from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_shop_status():
    """
    Get current shop status (open/closed)
    """
    return {"is_open": True, "message": "Shop is open"}
