package cn.iocoder.yudao.framework.web.core.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.web.filter.CorsFilter;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.net.URI;
import java.util.Locale;

/**
 * Lets requests whose Origin exactly matches the effective request origin
 * continue without treating them as cross-origin requests. Foreign origins
 * still pass through the configured allowlist.
 */
public class SameOriginAwareCorsFilter extends OncePerRequestFilter {

    private final CorsFilter corsFilter;

    public SameOriginAwareCorsFilter(CorsFilter corsFilter) {
        this.corsFilter = corsFilter;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        if (isSameOrigin(request)) {
            filterChain.doFilter(request, response);
            return;
        }
        corsFilter.doFilter(request, response, filterChain);
    }

    static boolean isSameOrigin(HttpServletRequest request) {
        String origin = request.getHeader(HttpHeaders.ORIGIN);
        if (origin == null || origin.isBlank()) {
            return false;
        }
        try {
            URI uri = URI.create(origin);
            if (uri.getHost() == null || uri.getRawUserInfo() != null
                    || (uri.getPath() != null && !uri.getPath().isEmpty() && !"/".equals(uri.getPath()))
                    || uri.getQuery() != null || uri.getFragment() != null) {
                return false;
            }
            String originScheme = uri.getScheme();
            if (originScheme == null) {
                return false;
            }
            return originScheme.equalsIgnoreCase(request.getScheme())
                    && uri.getHost().equalsIgnoreCase(request.getServerName())
                    && effectivePort(originScheme, uri.getPort())
                    == effectivePort(request.getScheme(), request.getServerPort());
        } catch (IllegalArgumentException ex) {
            return false;
        }
    }

    private static int effectivePort(String scheme, int port) {
        if (port > 0) {
            return port;
        }
        return "https".equalsIgnoreCase(scheme) ? 443 : 80;
    }
}
