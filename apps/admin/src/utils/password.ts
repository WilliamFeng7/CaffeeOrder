export const PASSWORD_POLICY_MESSAGE = '密码至少 8 位，且必须同时包含字母和数字'

/** Returns true when valid, otherwise the message to show next to the field. */
export function validatePassword(value: string): true | string {
  const password = value ?? ''
  const bytes = new TextEncoder().encode(password).length
  if (password.length < 8 || bytes > 72 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return PASSWORD_POLICY_MESSAGE
  }
  return true
}
