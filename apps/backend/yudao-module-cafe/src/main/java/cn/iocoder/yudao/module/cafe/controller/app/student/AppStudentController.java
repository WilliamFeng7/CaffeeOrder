package cn.iocoder.yudao.module.cafe.controller.app.student;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.service.auth.StudentAuthService;
import cn.iocoder.yudao.module.cafe.service.card.StudentCardClient;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
import static cn.iocoder.yudao.framework.security.core.util.SecurityFrameworkUtils.getLoginUserId;
@RestController @RequestMapping("/cafe/student") public class AppStudentController {
    @Resource private StudentAuthService students;
    @Resource private StudentCardClient cards;
    @GetMapping("/me") public CommonResult<Map<String,Object>> me(){var student=students.getStudent(getLoginUserId());return success(Map.of("studentNo",student.getStudentNo(),"name",student.getName(),"balance",balance(student.getStudentNo())));}
    private int balance(String studentNo){
        try{return cards.balance(studentNo);}catch(Exception ex){throw cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception(cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.CARD_UNAVAILABLE);}
    }
}
