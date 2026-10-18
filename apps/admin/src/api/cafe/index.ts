import request from '@/config/axios'
export interface Category { id?: number; code: string; name: string; nameEn: string; sort: number }
export interface Option { id?: number; name: string; nameEn: string; priceDelta: number; isDefault: boolean; sort: number }
export interface OptionGroup { id?: number; name: string; nameEn: string; sort: number; options: Option[] }
export interface MenuItem { id?: number; name: string; nameEn: string; description: string; descriptionEn: string; price: number; categoryCode: string; imageUrl: string; recommended: boolean; enabled: boolean; soldOut: boolean; sort: number; groupIds: number[] }
export interface BusinessHour { start: string; end: string }
export interface Shop { open: boolean; banner: string; businessHours: BusinessHour[] }
export interface OrderItem { itemId: number; name: string; nameEn: string; imageUrl: string; quantity: number; unitPrice: number; optionsText: string }
export interface Order { id: number; orderNo: string; studentNo: string; studentName: string; status: number; posOrderNo: string | null; totalPrice: number; cupCount: number; createTime: number; enteredTime: number | null; doneTime: number | null; failureReason: string | null; items: OrderItem[] }
export interface OrderFilter { startDate?: string; endDate?: string; status?: number; student?: string; posOrderNo?: string }
export const categories = () => request.get<Category[]>({ url: '/cafe/category/list' })
export const menuItems = () => request.get<MenuItem[]>({ url: '/cafe/menu-item/list' })
export const optionGroups = () => request.get<OptionGroup[]>({ url: '/cafe/option-group/list' })
const save = (entity: string, data: { id?: number }) => data.id ? request.put({ url: `/cafe/${entity}/update`, data }) : request.post({ url: `/cafe/${entity}/create`, data })
export const saveCategory = (data: Category) => save('category', data)
export const saveItem = (data: MenuItem) => save('menu-item', data)
export const saveGroup = (data: OptionGroup) => save('option-group', data)
export const removeEntity = (entity: string, id: number) => request.delete({ url: `/cafe/${entity}/delete`, params: { id } })
export const shop = () => request.get<Shop>({ url: '/cafe/shop/get' })
export const saveShop = (data: Shop) => request.put({ url: '/cafe/shop/update', data })
export const orders = (params: OrderFilter & { pageNo: number; pageSize: number }) => request.get<{list: Order[]; total: number}>({ url: '/cafe/order/page', params })
export const statistics = (params: OrderFilter) => request.get<{ orderCount: number; totalPrice: number; paidAmount: number }>({ url: '/cafe/order/statistics', params })
export const exportOrders = (params: OrderFilter) => request.download({ url: '/cafe/order/export-excel', params })
export const money = (cents: number) => `¥${((cents || 0) / 100).toFixed(2)}`
export const beijingTime = (timestamp: number | null) => timestamp ? new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(timestamp) : '—'
export const statusLabels: Record<number, string> = { 0: '支付中', 1: '支付失败', 2: '支付中（补偿中）', 10: '待录单', 20: '制作中', 30: '制作完成' }
