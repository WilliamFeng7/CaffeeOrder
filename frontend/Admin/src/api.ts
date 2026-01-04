import apiClient from '@shared/api-client';

export interface DashboardStats {
    overview: {
        total_revenue_today: number;
        revenue_growth: number;
        total_orders_today: number;
        orders_growth: number;
        aov_today: number;
        new_members_today: number;
        pending_orders_count: number;
    };
    operations: {
        funnel: {
            pending: number;
            processing: number;
            ready: number;
            completed: number;
            cancelled: number;
        };
        estimated_wait_minutes: number;
        trend: Array<{ hour: string; orders: number; revenue: number }>;
    };
    inventory: {
        top_selling_items: Array<{ name: string; sales: number }>;
        sold_out_items: Array<{ name: string; category: string }>;
    };
}

export interface User {
    id: number;
    username: string;
    uuid: string;
    name?: string;
    phone?: string;
    email?: string;
    role: string;
    balance: number;
    password?: string;
}

export interface Product {
    id: number;
    name: string;
    name_cn?: string;
    description?: string;
    price: number;
    category: string;
    image: string;
    is_active: boolean;
    is_recommend: boolean;
    inventory_count: number;
}

export interface Order {
    id: number;
    user: number;
    user_id?: number; // Compat
    order_no?: string;
    pickup_number?: number;
    total: number;
    status: string;
    created_at: string;
    updated_at?: string;
    items: any[];
}

export const api = {
    // --- Auth ---
    async login(username: string, password: string) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await apiClient.post('/login/access-token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return res.data; // { access_token, token_type }
    },

    // --- Stats ---
    async getDashboardStats(): Promise<DashboardStats> {
        const res = await apiClient.get('/admin/stats');
        return res.data;
    },

    // --- Users ---
    async getUsers(): Promise<User[]> {
        const res = await apiClient.get('/admin/users');
        return res.data;
    },

    async createUser(data: Partial<User>): Promise<User> {
        const res = await apiClient.post('/admin/users', data, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async updateUser(id: number, data: any) {
        // If balance is present, convert Yuan to Cents
        const payload = { ...data };
        if (payload.balance !== undefined) {
            payload.balance = Math.round(payload.balance * 100);
        }

        const res = await apiClient.put(`/admin/users/${id}`, payload, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async deleteUser(id: number): Promise<{ ok: boolean }> {
        const res = await apiClient.delete(`/admin/users/${id}`);
        return res.data;
    },

    async deposit(userId: number, amount: number) {
        // Convert Yuan to Cents
        const amountInCents = Math.round(amount * 100);
        const res = await apiClient.post(`/users/${userId}/deposit?amount=${amountInCents}`);
        return res.data;
    },

    // --- Products ---
    async getProducts(): Promise<Product[]> {
        const res = await apiClient.get('/admin/products');
        return res.data.map((p: any) => ({
            ...p,
            price: p.price / 100, // Cents to Yen
            image: p.image_path // Map backend field to frontend field
        }));
    },

    async createProduct(data: Partial<Product>) {
        const payload = {
            ...data,
            price: Math.round((data.price || 0) * 100), // Yen to Cents
            image_path: data.image // Map frontend field to backend field
        };
        delete (payload as any).image; // Remove frontend-only field
        const res = await apiClient.post('/admin/products', payload, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async updateProduct(id: number, product: Partial<Product>) {
        // Prepare payload: map frontend 'image' to backend 'image_path'
        const payload = {
            ...product,
            image_path: product.image,
            price: Math.round((product.price || 0) * 100) // Ensure price is in cents
        };
        delete (payload as any).image; // Remove frontend-only field

        const res = await apiClient.put(`/admin/products/${id}`, payload, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async uploadImage(file: File): Promise<string> {
        const formData = new FormData();
        formData.append('file', file);

        const res = await apiClient.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return res.data.url;
    },

    async deleteProduct(id: number) {
        const res = await apiClient.delete(`/admin/products/${id}`);
        return res.data;
    },

    // --- Orders ---
    async getAllOrders(): Promise<Order[]> {
        const res = await apiClient.get('/admin/orders');
        return res.data.map((o: any) => ({
            id: o.id,
            user: o.user_id,
            total: o.total_amount / 100,
            status: o.status,
            created_at: o.created_at,
            items: o.items // Pass items for detailed view
        }));
    },

    async updateOrderStatus(id: number, status: string): Promise<Order> {
        const res = await apiClient.put(`/admin/orders/${id}/status?status=${status}`);
        return res.data;
    },

    async syncOrders(since: number = 0): Promise<Order[]> {
        const res = await apiClient.get(`/orders/sync?since=${since}`);
        return res.data.map((o: any) => ({
            id: o.id,
            order_no: o.order_no,
            user: o.user_id, // Map for compat
            user_id: o.user_id,
            pickup_number: o.pickup_number,
            total: o.total_amount / 100,
            status: o.status,
            created_at: o.created_at,
            updated_at: o.updated_at,
            items: o.items
        }));
    },



    // --- Settings ---
    async getSettings() {
        const res = await apiClient.get('/settings/');
        return res.data;
    },

    async updateSetting(key: string, value: string) {
        const res = await apiClient.put(`/settings/${key}`, { value });
        return res.data;
    },

    // --- Finance ---
    async getFinanceStats() {
        const res = await apiClient.get('/finance/stats');
        return res.data;
    },

    async getFinanceChart(days: number = 7) {
        const res = await apiClient.get(`/finance/chart?days=${days}`);
        return res.data;
    },

    async getFinanceTransactions(page: number = 1, type: string = 'order') {
        const skip = (page - 1) * 20;
        const res = await apiClient.get(`/finance/transactions?skip=${skip}&limit=20&type=${type}`);
        return res.data;
    }
};
