package cn.iocoder.yudao.module.cafe.controller.admin.menu.vo;
import lombok.Data;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.*;
@Data public class OptionGroupSaveReqVO {
    private Long id;
    @NotBlank @Size(max=50) private String name;
    @Size(max=100) private String nameEn;
    @NotNull @Min(0) private Integer sort;
    @Valid @NotEmpty @Size(max=50) private List<Option> options;
    @Data public static class Option {
        private Long id;
        @NotBlank @Size(max=50) private String name;
        @Size(max=100) private String nameEn;
        @NotNull @Min(0) @Max(1000000) private Integer priceDelta;
        @NotNull private Boolean isDefault;
        @NotNull @Min(0) private Integer sort;
    }
}
