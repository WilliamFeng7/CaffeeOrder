import { DRINKS, IMG } from '../../data';
import { Icon } from '../Icon';
import { BottomNav } from './BottomNav';
import { formatMoney } from '../Phone';

const CATEGORIES = ['店长推荐', '当季新品', '现磨咖啡', '鲜果茶', '烘焙'];

export function MenuScreen({
  active = '现磨咖啡',
  items = ['latte', 'espresso', 'cappuccino', 'macchiato', 'flatwhite', 'coldbrew'],
  count = 6,
}: {
  active?: string;
  items?: string[];
  count?: number;
}) {
  return (
    <div className="app">
      <div className="app-scroll">
        <div className="app-pad menu-head">
          <div className="menu-title-row">
            <div>
              <p className="menu-count">{count} 款</p>
              <h1 className="menu-title">{active}</h1>
            </div>
          </div>
          <div className="menu-search">
            <Icon name="search" size={14} />
            搜索咖啡、茶或甜点
          </div>
        </div>

        <div className="menu-cats">
          {CATEGORIES.map((cat) => (
            <span key={cat} className={`menu-cat ${cat === active ? 'is-active' : ''}`}>
              {cat}
            </span>
          ))}
        </div>

        <div className="menu-grid">
          {items.map((id) => {
            const drink = DRINKS[id];
            if (!drink) return null;
            return (
              <article className="menu-product" key={drink.id}>
                <div className="menu-product-img">
                  <img src={IMG(drink.img)} alt={drink.name} />
                </div>
                <h3>{drink.name}</h3>
                <p>{formatMoney(drink.price)}</p>
              </article>
            );
          })}
        </div>
      </div>

      <BottomNav active="order" />
    </div>
  );
}
