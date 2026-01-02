import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1'; // Direct to backend or via proxy

const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded', // Default for login, but we override for JSON
    },
});

apiClient.interceptors.request.use((config) => {
    const token = sessionStorage.getItem('admin_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

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

export const api = {
    // --- Auth ---
    async login(username: string, password: string) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await apiClient.post('/login/access-token', formData);
        return res.data; // { access_token, token_type }
    },

    // --- Stats ---
    async getDashboardStats(): Promise<DashboardStats> {
        const res = await apiClient.get('/admin/stats');
        return res.data;
    },

    // --- Users ---
    async getUsers() {
        const res = await apiClient.get('/admin/users');
        return res.data.map((u: any) => ({
            ...u,
            balance: u.balance / 100 // Convert cents to Yuan
        }));
    },

    async createUser(data: any) {
        const payload = {
            ...data,
            balance: Math.round(data.balance * 100) // Convert Yuan to Cents
        };
        const res = await apiClient.post('/admin/users', payload, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async updateUser(id: number, data: any) {
        const res = await apiClient.put(`/admin/users/${id}`, data, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async deleteUser(id: number) {
        const res = await apiClient.delete(`/admin/users/${id}`);
        return res.data;
    },

    async deposit(userId: number, amount: number) {
        const res = await apiClient.post(`/users/${userId}/deposit?amount=${amount}`);
        return res.data;
    },

    // --- Products ---
    async getProducts() {
        const res = await apiClient.get('/admin/products');
        return res.data.map((p: any) => ({
            ...p,
            price: p.price / 100, // Cents to Yen
            image: p.image_path // Map backend field to frontend field
        }));
    },

    async createProduct(data: any) {
        const payload = {
            ...data,
            price: Math.round(data.price * 100), // Yen to Cents
            image_path: data.image // Map frontend field to backend field
        };
        delete payload.image; // Remove frontend-only field
        const res = await apiClient.post('/admin/products', payload, {
            headers: { 'Content-Type': 'application/json' }
        });
        return res.data;
    },

    async updateProduct(id: number, product: any) {
        const token = sessionStorage.getItem('admin_token');

        // Prepare payload: map frontend 'image' to backend 'image_path'
        const payload = {
            ...product,
            image_path: product.image,
            price: Math.round(product.price * 100) // Ensure price is in cents
        };
        delete payload.image; // Remove frontend-only field

        const response = await fetch(`${API_BASE}/admin/products/${id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        return await response.json();
    },

    async uploadImage(file: File): Promise<string> {
        const token = sessionStorage.getItem('admin_token'); // Changed from adminToken to admin_token to match interceptor
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        return data.url;
    },

    async deleteProduct(id: number) {
        const res = await apiClient.delete(`/admin/products/${id}`);
        return res.data;
    },

    // --- Orders ---
    async getAllOrders() {
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

    async updateOrderStatus(id: number, status: string) {
        const res = await apiClient.put(`/admin/orders/${id}/status?status=${status}`);
        return res.data;
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
