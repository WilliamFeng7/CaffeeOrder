package cn.iocoder.yudao.module.cafe.controller.app.menu.vo;
import lombok.Data;
import java.util.List;
@Data public class MenuRespVO {
    private List<Category> categories;
    private List<Item> items;
    @Data public static class Category { private Long id; private String code; private String name; private String nameEn; private Integer sort; }
    @Data public static class Item {
        private Long id; private String name; private String nameEn; private String description; private String descriptionEn;
        private Integer price; private String categoryCode; private String imageUrl; private Boolean recommended;
        private Boolean soldOut; private Integer sort; private Boolean enabled;
        private List<Group> optionGroups; private List<Long> groupIds;
    }
    @Data public static class Group { private Long id; private String name; private String nameEn; private Integer sort; private List<Option> options; }
    @Data public static class Option { private Long id; private String name; private String nameEn; private Integer priceDelta; private Boolean isDefault; private Integer sort; }
}
