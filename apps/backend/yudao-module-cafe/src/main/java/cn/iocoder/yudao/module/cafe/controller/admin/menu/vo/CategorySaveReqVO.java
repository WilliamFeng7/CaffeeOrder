package cn.iocoder.yudao.module.cafe.controller.admin.menu.vo;
import lombok.Data;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.*;
@Data public class CategorySaveReqVO {
    private Long id;
    @NotBlank @Pattern(regexp="[a-z][a-z0-9-]{0,29}",message="分类编码只能使用小写字母、数字和连字符") private String code;
    @NotBlank @Size(max=50) private String name;
    @Size(max=100) private String nameEn;
    @NotNull @Min(0) private Integer sort;
}
