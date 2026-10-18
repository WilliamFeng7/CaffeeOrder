package cn.iocoder.yudao.module.cafe.controller.admin.menu.vo;
import lombok.Data;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.*;
@Data public class ShopSaveReqVO {
    @NotNull private Boolean open;
    @Size(max=120,message="公告最多 120 字") private String banner;
    @NotNull @Size(max=10) @Valid private List<Hour> businessHours;
    @Data public static class Hour {
        @NotBlank @Pattern(regexp="(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00",message="营业时段格式应为 HH:mm") private String start;
        @NotBlank @Pattern(regexp="(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00",message="营业时段格式应为 HH:mm") private String end;
    }
}
