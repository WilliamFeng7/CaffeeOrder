package cn.iocoder.yudao.framework.apilog.core.util;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ArrayUtil;
import cn.hutool.core.util.StrUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** 访问日志统一脱敏；解析失败时放弃原始内容，避免敏感字段绕过 JSON 解析进入日志。 */
public final class ApiAccessLogSanitizer {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final List<String> SENSITIVE_KEYS = List.of(
            "password", "passwd", "token", "accesstoken", "refreshtoken",
            "idtoken", "authorization", "secret", "clientsecret",
            "newpassword", "oldpassword", "confirmpassword", "currentpassword",
            "authcode", "verificationcode", "otp", "pin");

    private ApiAccessLogSanitizer() {
    }

    public static String sanitizeMap(Map<String, ?> map, String[] additionalKeys) {
        if (CollUtil.isEmpty(map)) {
            return null;
        }
        List<String> sensitiveKeys = new ArrayList<>(SENSITIVE_KEYS);
        if (additionalKeys != null) {
            for (String key : additionalKeys) {
                sensitiveKeys.add(normalize(key));
            }
        }
        Map<String, Object> sanitized = new LinkedHashMap<>();
        map.forEach((key, value) -> {
            if (!isSensitive(key, sensitiveKeys)) {
                sanitized.put(key, value);
            }
        });
        try {
            return OBJECT_MAPPER.writeValueAsString(sanitized);
        } catch (Exception ignored) {
            return "\"[unparseable request parameters]\"";
        }
    }

    public static String sanitizeJson(String jsonString, String[] additionalKeys) {
        if (StrUtil.isBlank(jsonString)) {
            return null;
        }
        try {
            JsonNode root = OBJECT_MAPPER.readTree(jsonString);
            sanitizeNode(root, additionalKeys);
            return OBJECT_MAPPER.writeValueAsString(root);
        } catch (Exception ignored) {
            return "\"[unparseable request body]\"";
        }
    }

    public static String sanitizeObject(Object value, String[] additionalKeys) {
        if (value == null) {
            return null;
        }
        try {
            return sanitizeJson(OBJECT_MAPPER.writeValueAsString(value), additionalKeys);
        } catch (Exception ignored) {
            return "\"[unserializable log value]\"";
        }
    }

    private static void sanitizeNode(JsonNode node, String[] additionalKeys) {
        if (node == null) {
            return;
        }
        if (node.isArray()) {
            node.forEach(child -> sanitizeNode(child, additionalKeys));
            return;
        }
        if (!node.isObject()) {
            return;
        }
        ObjectNode object = (ObjectNode) node;
        List<String> fields = new ArrayList<>();
        object.fieldNames().forEachRemaining(fields::add);
        for (String field : fields) {
            if (isSensitive(field, defaultAndAdditionalKeys(additionalKeys))) {
                object.remove(field);
            } else {
                sanitizeNode(object.get(field), additionalKeys);
            }
        }
    }

    private static List<String> defaultAndAdditionalKeys(String[] additionalKeys) {
        List<String> keys = new ArrayList<>(SENSITIVE_KEYS);
        if (ArrayUtil.isNotEmpty(additionalKeys)) {
            for (String key : additionalKeys) {
                keys.add(normalize(key));
            }
        }
        return keys;
    }

    private static boolean isSensitive(String key, List<String> sensitiveKeys) {
        String normalized = normalize(key);
        for (String sensitiveKey : sensitiveKeys) {
            if (sensitiveKey.equals(normalized)) {
                return true;
            }
        }
        return false;
    }

    private static String normalize(String key) {
        return key == null ? "" : key.toLowerCase(Locale.ROOT).replace("_", "").replace("-", "");
    }
}
