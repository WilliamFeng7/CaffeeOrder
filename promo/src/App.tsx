import { useEffect, useRef, useState } from 'react';
import { Icon, type IconName } from './components/Icon';
import { Phone, formatMoney } from './components/Phone';
import { HomeScreen } from './components/screens/HomeScreen';
import { PickupScreen, type Stage } from './components/screens/PickupScreen';
import { Reveal } from './components/Reveal';
import { Film } from './components/Film';
import { DRINKS, FEATURES, HOURS, IMG, MENU_PICKS, STAGES } from './data';

const NAV_LINKS = [
  { href: '#how', label: '点单流程' },
  { href: '#film', label: '宣传片' },
  { href: '#features', label: '为什么好用' },
  { href: '#menu', label: '菜单' },
];

function useScrollState() {
  const [scrolled, setScrolled] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      raf = 0;
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setScrolled(y > 20);
      setProgress(max > 0 ? Math.min(1, y / max) : 0);
    };
    const onScroll = () => {
      if (!raf) raf = window.requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }, []);

  return { scrolled, progress };
}

function useTilt<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    let raf = 0;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const apply = () => {
      raf = 0;
      currentX += (targetX - currentX) * 0.12;
      currentY += (targetY - currentY) * 0.12;
      node.style.transform = `perspective(1300px) rotateY(${currentX}deg) rotateX(${currentY}deg)`;
      if (Math.abs(targetX - currentX) > 0.01 || Math.abs(targetY - currentY) > 0.01) {
        raf = window.requestAnimationFrame(apply);
      }
    };

    const onMove = (event: PointerEvent) => {
      const rect = node.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      targetX = x * 6;
      targetY = -y * 4.5;
      if (!raf) raf = window.requestAnimationFrame(apply);
    };

    const onLeave = () => {
      targetX = 0;
      targetY = 0;
      if (!raf) raf = window.requestAnimationFrame(apply);
    };

    node.addEventListener('pointermove', onMove);
    node.addEventListener('pointerleave', onLeave);
    return () => {
      window.cancelAnimationFrame(raf);
      node.removeEventListener('pointermove', onMove);
      node.removeEventListener('pointerleave', onLeave);
    };
  }, []);

  return ref;
}

function HomeVignette() {
  return (
    <div className="vig vig-home" aria-hidden="true">
      <div className="vig-home-top">
        <span className="vig-brand">OTIA Café</span>
        <span className="vig-live">
          <i />
          营业中
        </span>
      </div>
      <p className="vig-hello">下午好，林同学</p>
      <p className="vig-headline">今天想喝点什么？</p>
      <div className="vig-feature">
        <img src={IMG(DRINKS.latte.img)} alt="" />
        <div>
          <span>热销</span>
          <b>经典拿铁</b>
          <em>¥15</em>
        </div>
      </div>
      <div className="vig-login">
        <Icon name="chat" size={14} />
        钉钉免登 · 学号已带出
      </div>
    </div>
  );
}

function OptionsVignette() {
  return (
    <div className="vig vig-options" aria-hidden="true">
      <div className="vig-product">
        <img src={IMG(DRINKS.latte.img)} alt="" />
        <div>
          <b>经典拿铁</b>
          <span>双份浓缩 · 蒸汽牛奶</span>
        </div>
        <em>¥15</em>
      </div>
      <p className="vig-label">温度</p>
      <div className="vig-chips">
        <span className="on">热</span>
        <span>冰</span>
      </div>
      <p className="vig-label">糖度</p>
      <div className="vig-chips four">
        <span>无糖</span>
        <span>半糖</span>
        <span className="on">标准</span>
        <span>多糖</span>
      </div>
      <div className="vig-add">
        加入购物车
        <Icon name="plus" size={13} />
      </div>
    </div>
  );
}

function PickupVignette() {
  return (
    <div className="vig vig-pickup" aria-hidden="true">
      <div className="vig-receipt-top">
        <div>
          <span>收银单号</span>
          <b>A012</b>
        </div>
        <span className="vig-status">
          <i />
          制作中
        </span>
      </div>
      <p className="vig-ahead">前面还有 2 单</p>
      <div className="vig-progress">
        <span style={{ transform: 'scaleX(0.56)' }} />
      </div>
      <div className="vig-steps">
        <span className="past">待录单</span>
        <span className="past">制作中</span>
        <span>制作完成</span>
      </div>
      <div className="vig-toast">
        <Icon name="bell" size={14} />
        做好会提醒，不用一直刷新
      </div>
    </div>
  );
}

function CopyPath() {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const text = '钉钉 → 工作台 → OTIA Café';
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const input = document.createElement('textarea');
      input.value = text;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      input.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2200);
  };

  return (
    <button type="button" className="copy-path" onClick={copy}>
      <Icon name={copied ? 'check' : 'copy'} size={14} />
      {copied ? '已复制打开路径' : '复制打开路径'}
    </button>
  );
}

export default function App() {
  const { scrolled, progress } = useScrollState();
  const tiltRef = useTilt<HTMLDivElement>();
  const [stageIndex, setStageIndex] = useState(1);
  const stage = STAGES[stageIndex].id as Stage;

  return (
    <div className="site" id="top">
      <div className="scroll-progress" style={{ transform: `scaleX(${progress})` }} aria-hidden="true" />

      <header className={`nav ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="wrap nav-inner">
          <a href="#top" className="brand" aria-label="OTIA Café 学生端，回到顶部">
            <span className="brand-word">OTIA Café</span>
            <span className="brand-tag">学生端</span>
          </a>

          <nav className="nav-links" aria-label="页面导航">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href}>
                {link.label}
              </a>
            ))}
          </nav>

          <div className="nav-actions">
            <span className="open-pill">
              <i />
              营业中
            </span>
            <a className="btn btn-primary btn-sm" href="#open">
              在钉钉打开
              <Icon name="arrow-up-right" size={14} />
            </a>
          </div>
        </div>
      </header>

      <main>
        {/* ---------------------------------------------------------------- hero */}
        <section className="hero">
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <p className="kicker hero-kicker">
                <span className="kicker-line" />
                OTIA CAFÉ · 学生端
              </p>
              <h1 className="hero-title">
                上课前点好，
                <br />
                <span className="hero-accent">下课就喝到。</span>
              </h1>
              <p className="hero-lede">
                在钉钉里打开 OTIA Café，选好温度与糖度，用学生卡直接付款。咖啡师录单后，收银单号和制作进度会自己回到你手上。
              </p>
              <div className="hero-actions">
                <a className="btn btn-primary btn-lg" href="#open">
                  在钉钉中打开
                  <Icon name="arrow-up-right" size={16} />
                </a>
                <a className="btn btn-ghost btn-lg" href="#film">
                  <span className="play-dot">
                    <Icon name="play" size={10} />
                  </span>
                  看 38 秒短片
                </a>
              </div>

              <dl className="hero-facts">
                <div>
                  <dt>免登录</dt>
                  <dd>钉钉里打开，就是你的账号</dd>
                </div>
                <div>
                  <dt>学生卡直付</dt>
                  <dd>不用扫码，余额看得见</dd>
                </div>
                <div>
                  <dt>每 3 秒</dt>
                  <dd>订单进度自己刷新</dd>
                </div>
              </dl>
            </div>

            <div className="hero-visual" aria-hidden="true">
              <div className="hero-disc" />
              <div className="hero-arch">
                <img src={IMG(DRINKS.coldbrew.img)} alt="" />
              </div>
              <div className="hero-phone">
                <div className="hero-phone-tilt" ref={tiltRef}>
                  <Phone width={336}>
                    <HomeScreen />
                  </Phone>
                </div>
              </div>

              <div className="float-card float-queue">
                <span className="float-icon">
                  <Icon name="users" size={17} />
                </span>
                <div>
                  <span className="float-label">现在排队</span>
                  <b>
                    3 <small>单</small>
                  </b>
                </div>
                <span className="live-dot" />
              </div>

              <div className="float-card float-receipt">
                <span className="float-label">收银单号</span>
                <b className="float-no">A012</b>
                <div className="float-progress">
                  <span />
                </div>
                <span className="float-status">
                  <i />
                  制作中 · 前面还有 2 单
                </span>
              </div>
            </div>
          </div>

          <div className="ticker" aria-hidden="true">
            <div className="ticker-track">
              {[0, 1].map((copy) => (
                <div className="ticker-set" key={copy}>
                  {MENU_PICKS.map((drink) => (
                    <span key={drink.id}>
                      {drink.name}
                      <em>{formatMoney(drink.price)}</em>
                      <i>·</i>
                    </span>
                  ))}
                  <span>
                    冷萃咖啡
                    <em>¥20</em>
                    <i>·</i>
                  </span>
                  <span>
                    黄油可颂
                    <em>¥12</em>
                    <i>·</i>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ----------------------------------------------------------------- how */}
        <section className="section how" id="how">
          <div className="wrap">
            <Reveal className="section-head">
              <div>
                <p className="kicker">
                  <b>01</b> · 点单流程
                </p>
                <h2 className="section-title">
                  把点单，塞进
                  <br />
                  课间的十分钟。
                </h2>
              </div>
              <p className="section-note">
                从打开到取餐，三步。没有下载，没有排队，也不用记住取餐号。
              </p>
            </Reveal>

            <Reveal delay={80} group className="steps">
              <article className="step-card">
                <div className="step-top">
                  <span className="step-no">01</span>
                  <span className="step-icon">
                    <Icon name="house" size={19} />
                  </span>
                </div>
                <HomeVignette />
                <h3>打开钉钉</h3>
                <p>学号自动带出，免登录进入菜单。</p>
              </article>

              <article className="step-card">
                <div className="step-top">
                  <span className="step-no">02</span>
                  <span className="step-icon">
                    <Icon name="sliders" size={19} />
                  </span>
                </div>
                <OptionsVignette />
                <h3>选好这一杯</h3>
                <p>温度、糖度自己定，价格实时算清。</p>
              </article>

              <article className="step-card">
                <div className="step-top">
                  <span className="step-no">03</span>
                  <span className="step-icon">
                    <Icon name="bell" size={19} />
                  </span>
                </div>
                <PickupVignette />
                <h3>下课去取</h3>
                <p>收银单号 + 三步进度，做好再下楼。</p>
              </article>
            </Reveal>
          </div>
        </section>

        <Film />

        {/* ------------------------------------------------------------ features */}
        <section className="section features" id="features">
          <div className="wrap features-grid">
            <Reveal className="features-copy">
              <p className="kicker">
                <b>03</b> · 为什么好用
              </p>
              <h2 className="section-title">
                少排一次队，
                <br />
                多喝一口热的。
              </h2>
              <p className="section-note">
                学生端把点单、付款、取餐串成一条线。你只需要决定喝什么。
              </p>
              <a className="text-link" href="#open">
                在钉钉里打开
                <Icon name="arrow-right" size={15} />
              </a>
            </Reveal>

            <Reveal delay={120} group className="feature-list">
              {FEATURES.map((feature) => (
                <article className="feature-row" key={feature.title}>
                  <span className="feature-icon">
                    <Icon name={feature.icon as IconName} size={20} />
                  </span>
                  <div>
                    <h3>{feature.title}</h3>
                    <p>{feature.body}</p>
                  </div>
                  <span className="feature-index">{feature.index}</span>
                </article>
              ))}
            </Reveal>
          </div>
        </section>

        {/* ------------------------------------------------------------- pickup */}
        <section className="section timeline" id="timeline">
          <div className="wrap timeline-grid">
            <Reveal className="timeline-copy">
              <p className="kicker">
                <b>04</b> · 取餐
              </p>
              <h2 className="section-title">
                一杯咖啡的
                <br />
                三段进度。
              </h2>
              <p className="section-note">
                点一下状态，看看学生端会显示什么。不用猜，也不用问柜台。
              </p>

              <div className="stage-tabs" role="tablist" aria-label="订单状态">
                {STAGES.map((item, index) => (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={stageIndex === index}
                    className={`stage-tab ${stageIndex === index ? 'is-active' : ''}`}
                    onClick={() => setStageIndex(index)}
                  >
                    <span className="stage-index">0{index + 1}</span>
                    <span className="stage-body">
                      <b>{item.label}</b>
                      <em>{item.short}</em>
                    </span>
                    <Icon name="caret-right" size={15} />
                  </button>
                ))}
              </div>
            </Reveal>

            <Reveal delay={100} className="timeline-visual">
              <div className="stage-glow" aria-hidden="true" />
              <span className="ghost-number" aria-hidden="true">
                A012
              </span>
              <div className={`timeline-phone ${stage === 'ready' ? 'is-ready' : ''}`} aria-hidden="true">
                <Phone width={348}>
                  <PickupScreen stage={stage} toast={stage === 'ready'} />
                </Phone>
              </div>
              <div className="timeline-caption">
                <span>{STAGES[stageIndex].title}</span>
                <p>{STAGES[stageIndex].body}</p>
              </div>
            </Reveal>
          </div>
        </section>

        {/* --------------------------------------------------------------- menu */}
        <section className="section menu" id="menu">
          <div className="wrap">
            <Reveal className="section-head">
              <div>
                <p className="kicker">
                  <b>05</b> · 菜单
                </p>
                <h2 className="section-title">
                  今天，
                  <br />
                  喝点什么？
                </h2>
              </div>
              <p className="section-note">菜单和价格，以学生端当天显示为准。</p>
            </Reveal>

            <Reveal delay={80} group className="menu-grid">
              {MENU_PICKS.map((drink) => (
                <article className="drink-card" key={drink.id}>
                  <div className="drink-photo">
                    <img src={IMG(drink.img)} alt={`${drink.name}（${drink.en}）`} loading="lazy" />
                    {drink.tag ? <span className="drink-tag">{drink.tag}</span> : null}
                  </div>
                  <div className="drink-meta">
                    <div>
                      <h3>{drink.name}</h3>
                      <p>{drink.en}</p>
                    </div>
                    <span className="drink-price">{formatMoney(drink.price)}</span>
                  </div>
                </article>
              ))}
            </Reveal>

            <Reveal delay={120} className="menu-foot">
              <span>还有冷萃、抹茶、鲜果茶和每天现烤的烘焙。</span>
              <a className="text-link" href="#open">
                去学生端看全部
                <Icon name="arrow-up-right" size={15} />
              </a>
            </Reveal>
          </div>
        </section>

        {/* --------------------------------------------------------------- card */}
        <section className="section card-section" id="card">
          <div className="wrap card-grid">
            <Reveal className="card-visual" aria-hidden>
              <div className="student-card">
                <div className="student-card-head">
                  <span>OTIA 学生卡</span>
                  <span className="card-chip" />
                </div>
                <div className="student-card-name">
                  <b>林同学</b>
                  <span>学号 2024 0317</span>
                </div>
                <div className="student-card-bottom">
                  <div>
                    <span>学生卡余额</span>
                    <b>¥50.00</b>
                  </div>
                  <span className="student-card-mark">OTIA</span>
                </div>
              </div>
              <div className="card-float">
                <span>本次消费</span>
                <b>− ¥15.00</b>
              </div>
            </Reveal>

            <Reveal delay={100} className="card-copy">
              <p className="kicker">
                <b>06</b> · 学生卡
              </p>
              <h2 className="section-title">
                钱在卡里，
                <br />
                单在手机里。
              </h2>
              <p className="section-note">
                家长通过支付宝把生活费交给学校，学校充进学生卡。点单时直接从卡里扣，余额和订单都留在学生端。
              </p>
              <ul className="check-list">
                <li>
                  <Icon name="check" size={15} />
                  不用带现金，也不用掏手机扫码
                </li>
                <li>
                  <Icon name="check" size={15} />
                  结算页实时显示学生卡余额
                </li>
                <li>
                  <Icon name="check" size={15} />
                  每一笔订单和消费，都能在「我的」查到
                </li>
              </ul>
            </Reveal>
          </div>
        </section>

        {/* ---------------------------------------------------------------- faq */}
        <section className="section faq" id="faq">
          <div className="wrap faq-grid">
            <Reveal>
              <p className="kicker">
                <b>07</b> · 常见问题
              </p>
              <h2 className="section-title">你可能想问。</h2>
            </Reveal>

            <Reveal delay={100} className="faq-list">
              <details>
                <summary>
                  <span>需要下载 App 吗？</span>
                  <i>+</i>
                </summary>
                <p>不用。在钉钉工作台打开 OTIA Café 就行。添加到主屏幕后，它看起来和用起来都更像一个 App。</p>
              </details>
              <details>
                <summary>
                  <span>什么时候可以点单？</span>
                  <i>+</i>
                </summary>
                <p>营业时段是 {HOURS}。打烊后菜单只读，不能下单；首页会显示下一次营业时间。</p>
              </details>
              <details>
                <summary>
                  <span>收银单号在哪里看？</span>
                  <i>+</i>
                </summary>
                <p>下单后进入「取餐」。咖啡师录单并回填后，收银单号会出现在订单卡片最上方，制作完成后还会提醒你下楼。</p>
              </details>
              <details>
                <summary>
                  <span>学生卡余额怎么用？</span>
                  <i>+</i>
                </summary>
                <p>在结算页直接用学生卡付款，不用扫码。余额不足时，支付按钮会提示，可以先找家长充值。</p>
              </details>
            </Reveal>
          </div>
        </section>

        {/* -------------------------------------------------------------- finale */}
        <section className="finale" id="open">
          <div className="finale-grain" aria-hidden="true" />
          <div className="wrap finale-grid">
            <Reveal className="finale-copy">
              <p className="kicker finale-kicker">
                <span className="kicker-line" />
                OTIA CAFÉ · 学生端
              </p>
              <h2>
                下一杯，
                <br />
                提前点好。
              </h2>
              <p className="finale-lede">
                在钉钉工作台打开 OTIA Café。营业时段内下单，用学生卡付款，然后安心上课。
              </p>
              <div className="finale-actions">
                <div className="finale-path">
                  <Icon name="chat" size={17} />
                  <span>
                    钉钉 <i>→</i> 工作台 <i>→</i> <b>OTIA Café</b>
                  </span>
                </div>
                <CopyPath />
              </div>
              <p className="finale-hours">
                <Icon name="clock" size={14} />
                {HOURS}
                <span>营业时段外菜单只读</span>
              </p>
            </Reveal>

            <Reveal delay={120} className="finale-visual" aria-hidden>
              <div className="finale-arch">
                <img src={IMG(DRINKS.latte.img)} alt="" loading="lazy" />
              </div>
              <div className="finale-seal">
                <span>OTIA</span>
                <em>学生专享</em>
                <span>2026</span>
              </div>
              <p className="finale-note">一杯咖啡，<br />刚好在课间。</p>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="wrap footer-top">
          <div>
            <span className="brand-word">OTIA Café</span>
            <p>校园咖啡 · 学生端 v3.0</p>
          </div>
          <nav aria-label="页脚导航">
            <a href="#how">点单流程</a>
            <a href="#film">宣传片</a>
            <a href="#menu">菜单</a>
            <a href="#faq">常见问题</a>
            <a href="#top">回到顶部</a>
          </nav>
        </div>
        <div className="wrap footer-bottom">
          <span>为 OTIA 学生而做 · 2026</span>
          <span>营业时间 {HOURS}</span>
          <span>菜单与价格以学生端当天显示为准</span>
        </div>
      </footer>
    </div>
  );
}
