package cn.iocoder.yudao.framework.common.util.validation;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class PasswordPolicyUtilsTest {

    @Test
    void acceptsSimpleLetterAndDigitPassword() {
        assertTrue(PasswordPolicyUtils.isValid("admin123"));
        assertTrue(PasswordPolicyUtils.isValid("student123"));
    }

    @Test
    void rejectsShortOrSingleCharacterClassPasswords() {
        assertFalse(PasswordPolicyUtils.isValid("pass12"));
        assertFalse(PasswordPolicyUtils.isValid("password"));
        assertFalse(PasswordPolicyUtils.isValid("12345678"));
        assertFalse(PasswordPolicyUtils.isValid(null));
    }
}
