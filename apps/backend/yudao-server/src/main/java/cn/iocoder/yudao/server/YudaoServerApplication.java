package cn.iocoder.yudao.server;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import java.util.TimeZone;
@SpringBootApplication(scanBasePackages={"cn.iocoder.yudao.server","cn.iocoder.yudao.module"})
public class YudaoServerApplication {
    public static void main(String[] args) {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Shanghai"));
        SpringApplication.run(YudaoServerApplication.class,args);
    }
}
