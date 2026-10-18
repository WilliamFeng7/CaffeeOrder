package cn.iocoder.yudao.module.cafe.controller.admin.menu.vo;
import lombok.Data;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.*;
@Data public class MenuItemSaveReqVO {
    private Long id;
    @NotBlank @Size(max=100) private String name;
    @Size(max=100) private String nameEn;
    @Size(max=1000) private String description;
    @Size(max=1000) private String descriptionEn;
    @NotNull @Min(0) @Max(1000000) private Integer price;
    @NotBlank private String categoryCode;
    @NotBlank @Size(max=1000) @Pattern(regexp="(?:/[^/].*|https?://.+)",message="图片地址必须是站内路径或 HTTP 地址") private String imageUrl;
    @NotNull private Boolean recommended;
    @NotNull private Boolean enabled;
    @NotNull private Boolean soldOut;
    @NotNull @Min(0) private Integer sort;
    @NotNull @Size(max=10) private List<@NotNull Long> groupIds;
}
