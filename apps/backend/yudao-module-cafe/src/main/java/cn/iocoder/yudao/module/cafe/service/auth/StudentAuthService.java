package cn.iocoder.yudao.module.cafe.service.auth;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.AuthLoginRespVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
public interface StudentAuthService {
    AuthLoginRespVO dingTalkLogin(String authCode);
    AuthLoginRespVO passwordLogin(String studentNo, String password);
    AuthLoginRespVO devLogin(String studentNo,String name);
    StudentDO getStudent(Long id);
}
