import request from '@/config/axios'
import type { UserLoginVO } from './types'
export const login = (data: UserLoginVO) => request.post({ url: '/system/auth/login', data })
export const loginOut = () => request.post({ url: '/system/auth/logout' })
export const getInfo = () => request.get({ url: '/system/auth/get-permission-info' })
