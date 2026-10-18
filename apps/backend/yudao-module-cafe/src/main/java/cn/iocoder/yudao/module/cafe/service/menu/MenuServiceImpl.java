package cn.iocoder.yudao.module.cafe.service.menu;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.*;
import cn.iocoder.yudao.module.cafe.dal.dataobject.*;
import cn.iocoder.yudao.module.cafe.dal.mysql.*;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import jakarta.annotation.Resource;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
@Service("cafeMenuService") public class MenuServiceImpl implements MenuService {
    @Resource private CategoryMapper categories;
    @Resource private MenuItemMapper items;
    @Resource private OptionGroupMapper groups;
    @Resource private OptionMapper options;
    @Resource private ItemGroupMapper itemGroups;
    public MenuRespVO getMenu(boolean includeDisabled) {
        MenuRespVO result=new MenuRespVO();
        result.setCategories(BeanUtils.toBean(categories.selectList(new LambdaQueryWrapper<CategoryDO>().orderByAsc(CategoryDO::getSort,CategoryDO::getId)),MenuRespVO.Category.class));
        Map<Long,MenuRespVO.Group> groupMap=new LinkedHashMap<>();
        getGroups().forEach(group->groupMap.put(group.getId(),group));
        Map<Long,List<Long>> bindings=new HashMap<>();
        itemGroups.selectList().forEach(binding->bindings.computeIfAbsent(binding.getItemId(),key->new ArrayList<>()).add(binding.getGroupId()));
        List<MenuItemDO> rows=items.selectList(new LambdaQueryWrapper<MenuItemDO>().eq(!includeDisabled,MenuItemDO::getEnabled,true).orderByAsc(MenuItemDO::getSort,MenuItemDO::getId));
        result.setItems(rows.stream().map(row->{
            MenuRespVO.Item item=BeanUtils.toBean(row,MenuRespVO.Item.class);
            var selected=bindings.getOrDefault(row.getId(),List.of()).stream().map(groupMap::get).filter(Objects::nonNull)
                .sorted(Comparator.comparing(MenuRespVO.Group::getSort).thenComparing(MenuRespVO.Group::getId)).toList();
            item.setOptionGroups(selected); item.setGroupIds(selected.stream().map(MenuRespVO.Group::getId).toList()); return item;
        }).toList());
        return result;
    }
    public List<MenuRespVO.Group> getGroups() {
        Map<Long,List<MenuRespVO.Option>> byGroup=new HashMap<>();
        options.selectList(new LambdaQueryWrapper<OptionDO>().orderByAsc(OptionDO::getSort,OptionDO::getId)).forEach(option->
            byGroup.computeIfAbsent(option.getGroupId(),id->new ArrayList<>()).add(BeanUtils.toBean(option,MenuRespVO.Option.class)));
        return groups.selectList(new LambdaQueryWrapper<OptionGroupDO>().orderByAsc(OptionGroupDO::getSort,OptionGroupDO::getId)).stream().map(row->{
            MenuRespVO.Group group=BeanUtils.toBean(row,MenuRespVO.Group.class); group.setOptions(byGroup.getOrDefault(row.getId(),List.of()));return group;
        }).toList();
    }
    @Transactional(rollbackFor=Exception.class)
    public Long saveCategory(CategorySaveReqVO request) {
        CategoryDO row=BeanUtils.toBean(request,CategoryDO.class);
        if(row.getId()!=null){
            CategoryDO old=categories.selectOne(new LambdaQueryWrapper<CategoryDO>().eq(CategoryDO::getId,row.getId()).last("FOR UPDATE"));
            if(old==null)throw exception(MENU_NOT_FOUND);
            if(!old.getCode().equals(row.getCode()))throw new IllegalArgumentException("分类编码创建后不能修改");
        }
        try {if(row.getId()==null)categories.insert(row);else categories.updateById(row);}
        catch(DuplicateKeyException ex){throw exception(MENU_DUPLICATE);}
        return row.getId();
    }
    @Transactional(rollbackFor=Exception.class)
    public void deleteCategory(Long id) {
        CategoryDO category=categories.selectOne(new LambdaQueryWrapper<CategoryDO>().eq(CategoryDO::getId,id).last("FOR UPDATE"));if(category==null)throw exception(MENU_NOT_FOUND);
        if(items.selectCount(new LambdaQueryWrapper<MenuItemDO>().eq(MenuItemDO::getCategoryCode,category.getCode()))>0)throw exception(MENU_IN_USE);
        categories.deleteById(id);
    }
    @Transactional(rollbackFor=Exception.class)
    public Long saveItem(MenuItemSaveReqVO request) {
        if(categories.selectOne(new LambdaQueryWrapper<CategoryDO>().eq(CategoryDO::getCode,request.getCategoryCode()).last("FOR UPDATE"))==null)throw exception(MENU_NOT_FOUND);
        if(new HashSet<>(request.getGroupIds()).size()!=request.getGroupIds().size())throw exception(MENU_INVALID);
        for(Long id:request.getGroupIds().stream().sorted().toList())if(groups.selectOne(new LambdaQueryWrapper<OptionGroupDO>().eq(OptionGroupDO::getId,id).last("FOR UPDATE"))==null)throw exception(MENU_NOT_FOUND);
        MenuItemDO row=BeanUtils.toBean(request,MenuItemDO.class);
        if(row.getId()!=null&&items.selectById(row.getId())==null)throw exception(MENU_NOT_FOUND);
        if(row.getId()==null)items.insert(row);else items.updateById(row);
        itemGroups.delete(new LambdaQueryWrapper<ItemGroupDO>().eq(ItemGroupDO::getItemId,row.getId()));
        for(Long groupId:request.getGroupIds()){
            ItemGroupDO binding=new ItemGroupDO();binding.setItemId(row.getId());binding.setGroupId(groupId);itemGroups.insert(binding);
        }
        return row.getId();
    }
    @Transactional(rollbackFor=Exception.class)
    public void deleteItem(Long id) {
        if(items.selectById(id)==null)throw exception(MENU_NOT_FOUND);
        items.deleteById(id);itemGroups.delete(new LambdaQueryWrapper<ItemGroupDO>().eq(ItemGroupDO::getItemId,id));
    }
    @Transactional(rollbackFor=Exception.class)
    public Long saveGroup(OptionGroupSaveReqVO request) {
        if(request.getOptions().stream().filter(o->Boolean.TRUE.equals(o.getIsDefault())).count()!=1)
            throw new IllegalArgumentException("每个规格组需要且只能有一个默认选项");
        if(request.getOptions().stream().map(OptionGroupSaveReqVO.Option::getName).distinct().count()!=request.getOptions().size())throw exception(MENU_DUPLICATE);
        OptionGroupDO row=BeanUtils.toBean(request,OptionGroupDO.class);
        if(row.getId()!=null&&groups.selectOne(new LambdaQueryWrapper<OptionGroupDO>().eq(OptionGroupDO::getId,row.getId()).last("FOR UPDATE"))==null)throw exception(MENU_NOT_FOUND);
        if(row.getId()==null)groups.insert(row);else groups.updateById(row);
        Set<Long> kept=new HashSet<>();
        for(var option:request.getOptions()){
            OptionDO value=BeanUtils.toBean(option,OptionDO.class);value.setGroupId(row.getId());
            if(value.getId()!=null){
                OptionDO old=options.selectById(value.getId());
                if(old==null||!old.getGroupId().equals(row.getId())||!kept.add(value.getId()))throw exception(MENU_INVALID);
                options.updateById(value);
            } else { options.insert(value);kept.add(value.getId()); }
        }
        options.delete(new LambdaQueryWrapper<OptionDO>().eq(OptionDO::getGroupId,row.getId()).notIn(OptionDO::getId,kept));
        return row.getId();
    }
    @Transactional(rollbackFor=Exception.class)
    public void deleteGroup(Long id) {
        if(groups.selectOne(new LambdaQueryWrapper<OptionGroupDO>().eq(OptionGroupDO::getId,id).last("FOR UPDATE"))==null)throw exception(MENU_NOT_FOUND);
        if(itemGroups.selectCount(new LambdaQueryWrapper<ItemGroupDO>().eq(ItemGroupDO::getGroupId,id))>0)throw exception(MENU_IN_USE);
        groups.deleteById(id);options.delete(new LambdaQueryWrapper<OptionDO>().eq(OptionDO::getGroupId,id));
    }
}
