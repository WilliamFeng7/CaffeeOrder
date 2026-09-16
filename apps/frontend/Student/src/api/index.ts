import apiClient from '@shared/api-client';
import type { Product, UserProfile, CartItem } from '../types';

// API 基础路径已经在 shared api-client 中配置好了

export const api = {
    /**
     * 用户登录 (User Login)
     */
    async login(username: string, password: string): Promise<any> {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await apiClient.post('/login/access-token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    /**
     * 获取菜单列表 (Get Menu)
     */
    async getMenu(): Promise<Product[]> {
        try {
            const response = await apiClient.get('/menu/');
            const items = response.data;
            return items.map((item: any) => ({
                id: item.id.toString(),
                name: item.name,
                nameCN: item.name_cn || item.name,
                description: item.description || `Freshly prepared ${item.name}`,
                descriptionCN: item.description || `新鲜制作的 ${item.name}`,
                price: item.price / 100,
                category: item.category.toLowerCase(),
                image: item.image_path,
                tags: item.is_recommend ? ['Best Seller'] : [],
                isPopular: item.is_recommend || false,
                inventoryCount: item.inventory_count,
            }));
        } catch (error) {
            console.error('Failed to fetch menu:', error);
            return [];
        }
    },

    /**
     * 获取个人资料 (Get User Profile)
     */
    async getProfile(): Promise<UserProfile & { balance: number; username: string }> {
        const response = await apiClient.get('/users/me');
        const data = response.data;
        return {
            name: data.name || data.username,
            phone: data.phone || '',
            email: data.email || '',
            balance: data.balance / 100, // Cents to Yuan
            username: data.username,
            uuid: data.uuid || 'N/A'
        };
    },

    /**
     * 修改密码 (Update Password)
     */
    async updatePassword(oldPassword: string, newPassword: string): Promise<void> {
        try {
            await apiClient.put('/users/me/password', {
                old_password: oldPassword,
                new_password: newPassword
            });
        } catch (error: any) {
            const err = error.response?.data;
            let msg = err?.detail || 'Password update failed';
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
     */
    async updateProfile(profile: UserProfile): Promise<UserProfile> {
        const response = await apiClient.put('/users/me', {
            name: profile.name,
            phone: profile.phone,
            email: profile.email
        });
        const data = response.data;
        return {
            name: data.name || data.username,
            phone: data.phone || '',
            email: data.email || '',
            uuid: data.uuid || 'N/A',
            avatar: profile.avatar,
            balance: data.balance / 100, // Cents to Yuan
            username: data.username
        };
    },

    /**
     * 创建订单 (Create Order)
     */
    async createOrder(items: CartItem[]) {
        const backendItems = [];
        for (const item of items) {
            for (let i = 0; i < item.quantity; i++) {
                backendItems.push({
                    menu_item_id: parseInt(item.id),
                    spec: {
                        size: item.size || 'Regular',
                        sugar: item.sugar || 'Regular',
                        temp: item.temperature || 'Hot',
                    }
                });
            }
        }

        const response = await apiClient.post('/orders/', { items: backendItems });
        return response.data;
    },

    /**
     * 获取我的历史订单 (Get My Orders)
     */
    async getMyOrders() {
        try {
            const response = await apiClient.get('/orders/me');
            const orders = response.data;
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
                            image: backendItem.image_url, // Added mapping for image
                            quantity: 1,
                            size: backendItem.spec.size,
                            temperature: backendItem.spec.temp,
                            sugar: backendItem.spec.sugar
                        });
                    }
                });

                return {
                    id: o.id.toString(),
                    uuid: o.order_no, // Backend uses order_no as unique public id
                    order_no: o.order_no,
                    date: o.created_at,
                    items: Array.from(itemMap.values()),
                    total: o.total_amount / 100,
                    type: 'dine-in',
                    pickupNumber: o.pickup_number,
                    dailyNumber: o.pickup_number,
                    status: ['completed', 'refunded'].includes(o.status) ? 'completed' : 'active',
                    isCompleted: o.is_completed,
                    pointsEarned: 0
                };
            });
        } catch {
            return [];
        }
    },

    /**
     * Get Shop Status
     */
    async getShopStatus() {
        try {
            const response = await apiClient.get('/shop/status');
            return response.data;
        } catch {
            return { is_open: true };
        }
    }
};

