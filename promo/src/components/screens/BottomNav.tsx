import { Icon, type IconName } from '../Icon';

const ITEMS: { id: string; label: string; icon: IconName }[] = [
  { id: 'home', label: '首页', icon: 'house' },
  { id: 'order', label: '点餐', icon: 'coffee' },
  { id: 'pickup', label: '取餐', icon: 'bell' },
  { id: 'profile', label: '我的', icon: 'user' },
];

export function BottomNav({
  active,
  badge = 0,
}: {
  active: 'home' | 'order' | 'pickup' | 'profile';
  badge?: number;
}) {
  const index = Math.max(0, ITEMS.findIndex((item) => item.id === active));
  return (
    <div className="phone-nav">
      <span
        className="phone-nav-line"
        style={{ left: `calc(${index * 25}% + ${25 / 2}% - 10px)` }}
      />
      {ITEMS.map((item) => (
        <div key={item.id} className={`phone-nav-item ${item.id === active ? 'is-active' : ''}`}>
          <span style={{ position: 'relative', display: 'inline-flex' }}>
            <Icon name={item.icon} size={22} strokeWidth={item.id === active ? 1.7 : 1.4} />
            {item.id === 'pickup' && badge > 0 ? <span className="phone-nav-badge">{badge}</span> : null}
          </span>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
