import { DRINKS, IMG } from '../../data';
import { Icon } from '../Icon';
import { BottomNav } from './BottomNav';
import { formatMoney } from '../Phone';

export function HomeScreen({
  name = '林同学',
  queue = 3,
}: {
  name?: string;
  queue?: number;
}) {
  const feat = DRINKS.latte;
  const minis = [DRINKS.coconut, DRINKS.cheesecake, DRINKS.macchiato, DRINKS.croissant];

  return (
    <div className="app">
      <div className="app-scroll app-pad">
        <header className="home-header">
          <span className="home-brand">OTIA Café</span>
          <span className="home-queue">
            <span className="dot" />
            现在排队 {queue} 单
          </span>
        </header>

        <section className="home-greeting">
          <p className="eyebrow">下午好，{name}</p>
          <h1>今天想喝点什么？</h1>
        </section>

        <article className="home-feat">
          <div className="home-feat-img">
            <img src={IMG(feat.img)} alt={feat.name} />
          </div>
          <div className="home-feat-copy">
            <p className="home-tag">
              <Icon name="star" size={12} />
              热销
            </p>
            <h2>{feat.name}</h2>
            <p>{feat.desc}</p>
            <div className="home-feat-row">
              <span className="home-price">
                {formatMoney(feat.price)}
                <small>起</small>
              </span>
              <span className="home-add">
                <Icon name="plus" size={12} />
                加入
              </span>
            </div>
          </div>
        </article>

        <section className="home-trend">
          <div className="home-trend-head">
            <h2>热门推荐</h2>
            <span>全部菜单</span>
          </div>
          <div className="home-trend-grid">
            {minis.map((drink) => (
              <article className="home-mini" key={drink.id}>
                <img src={IMG(drink.img)} alt={drink.name} />
                <span style={{ minWidth: 0 }}>
                  <b>{drink.name}</b>
                  <span>{formatMoney(drink.price)}</span>
                </span>
              </article>
            ))}
          </div>
        </section>
      </div>

      <BottomNav active="home" />
    </div>
  );
}
