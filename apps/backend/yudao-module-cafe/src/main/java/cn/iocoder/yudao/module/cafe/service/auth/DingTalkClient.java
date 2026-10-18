package cn.iocoder.yudao.module.cafe.service.auth;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import com.fasterxml.jackson.databind.*;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
/** 企业内部应用免登：官方文档及字段约定见 docs/upstream.md。凭证仅在服务端使用。 */
@Component public class DingTalkClient {
    public record Identity(String userId,String studentNo,String name) {}
    @Resource private CafeProperties properties;
    @Resource private ObjectMapper json;
    private final HttpClient http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private String cachedToken;
    private long tokenExpiresAt;
    public Identity identity(String authCode) {
        var config=properties.getDingtalk();
        if(config.getCorpId().isBlank()||config.getAppKey().isBlank()||config.getAppSecret().isBlank())throw exception(AUTH_FAILED);
        JsonNode info=post("/topapi/v2/user/getuserinfo",Map.of("code",authCode));
        String userId=text(info.path("result"),"userid");
        if(userId.isBlank())throw exception(AUTH_FAILED);
        JsonNode user=post("/topapi/v2/user/get",Map.of("userid",userId)).path("result");
        String studentNo=text(user,config.getStudentNoField());
        String name=text(user,"name");
        if(studentNo.isBlank())throw exception(STUDENT_NO_MISSING);
        if(studentNo.length()>40||userId.length()>100||name.isBlank()||name.length()>80)throw exception(AUTH_FAILED);
        return new Identity(userId,studentNo,name);
    }
    private String text(JsonNode node,String field){return node.path(field).asText("").trim();}
    private synchronized String token() {
        if(cachedToken!=null&&System.currentTimeMillis()<tokenExpiresAt)return cachedToken;
        var config=properties.getDingtalk();
        JsonNode response=send(HttpRequest.newBuilder(URI.create("https://oapi.dingtalk.com/gettoken?appkey="+encode(config.getAppKey())+"&appsecret="+encode(config.getAppSecret()))).GET().timeout(Duration.ofSeconds(10)).build());
        String token=text(response,"access_token");
        if(token.isBlank())throw exception(AUTH_FAILED);
        cachedToken=token;tokenExpiresAt=System.currentTimeMillis()+Math.max(1,response.path("expires_in").asLong(7200)-120)*1000;
        return cachedToken;
    }
    private JsonNode post(String path,Map<String,String> body){
        try {
            return send(HttpRequest.newBuilder(URI.create("https://oapi.dingtalk.com"+path+"?access_token="+encode(token())))
                .timeout(Duration.ofSeconds(10)).header("Content-Type","application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json.writeValueAsString(body))).build());
        } catch(cn.iocoder.yudao.framework.common.exception.ServiceException ex){throw ex;}
          catch(Exception ex){throw exception(AUTH_FAILED);}
    }
    private JsonNode send(HttpRequest request){
        try {
            var response=http.send(request,HttpResponse.BodyHandlers.ofString());
            if(response.statusCode()!=200)throw exception(AUTH_FAILED);
            JsonNode result=json.readTree(response.body());
            if(!result.has("errcode")||result.path("errcode").asInt(-1)!=0)throw exception(AUTH_FAILED);
            return result;
        } catch(InterruptedException ex){Thread.currentThread().interrupt();throw exception(AUTH_FAILED);}
          catch(Exception ex){throw exception(AUTH_FAILED);}
    }
    private static String encode(String value){return URLEncoder.encode(value,StandardCharsets.UTF_8);}
}
