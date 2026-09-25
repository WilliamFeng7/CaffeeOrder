import apiClient from '@shared/api-client';

export interface OrderItem {
    name: string;
    quantity: number;
    temperature?: string;
    sugar?: string;
    size?: string;
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
    items: OrderItem[];
}

/**
 * Map the backend order-item shape onto what OrderCard renders.
 *
 * The API returns snapshot rows: `{ item_name, price_snap, spec: {temp, sugar,
 * size}, quantity }`. OrderCard reads `name / temperature / sugar` and sums
 * `quantity`. Passing the raw rows straight through (the previous behaviour)
 * made every KDS card render a blank product name, and the item count reduce
 * over `undefined` into NaN.
 *
 * Orders are stored one row per unit, so identical lines are folded together
 * here to show "3× Flat White" instead of three separate rows.
 */
function mapOrderItems(raw: unknown[] | undefined): OrderItem[] {
    const grouped = new Map<string, OrderItem>();

    for (const entry of raw ?? []) {
        const item = (entry ?? {}) as Record<string, any>;
        const spec = (item.spec ?? {}) as Record<string, string>;
        const name: string = item.item_name ?? item.name ?? '';
        const temperature: string | undefined = spec.temp ?? spec.temperature;
        const sugar: string | undefined = spec.sugar;
        const size: string | undefined = spec.size;
        const quantity = Number(item.quantity ?? 1) || 1;

        const key = `${name}|${temperature ?? ''}|${sugar ?? ''}|${size ?? ''}`;
        const existing = grouped.get(key);
        if (existing) {
            existing.quantity += quantity;
        } else {
            grouped.set(key, { name, quantity, temperature, sugar, size });
        }
    }

    return [...grouped.values()];
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
    // `signal` lets the polling composable cancel an in-flight request when the
    // next tick starts; without it the AbortController it creates was decorative
    // and a slow response could still overwrite a newer one.
    async getAllOrders(signal?: AbortSignal): Promise<Order[]> {
        const res = await apiClient.get('/admin/orders', { signal });
        return res.data.map((o: any) => ({
            id: o.id,
            user: o.user_id, // Map backend to frontend
            total: o.total_amount / 100,
            status: o.status,
            order_no: o.order_no,
            pickup_number: o.pickup_number,
            created_at: o.created_at,
            items: mapOrderItems(o.items)
        }));
    },

    async updateOrderStatus(id: number, status: string): Promise<Order> {
        const res = await apiClient.put(`/admin/orders/${id}/status?status=${status}`);
        return res.data;
    },

    async syncOrders(since: number = 0, signal?: AbortSignal): Promise<Order[]> {
        const res = await apiClient.get(`/orders/sync?since=${since}`, { signal });
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
            items: mapOrderItems(o.items)
        }));
    }
};
