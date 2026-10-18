/**
 * yudao 后端的通用请求封装，学生端和咖啡师端共用。
 *
 *   const api = createYudaoClient({
 *     baseUrl: '/app-api/cafe',              // 接口前缀
 *     tokenKey: 'otia.student.accessToken',  // 令牌在存储里的键名
 *     storage: 'localStorage',               // 或 'sessionStorage'
 *     onUnauthorized: () => signInAgain(),   // 令牌失效（已清掉）后调用
 *   });
 *   api.setTokens(await api.post<Tokens>('/auth/dev-login', body, { auth: false }));
 *   const order = await api.post<Order>('/order/create', body, { headers: { 'Idempotency-Key': key } });
 *
 * 成败看返回体 { code, data, msg } 的 code（yudao 出错时 HTTP 状态码通常仍是 200）：code 为 0 返回 data，
 * 否则抛出 YudaoError，它的 msg 可以直接给用户看；断网、超时这类没拿到返回体的情况 code 为 NETWORK_ERROR。
 * code 为 401 时清掉令牌并调用 onUnauthorized；配置了 refresh 的，会先用刷新令牌换一次新令牌、重发请求。
 */

/** 没拿到 yudao 返回体（断网、超时、网关报错）时 YudaoError 的 code。 */
export const NETWORK_ERROR = -1;

export class YudaoError extends Error {
  readonly code: number;
  readonly msg: string;

  constructor(code: number, msg: string) {
    super(msg);
    this.name = 'YudaoError';
    this.code = code;
    this.msg = msg;
  }
}

export interface YudaoTokens {
  accessToken: string;
  refreshToken?: string | null;
}

export interface YudaoClientOptions {
  /** 接口前缀，比如 '/admin-api'、'/app-api/cafe'。 */
  baseUrl: string;
  /** 访问令牌在存储里的键名。 */
  tokenKey: string;
  /** localStorage 在刷新页面、重开浏览器后仍保留；sessionStorage 关掉页面就清空。 */
  storage: 'localStorage' | 'sessionStorage';
  /** 令牌失效时调用，此时令牌已经清掉。 */
  onUnauthorized?: () => void;
  /**
   * yudao 的刷新令牌（可选）。配置后，code 401 时先调 POST {path} 并在请求体提交 refreshToken，再重发一次请求；
   * 换不到才算令牌失效。
   */
  refresh?: { path: string; tokenKey: string };
  /**
   * 没有刷新令牌时的重新登录（可选），例如学生端重新走一次钉钉免登。
   * 成功后用新令牌重放原请求一次；同一时刻的多个 401 共用同一次登录。
   */
  reauthenticate?: () => Promise<YudaoTokens | null>;
  /** 单次请求的超时毫秒数，默认 15000。 */
  timeout?: number;
}

export interface YudaoRequestOptions {
  /** 查询参数，值为 undefined 或 null 的不发送。 */
  params?: Record<string, string | number | boolean | null | undefined>;
  /** 额外的请求头，比如 { 'Idempotency-Key': key }。 */
  headers?: Record<string, string>;
  /** 为 false 时不带令牌，用于登录这类免登录接口。 */
  auth?: boolean;
  /** 调用方取消请求时，抛出浏览器原生的 AbortError。 */
  signal?: AbortSignal;
  /** 覆盖默认超时，毫秒。 */
  timeout?: number;
}

interface Envelope<T> {
  code: number;
  data: T;
  msg: string;
}

export function createYudaoClient(options: YudaoClientOptions) {
  const defaultTimeout = options.timeout ?? 15000;
  const base = options.baseUrl.replace(/\/+$/, '');
  let refreshing: Promise<string | null> | null = null;

  // 隐私模式或禁用存储时，读写可能直接抛错。
  const store = {
    get(key: string): string | null {
      try {
        return window[options.storage].getItem(key);
      } catch {
        return null;
      }
    },
    set(key: string, value: string) {
      try {
        window[options.storage].setItem(key, value);
      } catch {
        // 存不下时只在本次页面里有效。
      }
    },
    remove(key: string) {
      try {
        window[options.storage].removeItem(key);
      } catch {
        // 同上
      }
    },
  };

  const getToken = () => store.get(options.tokenKey);

  function setTokens(tokens: YudaoTokens) {
    store.set(options.tokenKey, tokens.accessToken);
    if (options.refresh && tokens.refreshToken) store.set(options.refresh.tokenKey, tokens.refreshToken);
  }

  function clearTokens() {
    store.remove(options.tokenKey);
    if (options.refresh) store.remove(options.refresh.tokenKey);
  }

  function buildUrl(path: string, params?: YudaoRequestOptions['params']) {
    let url = base + (path.startsWith('/') ? path : `/${path}`);
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value !== undefined && value !== null) query.append(key, String(value));
    }
    const search = query.toString();
    if (search) url += (url.includes('?') ? '&' : '?') + search;
    return url;
  }

  async function send<T>(method: string, path: string, body: unknown, init: YudaoRequestOptions, token: string | null): Promise<Envelope<T>> {
    const headers: Record<string, string> = { Accept: 'application/json', ...init.headers };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers.Authorization = `Bearer ${token}`;

    // 超时和调用方的取消都落到同一个 AbortController 上。
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, init.timeout ?? defaultTimeout);
    const cancel = () => controller.abort();
    if (init.signal?.aborted) controller.abort();
    init.signal?.addEventListener('abort', cancel);

    try {
      let response: Response;
      let payload: unknown;
      try {
        response = await fetch(buildUrl(path, init.params), {
          method,
          headers,
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: controller.signal,
          cache: 'no-store',
        });
        payload = await response.json().catch(() => undefined);
      } catch (error) {
        if (timedOut) throw new YudaoError(NETWORK_ERROR, '服务器响应超时，请稍后重试');
        if (init.signal?.aborted) throw error;
        throw new YudaoError(NETWORK_ERROR, '连不上服务器，请检查网络');
      }
      if (timedOut) throw new YudaoError(NETWORK_ERROR, '服务器响应超时，请稍后重试');
      if (init.signal?.aborted) throw new DOMException('请求已取消', 'AbortError');

      const envelope = payload as Partial<Envelope<T>> | undefined;
      if (typeof envelope?.code !== 'number') {
        throw new YudaoError(
          NETWORK_ERROR,
          response.ok ? '服务器返回的内容无法识别' : `服务器暂时无法访问（HTTP ${response.status}），请稍后重试`,
        );
      }
      return { code: envelope.code, data: envelope.data as T, msg: envelope.msg ?? '' };
    } finally {
      clearTimeout(timer);
      init.signal?.removeEventListener('abort', cancel);
    }
  }

  /** 换新的访问令牌；优先刷新令牌，没有时重新免登。断网时抛错，原令牌保留。 */
  function refreshAfter(usedToken: string | null): Promise<string | null> {
    const refresh = options.refresh;
    if (!refresh && !options.reauthenticate) return Promise.resolve(null);
    const current = getToken();
    if (current && current !== usedToken) return Promise.resolve(current);

    refreshing ??= (async () => {
      try {
        const refreshToken = refresh ? store.get(refresh.tokenKey) : null;
        if (refresh && refreshToken) {
          const result = await send<YudaoTokens>('POST', refresh.path, { refreshToken }, {}, null);
          if (result.code === 0 && result.data?.accessToken) {
            setTokens(result.data);
            return result.data.accessToken;
          }
        }
        if (options.reauthenticate) {
          const tokens = await options.reauthenticate();
          if (tokens?.accessToken) {
            setTokens(tokens);
            return tokens.accessToken;
          }
        }
        return null;
      } finally {
        refreshing = null;
      }
    })();
    return refreshing;
  }

  function expire(usedToken: string | null) {
    // 别的请求已经换了新令牌或重新登录过，就不要清掉新的。
    if (getToken() !== usedToken) return;
    clearTokens();
    options.onUnauthorized?.();
  }

  async function request<T = unknown>(method: string, path: string, body?: unknown, init: YudaoRequestOptions = {}): Promise<T> {
    const useToken = init.auth !== false;
    let token = useToken ? getToken() : null;
    let result = await send<T>(method, path, body, init, token);

    if (result.code === 401 && useToken) {
      const fresh = await refreshAfter(token);
      if (fresh) {
        token = fresh;
        result = await send<T>(method, path, body, init, token);
      }
      if (result.code === 401) {
        expire(token);
        throw new YudaoError(401, result.msg || '登录已失效，请重新登录');
      }
    }

    if (result.code !== 0) throw new YudaoError(result.code, result.msg || `请求失败（${result.code}）`);
    return result.data;
  }

  return {
    request,
    get: <T = unknown>(path: string, init?: YudaoRequestOptions) => request<T>('GET', path, undefined, init),
    post: <T = unknown>(path: string, body?: unknown, init?: YudaoRequestOptions) => request<T>('POST', path, body, init),
    put: <T = unknown>(path: string, body?: unknown, init?: YudaoRequestOptions) => request<T>('PUT', path, body, init),
    delete: <T = unknown>(path: string, init?: YudaoRequestOptions) => request<T>('DELETE', path, undefined, init),
    getToken,
    setTokens,
    clearTokens,
  };
}

export type YudaoClient = ReturnType<typeof createYudaoClient>;
