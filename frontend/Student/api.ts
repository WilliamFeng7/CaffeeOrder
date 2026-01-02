/**
 * api.ts
 * 
 * 后端 API 交互服务 (Backend API Service).
 * 
 * 主要功能 (Core Features):
 * 1. 认证 (Authentication): 处理用户登录 (login)，获取 Token。
 * 2. 菜单数据 (Menu Data): 从后端获取最新菜单列表 (getMenu)，并转换为前端模型。
 * 3. 个人中心 (Profile): 获取和更新用户信息 (getProfile, updateProfile)，修改密码 (updatePassword)。
 * 4. 订单流程 (Order Flow): 创建订单 (createOrder)，获取历史订单 (getMyOrders)。
 */

import type { Product, Order, UserProfile, CartItem } from './types';
import { PRODUCTS } from './data';

// ... (existing code)



// API 基础路径 (需与 `vite.config.ts` 中的 proxy 配置匹配)
const API_BASE = '/api/v1';

export const api = {
    /**
     * 用户登录 (User Login)
     * 发送用户名和密码，获取 OAuth2 Access Token。
     * @param username 用户名
     * @param password 密码
     * @returns Promise<string> 返回 access_token
     */
    async login(username: string, password: string): Promise<any> {
        // 构建 OAuth2 标准表单数据
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/login/access-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const error = new Error('Login failed');
            (error as any).response = { data: errorData };
            (error as any).status = response.status;
            throw error;
        }

        const data = await response.json();
        return data;
    },

    /**
     * 获取菜单列表 (Get Menu)
     * 1. 调用 GET /menu/ 获取后端商品数据。
     * 2. 将后端数据模型转换为前端 Product 接口格式。
     * 3. 处理价格转换 (分 -> 元) 和图片路径。
     */
    async getMenu(): Promise<Product[]> {
        const token = sessionStorage.getItem('token');
        const headers: HeadersInit = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`; // 携带 Token (如有)
        }

        const response = await fetch(`${API_BASE}/menu/`, {
            headers
        });

        if (!response.ok) {
            console.error('Failed to fetch menu, using backup data');
            return [];
        }

        const items = await response.json();
        // 数据转换映射
        return items.map((item: any) => ({
            id: item.id.toString(),
            name: item.name,
            nameCN: item.name_cn || item.name, // 使用后端返回的中文名，若无则用英文名
            description: item.description || `Freshly prepared ${item.name}`,
            descriptionCN: item.description || `新鲜制作的 ${item.name}`,
            price: item.price / 100, // 价格单位转换: 分 -> 元
            category: item.category.toLowerCase(),
            image: item.image_path.startsWith('http') ? item.image_path : item.image_path,
            tags: item.is_recommend ? ['Best Seller'] : [],
            isPopular: item.is_recommend || false, // 映射后端的 is_recommend 到前端的 isPopular
            inventoryCount: item.inventory_count,
        }));
    },

    /**
     * 获取个人资料 (Get User Profile)
     * 调用 GET /users/me
     */
    async getProfile(): Promise<UserProfile & { balance: number; username: string }> {
        const token = sessionStorage.getItem('token');
        const response = await fetch(`${API_BASE}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        return {
            name: data.name || data.username,
            phone: data.phone || '',
            email: data.email || '',
            balance: data.balance,
            username: data.username,
            uuid: data.uuid || 'N/A'
        };
    },

    /**
     * 修改密码 (Update Password)
     * 调用 PUT /users/me/password
     */
    async updatePassword(oldPassword: string, newPassword: string): Promise<void> {
        const token = sessionStorage.getItem('token');
        const response = await fetch(`${API_BASE}/users/me/password`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        if (!response.ok) {
            const err = await response.json();
            let msg = err.detail || 'Password update failed';
            // 处理 Pydantic 验证错误 (数组格式)
            if (typeof msg !== 'string' && Array.isArray(msg) && msg[0]?.msg) {
                msg = msg[0].msg.replace('Value error, ', '');
            } else if (typeof msg !== 'string') {
                msg = JSON.stringify(msg);
            }
            throw new Error(msg);
        }
    },

    /**
     * 更新个人资料 (Update User Profile)
     * 用于修改昵称、电话、邮箱等。
     */
    async updateProfile(profile: UserProfile): Promise<UserProfile> {
        const token = sessionStorage.getItem('token');
        const response = await fetch(`${API_BASE}/users/me`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: profile.name,
                phone: profile.phone,
                email: profile.email
            })
        });
        if (!response.ok) throw new Error('Failed to update profile');
        const data = await response.json();
        return {
            name: data.name || data.username,
            phone: data.phone || '',
            email: data.email || '',
            uuid: data.uuid || 'N/A',
            avatar: profile.avatar,
            balance: data.balance,
            username: data.username
        };
    },

    /**
     * 创建订单 (Create Order)
     * 将前端购物车数据转换为后端 OrderCreateSchema 格式。
     * 包括将商品规格 (Size, Sugar, Temp) 序列化。
     */
    async createOrder(items: CartItem[]) {
        const token = sessionStorage.getItem('token');
        const backendItems = [];
        // 展平购物车项 (处理 quantity > 1 的情况)
        for (const item of items) {
            for (let i = 0; i < item.quantity; i++) {
                backendItems.push({
                    menu_item_id: parseInt(item.id),
                    // 规格参数 JSON 序列化
                    spec: {
                        size: item.size || 'Regular',
                        sugar: item.sugar || 'Regular',
                        temp: item.temperature || 'Hot',

                    }
                });
            }
        }

        const response = await fetch(`${API_BASE}/orders/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: backendItems })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Order failed');
        }
        return await response.json();
    },

    /**
     * 获取我的历史订单 (Get My Orders)
     * 调用 GET /orders/me
     * 并将后端扁平化的 OrderItem 聚合为前端可展示的 CartItem (按规格合并数量)。
     */
    async getMyOrders() {
        // ... (existing implementation)
        const token = sessionStorage.getItem('token');
        const response = await fetch(`${API_BASE}/orders/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) return [];

        const orders = await response.json();
        return orders.map((o: any) => {
            const itemMap = new Map<string, any>();

            o.items.forEach((backendItem: any) => {
                const specKey = JSON.stringify(backendItem.spec);
                const key = `${backendItem.item_name}-${specKey}`;

                if (itemMap.has(key)) {
                    itemMap.get(key).quantity += 1;
                } else {
                    itemMap.set(key, {
                        id: 'backend-item',
                        name: backendItem.item_name,
                        nameCN: backendItem.item_name,
                        price: backendItem.price_snap / 100,
                        quantity: 1,
                        size: backendItem.spec.size,
                        temperature: backendItem.spec.temp,
                        sugar: backendItem.spec.sugar
                    });
                }
            });

            return {
                id: o.id.toString(),
                uuid: o.uuid,
                date: o.created_at,
                items: Array.from(itemMap.values()),
                total: o.total_amount / 100,
                type: 'dine-in',
                pickupNumber: o.pickup_code,
                dailyNumber: o.pickup_number,
                status: ['completed', 'refunded'].includes(o.status) ? 'completed' : 'active',
                isCompleted: o.is_completed,
                pointsEarned: 0
            };
        });
    },



    /**
     * Get Shop Status
     */
    async getShopStatus() {
        try {
            const response = await fetch(`${API_BASE}/shop/status`); // Assuming this endpoint exists, or fallback
            if (!response.ok) return { is_open: true }; // Default open if failed
            return await response.json();
        } catch {
            return { is_open: true };
        }
    }
};

