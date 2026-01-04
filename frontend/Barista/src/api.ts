import apiClient from '@shared/api-client';

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
        // Use URLSearchParams for OAuth2 form data
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        params.append('grant_type', 'password');

        // Explicitly override Content-Type to x-www-form-urlencoded
        const res = await apiClient.post('/login/access-token', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        return res.data;
    },

    // --- Orders ---
    async getAllOrders(): Promise<Order[]> {
        const res = await apiClient.get('/admin/orders');
        return res.data.map((o: any) => ({
            id: o.id,
            user: o.user_id, // Map backend to frontend
            total: o.total_amount / 100,
            status: o.status,
            order_no: o.order_no,
            pickup_number: o.pickup_number,
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
    }
};
