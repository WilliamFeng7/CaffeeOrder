import { DRINKS, IMG } from '../../data';
import { Icon } from '../Icon';
import { MenuScreen } from './MenuScreen';
import { formatMoney } from '../Phone';

export function SheetScreen({
  temp = '热',
  sugar = '标准',
  added = false,
  sheetProgress = 1,
}: {
  temp?: '热' | '冰';
  sugar?: '无糖' | '半糖' | '标准' | '多糖';
  added?: boolean;
  sheetProgress?: number;
}) {
  const drink = DRINKS.latte;

  return (
    <div className="app">
      <MenuScreen />
      <div className="sheet-scrim" style={{ opacity: sheetProgress }} />
      <div className="sheet" style={{ transform: `translateY(${(1 - sheetProgress) * 100}%)` }}>
        <div className="sheet-photo">
          <img src={IMG(drink.img)} alt={drink.name} />
          <span className="sheet-close">
            <Icon name="x" size={15} />
          </span>
        </div>
        <div className="sheet-copy">
          <p className="home-tag">
            <Icon name="star" size={12} />
            热销
          </p>
          <h2>{drink.name}</h2>
          <p className="sheet-desc">{drink.desc}</p>

          <div className="sheet-group">
            <p className="sheet-label">温度</p>
            <div className="sheet-chips">
              {(['热', '冰'] as const).map((option) => (
                <span key={option} className={`sheet-chip ${temp === option ? 'is-on' : ''}`}>
                  {option}
                </span>
              ))}
            </div>
          </div>

          <div className="sheet-group">
            <p className="sheet-label">糖度</p>
            <div className="sheet-chips">
              {(['无糖', '半糖', '标准', '多糖'] as const).map((option) => (
                <span key={option} className={`sheet-chip ${sugar === option ? 'is-on' : ''}`}>
                  {option}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="sheet-footer">
          <div>
            <span className="label">总计</span>
            <span className="price">{formatMoney(drink.price)}</span>
          </div>
          <span className={`sheet-add ${added ? 'is-done' : ''}`}>
            {added ? (
              <>
                <Icon name="check" size={14} />
                已加入
              </>
            ) : (
              '加入购物车'
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
