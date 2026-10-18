package cn.iocoder.yudao.framework.apilog.core.util;

import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApiAccessLogSanitizerTest {

    @Test
    void removesPasswordsAndTokensAtEveryJsonDepth() {
        String sanitized = ApiAccessLogSanitizer.sanitizeJson("""
                {
                  "studentNo": "S2026001",
                  "password": "secret-one",
                  "newPassword": "secret-four",
                  "authCode": "secret-five",
                  "nested": {
                    "access_token": "secret-two",
                    "profile": {"name": "Student", "refreshToken": "secret-three"}
                  }
                }
                """, null);

        assertTrue(sanitized.contains("S2026001"));
        assertTrue(sanitized.contains("Student"));
        assertFalse(sanitized.contains("secret-one"));
        assertFalse(sanitized.contains("secret-two"));
        assertFalse(sanitized.contains("secret-three"));
        assertFalse(sanitized.contains("secret-four"));
        assertFalse(sanitized.contains("secret-five"));
        assertFalse(sanitized.contains("password"));
        assertFalse(sanitized.contains("access_token"));
    }

    @Test
    void queryValuesAreSanitizedWithoutMutatingTheInput() {
        Map<String, String> query = new LinkedHashMap<>();
        query.put("studentNo", "S2026001");
        query.put("Password", "secret");
        query.put("refresh-token", "secret");

        String sanitized = ApiAccessLogSanitizer.sanitizeMap(query, null);

        assertEquals("{\"studentNo\":\"S2026001\"}", sanitized);
        assertEquals("secret", query.get("Password"));
    }

    @Test
    void unparseableBodiesNeverFallBackToRawContent() {
        String sanitized = ApiAccessLogSanitizer.sanitizeJson(
                "{\"password\":\"secret\", malformed", null);

        assertEquals("\"[unparseable request body]\"", sanitized);
        assertFalse(sanitized.contains("secret"));
    }
}
