package cn.iocoder.yudao.framework.security.core.util;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

class SecurityFrameworkUtilsTest {

    @Test
    void headerOnlyAuthenticationRejectsQueryToken() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setParameter("token", "query-token");

        assertNull(SecurityFrameworkUtils.obtainAuthorization(request, "Authorization", ""));
    }

    @Test
    void headerWinsWhenLegacyParameterIsExplicitlyEnabled() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer header-token");
        request.setParameter("token", "query-token");

        assertEquals("header-token",
                SecurityFrameworkUtils.obtainAuthorization(request, "Authorization", "token"));
    }
}
