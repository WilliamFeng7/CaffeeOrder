import { DRINKS, IMG } from '../../data';
import { Icon } from '../Icon';
import { formatMoney } from '../Phone';

const money2 = (n: number) => `¥${n.toFixed(2)}`;

export function CheckoutScreen({
  paid = false,
  balance = 50,
  total = 15,
  pressing = false,
  successProgress = 0,
}: {
  paid?: boolean;
  balance?: number;
  total?: number;
  pressing?: boolean;
  successProgress?: number;
}) {
  const drink = DRINKS.latte;
  return (
    <div className="app">
      <div className="app-scroll app-pad checkout-scroll">
        <header className="checkout-head">
          <span className="checkout-back">
            <Icon name="arrow-left" size={18} />
          </span>
          <h1 className="checkout-title">确认订单</h1>
          <span className="checkout-count">1 件</span>
        </header>

        <p className="checkout-section-label">商品</p>

        <article className="checkout-item">
          <img src={IMG(drink.img)} alt={drink.name} />
          <div className="checkout-item-main">
            <h3>{drink.name}</h3>
            <p>热 · 标准</p>
            <div className="checkout-item-bottom">
              <span>{formatMoney(drink.price)} / 杯</span>
              <span className="qty-pill">
                <i>−</i>1<i>+</i>
              </span>
            </div>
          </div>
        </article>

        <section className="checkout-summary">
          <div className="summary-row">
            <span>小计</span>
            <span>{money2(total)}</span>
          </div>
          <div className="summary-row">
            <span>学生卡余额</span>
            <span>{money2(balance)}</span>
          </div>
          <div className="summary-rule" />
          <div className="summary-total-row">
            <span>总计</span>
            <span className="summary-total">{money2(total)}</span>
          </div>
        </section>

        <section className="checkout-info">
          <div className="checkout-info-row">
            <span>取餐方式</span>
            <b>到店取餐 · 凭收银单号</b>
          </div>
          <div className="checkout-info-row">
            <span>支付方式</span>
            <b>学生卡 · 免扫码</b>
          </div>
        </section>

        <p className="checkout-hint">
          <Icon name="bell" size={12} />
          下单后可在「取餐」查看制作进度
        </p>

        {paid ? (
          <div
            className="checkout-success"
            style={{ opacity: successProgress, transform: `translateY(${(1 - successProgress) * 10}px)` }}
          >
            <span className="checkout-success-ring">
              <Icon name="check" size={20} />
            </span>
            <b>支付成功</b>
            <span>咖啡师端已经收到这一单</span>
          </div>
        ) : null}
      </div>

      <div className="checkout-paybar">
        <div>
          <span className="label">应付</span>
          <span className="amount">{money2(total)}</span>
        </div>
        <button className={`pay-button ${paid ? 'is-done' : ''}`} type="button" style={{ transform: `scale(${pressing ? 0.96 : 1})` }}>
          {paid ? (
            <>
              <Icon name="check" size={15} />
              已下单
            </>
          ) : (
            `支付 ${money2(total)}`
          )}
        </button>
      </div>
    </div>
  );
}
