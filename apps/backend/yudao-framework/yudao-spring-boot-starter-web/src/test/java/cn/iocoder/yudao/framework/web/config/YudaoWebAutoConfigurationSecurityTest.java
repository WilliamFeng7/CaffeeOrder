package cn.iocoder.yudao.framework.web.config;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

class YudaoWebAutoConfigurationSecurityTest {

    @Test
    void defaultConfigurationRejectsCrossOriginPreflight() throws Exception {
        WebProperties properties = new WebProperties();
        properties.setAdminUi(new WebProperties.Ui());
        MockHttpServletRequest request = preflight("https://evil.example");
        MockHttpServletResponse response = new MockHttpServletResponse();

        new YudaoWebAutoConfiguration().corsFilterBean(properties).getFilter()
                .doFilter(request, response, new MockFilterChain());

        assertEquals(403, response.getStatus());
        assertNull(response.getHeader(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }

    @Test
    void explicitOriginAllowlistEnablesOnlyConfiguredOrigin() throws Exception {
        WebProperties properties = new WebProperties();
        properties.setAdminUi(new WebProperties.Ui());
        properties.getCors().setAllowedOrigins(List.of("https://trusted.example"));
        MockHttpServletRequest request = preflight("https://trusted.example");
        MockHttpServletResponse response = new MockHttpServletResponse();

        new YudaoWebAutoConfiguration().corsFilterBean(properties).getFilter()
                .doFilter(request, response, new MockFilterChain());

        assertEquals(200, response.getStatus());
        assertEquals("https://trusted.example",
                response.getHeader(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }

    @Test
    void commaSeparatedEnvironmentOriginsAreSplit() throws Exception {
        WebProperties properties = new WebProperties();
        properties.setAdminUi(new WebProperties.Ui());
        properties.getCors().setAllowedOrigins(List.of(
                "https://student.example, https://admin.example"));
        MockHttpServletRequest request = preflight("https://admin.example");
        MockHttpServletResponse response = new MockHttpServletResponse();

        new YudaoWebAutoConfiguration().corsFilterBean(properties).getFilter()
                .doFilter(request, response, new MockFilterChain());

        assertEquals(200, response.getStatus());
        assertEquals("https://admin.example",
                response.getHeader(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }

    @Test
    void exactSameOriginRequestIsNotRejectedByEmptyAllowlist() throws Exception {
        WebProperties properties = new WebProperties();
        properties.setAdminUi(new WebProperties.Ui());
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/admin-api/system/auth/login");
        request.setScheme("http");
        request.setServerName("150.158.121.81");
        request.setServerPort(5003);
        request.addHeader(HttpHeaders.ORIGIN, "http://150.158.121.81:5003");
        MockHttpServletResponse response = new MockHttpServletResponse();

        new YudaoWebAutoConfiguration().corsFilterBean(properties).getFilter()
                .doFilter(request, response, new MockFilterChain());

        assertEquals(200, response.getStatus());
        assertNull(response.getHeader(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }

    private MockHttpServletRequest preflight(String origin) {
        MockHttpServletRequest request = new MockHttpServletRequest("OPTIONS", "/admin-api/system/auth/login");
        request.addHeader(HttpHeaders.ORIGIN, origin);
        request.addHeader(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "POST");
        return request;
    }
}
