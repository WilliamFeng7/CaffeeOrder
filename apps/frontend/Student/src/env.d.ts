/// <reference types="vite/client" />

/**
 * 声明 .vue 文件的类型定义
 * 这样 TypeScript 就能识别 .vue 文件是一个 Vue 组件
 */
declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<object, object, any>
    export default component
}
