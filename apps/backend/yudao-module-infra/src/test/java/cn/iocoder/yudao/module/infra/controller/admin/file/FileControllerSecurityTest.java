package cn.iocoder.yudao.module.infra.controller.admin.file;

import cn.iocoder.yudao.module.infra.controller.admin.file.vo.file.FileCreateReqVO;
import org.junit.jupiter.api.Test;
import org.springframework.security.access.prepost.PreAuthorize;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class FileControllerSecurityTest {

    @Test
    void everyAlternateUploadEntryRequiresUploadPermission() throws Exception {
        assertPermission("getFilePresignedUrl", String.class, String.class);
        assertPermission("createFile", FileCreateReqVO.class);
    }

    private void assertPermission(String method, Class<?>... parameterTypes) throws Exception {
        PreAuthorize annotation = FileController.class.getMethod(method, parameterTypes)
                .getAnnotation(PreAuthorize.class);
        assertNotNull(annotation, method + " must require upload permission");
        assertEquals("@ss.hasPermission('infra:file:upload')", annotation.value());
    }
}
