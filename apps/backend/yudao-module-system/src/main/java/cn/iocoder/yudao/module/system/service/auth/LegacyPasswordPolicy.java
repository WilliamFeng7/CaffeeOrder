package cn.iocoder.yudao.module.system.service.auth;

/** Blocks the public import password left by immutable V1 migrations. */
public final class LegacyPasswordPolicy {

    private static final String LEGACY_SHARED_IMPORT_PASSWORD = "admin123";

    private LegacyPasswordPolicy() {
    }

    public static boolean isLegacySharedImportPassword(String password) {
        return LEGACY_SHARED_IMPORT_PASSWORD.equals(password);
    }
}
