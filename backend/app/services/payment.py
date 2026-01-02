import random
import uuid
import asyncio

class PaymentService:
    """
    支付服务 (Payment Service)
    
    模拟学校一卡通外部支付 API。
    在生产环境中，此类应负责发起真正的 HTTPS 请求对接支付网关。
    Mock service to simulate School External Payment API.
    """
    
    @staticmethod
    async def deduct_balance(student_id: str, amount_cents: int) -> str:
        """
        扣除余额 (Deduct Balance)
        
        Args:
            student_id: 学号
            amount_cents: 金额 (分)
            
        Returns:
            str: 外部交易流水号 (External Transaction ID)
            
        Raises:
            Exception: 如果余额不足或系统错误
        """
        # Validation: Prevent negative or invalid amounts
        if amount_cents <= 0:
            raise ValueError(f"Invalid payment amount: {amount_cents} cents")
        
        # Validation: Prevent unreasonably large transactions (e.g., > 10,000 Yuan)
        if amount_cents > 1000000:  # 10,000 Yuan
            raise ValueError(f"Payment amount exceeds maximum limit: {amount_cents} cents")
        
        # 模拟网络延迟 (Simulate latency & Processing)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # --- 模拟逻辑 (Mock Logic) ---
        # 总是返回成功，但在真实场景中这里会调用 Bank API
        
        # 生成一个模拟的外部交易号
        return f"EXT-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    async def refund(student_id: str, amount_cents: int) -> bool:
        """
        退款 (Refund)
        
        用于订单失败或取消时的资金回滚。
        """
        await asyncio.sleep(0.5)
        return True

    @staticmethod
    async def get_balance(student_id: str) -> int:
        """
        查询余额 (Get Balance)
        
        Returns:
            int: 余额 (分)
        """
        await asyncio.sleep(0.3)
        # 模拟返回固定余额 50.00 元
        return 5000 


# 单例实例 (Singleton Instance)
payment_service = PaymentService()
