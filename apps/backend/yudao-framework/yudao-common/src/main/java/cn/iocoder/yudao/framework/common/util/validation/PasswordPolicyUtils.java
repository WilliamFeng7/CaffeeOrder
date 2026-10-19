package cn.iocoder.yudao.framework.common.util.validation;

import java.nio.charset.StandardCharsets;

/**
 * Shared password policy for staff and bootstrap test accounts.
 * Passwords contain at least eight characters and include letters and digits.
 */
public final class PasswordPolicyUtils {

    public static final int MIN_LENGTH = 8;
    public static final int MAX_BYTES = 72;
    public static final String MESSAGE = "密码至少 8 位，且必须同时包含字母和数字";

    private PasswordPolicyUtils() {
    }

    public static boolean isValid(String password) {
        if (password == null || password.length() < MIN_LENGTH
                || password.getBytes(StandardCharsets.UTF_8).length > MAX_BYTES) {
            return false;
        }
        boolean hasLetter = false;
        boolean hasDigit = false;
        for (int index = 0; index < password.length(); index++) {
            char value = password.charAt(index);
            hasLetter |= Character.isLetter(value);
            hasDigit |= Character.isDigit(value);
        }
        return hasLetter && hasDigit;
    }
}
