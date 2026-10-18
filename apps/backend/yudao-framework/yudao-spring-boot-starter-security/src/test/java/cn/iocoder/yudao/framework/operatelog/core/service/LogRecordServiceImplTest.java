package cn.iocoder.yudao.framework.operatelog.core.service;

import cn.iocoder.yudao.framework.common.biz.system.logger.OperateLogCommonApi;
import cn.iocoder.yudao.framework.common.biz.system.logger.dto.OperateLogCreateReqDTO;
import com.mzt.logapi.beans.LogRecord;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class LogRecordServiceImplTest {

    @Test
    void systemOperationGetsNonEmptyAuditIdentity() {
        CapturingApi api = new CapturingApi();
        LogRecordServiceImpl service = new LogRecordServiceImpl();
        ReflectionTestUtils.setField(service, "operateLogApi", api);

        LogRecord record = new LogRecord();
        record.setType("SYSTEM 用户");
        record.setSubType("重置用户密码");
        record.setBizNo("1");
        record.setAction("初始化学校管理员密码");
        service.record(record);

        OperateLogCreateReqDTO request = api.request;
        assertNotNull(request);
        assertEquals(0L, request.getUserId());
        assertEquals(0, request.getUserType());
        assertFalse(request.getRequestMethod().isBlank());
        assertFalse(request.getRequestUrl().isBlank());
        assertFalse(request.getUserIp().isBlank());
        assertFalse(request.getUserAgent().isBlank());
    }

    private static final class CapturingApi implements OperateLogCommonApi {

        private OperateLogCreateReqDTO request;

        @Override
        public void createOperateLog(OperateLogCreateReqDTO createReqDTO) {
            request = createReqDTO;
        }
    }
}
