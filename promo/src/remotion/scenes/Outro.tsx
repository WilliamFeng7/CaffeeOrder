import { useCurrentFrame } from 'remotion';
import { MaskLine, PhotoArch, SceneFade, SceneIndex, enter, fadeStyle } from '../parts';
import { Icon } from '../../components/Icon';

export function Outro() {
  const frame = useCurrentFrame();

  return (
    <SceneFade duration={140} background="#0c1f1a" fadeIn={12} fadeOut={0}>
      <div className="v-grain" />
      <div className="v-outro-glow" />

      <div className="v-outro-wordmark">
        OTIA Café<span>Student Edition</span>
      </div>

      <div className="v-outro-copy">
        <p className="v-kicker" style={{ color: 'rgba(246,241,228,0.52)', ...fadeStyle(enter(frame, 4, 24), 16) }}>
          <b style={{ color: '#a9c9ba' }}>学生端</b> · 下一杯
        </p>
        <h1 className="v-outro-title">
          <MaskLine progress={enter(frame, 10, 32)}>下一杯，</MaskLine>
          <MaskLine progress={enter(frame, 18, 32)}>提前点好。</MaskLine>
        </h1>
        <p className="v-outro-sub" style={fadeStyle(enter(frame, 34, 30), 20)}>
          在钉钉工作台打开 OTIA Café。营业时段内下单，用学生卡付款，然后安心上课。
        </p>
        <div className="v-outro-cta" style={fadeStyle(enter(frame, 44, 28), 18)}>
          在钉钉工作台打开
          <Icon name="arrow-up-right" size={22} />
        </div>
        <p className="v-outro-hours" style={fadeStyle(enter(frame, 54, 26), 14)}>
          11:40–12:30 · 15:30–17:00
          <i />
          营业时段外菜单只读
          <i />
          学生端 v3.0
        </p>
      </div>

      <PhotoArch x={1370} y={240} width={430} height={560} file="latte.jpg" className="v-outro-arch" />

      <div className="v-outro-seal" style={fadeStyle(enter(frame, 50, 28), 20)}>
        <b>OTIA</b>
        <i />
        学生专享
        <i />
        2026
      </div>

      <p className="v-outro-note" style={fadeStyle(enter(frame, 58, 26), 16)}>
        一杯咖啡，
        <br />
        刚好在课间。
      </p>

      <SceneIndex index={6} light />
    </SceneFade>
  );
}
