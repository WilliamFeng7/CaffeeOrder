import { Icon } from '../Icon';
import { BottomNav } from './BottomNav';

export type Stage = 'created' | 'processing' | 'ready';

const PROGRESS: Record<Stage, number> = { created: 0.12, processing: 0.56, ready: 1 };
const LABEL: Record<Stage, string> = { created: '待录单', processing: '制作中', ready: '制作完成' };
const STEP: Record<Stage, number> = { created: 0, processing: 1, ready: 2 };

export function PickupScreen({
  stage = 'processing',
  receipt = 'A012',
  ahead = 2,
  toast = false,
  waitingText = '等待录单',
}: {
  stage?: Stage;
  receipt?: string;
  ahead?: number;
  toast?: boolean;
  waitingText?: string;
}) {
  const ready = stage === 'ready';
  const created = stage === 'created';

  return (
    <div className="app">
      <div className="app-scroll app-pad">
        <header className="pickup-head">
          <h1>取餐</h1>
          <div className="pickup-seg">
            <span className="is-on">当前订单</span>
            <span>历史订单</span>
          </div>
        </header>

        <article className={`pickup-card ${ready ? 'is-ready' : ''}`}>
          <div className="pickup-top">
            <div>
              <p className="pickup-label">收银单号</p>
              <p className={`pickup-no ${ready ? 'is-ready' : ''} ${created ? 'is-waiting' : ''}`}>
                {created ? waitingText : receipt}
              </p>
            </div>
            <span className={`pickup-status ${ready ? 'is-ready' : stage === 'processing' ? 'is-processing' : ''}`}>
              <span className="dot" />
              {LABEL[stage]}
            </span>
          </div>

          {!created ? (
            <p className="pickup-ahead">
              {ready ? '已做好，请到柜台取餐' : `前面还有 ${ahead} 单`}
            </p>
          ) : (
            <p className="pickup-ahead">咖啡师录单后会显示收银单号</p>
          )}

          <div className="pickup-progress">
            <div className="pickup-track">
              <div className="pickup-fill" style={{ transform: `scaleX(${PROGRESS[stage]})` }} />
            </div>
            <div className={`pickup-steps ${ready ? 'is-all' : ''}`}>
              {['待录单', '制作中', '制作完成'].map((label, index) => (
                <span key={label} className={index <= STEP[stage] ? 'is-past' : ''}>
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div className="pickup-items">
            <div className="pickup-item">
              <em>1×</em>
              <span>经典拿铁</span>
              <span className="spec">热 · 标准</span>
            </div>
          </div>

          <div className="pickup-meta">
            <span>
              今天 14:02 · 1 件
              <br />
              OTIA-20261017-0042
            </span>
            <b>¥15.00</b>
          </div>
        </article>

        <div className="pickup-past">
          <span>昨天 15:42 · A006</span>
          <span>¥15.00 · 制作完成</span>
        </div>
      </div>

      {toast ? (
        <div className="phone-toast">
          <span className="toast-check">
            <Icon name="check" size={10} />
          </span>
          制作完成，请凭收银单号到柜台取餐
        </div>
      ) : null}

      <BottomNav active="pickup" badge={1} />
    </div>
  );
}
