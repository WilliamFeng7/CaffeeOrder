import { Img } from 'remotion';
import { Backdrop, MaskLine, SceneFade, SceneIndex, enter, fadeStyle, photo } from '../parts';
import { useCurrentFrame, interpolate } from 'remotion';

export function Intro() {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 120], [1.08, 1], { extrapolateRight: 'clamp' });
  const photoIn = enter(frame, 14, 40);

  return (
    <SceneFade duration={120}>
      <Backdrop />

      <div className="v-wordmark">
        OTIA Café<span>Student Edition</span>
      </div>

      <div className="v-intro-copy">
        <p className="v-kicker" style={fadeStyle(enter(frame, 4, 24), 16)}>
          <b>学生端</b> · 一杯咖啡的 38 秒
        </p>
        <h1 className="v-intro-title">
          <MaskLine progress={enter(frame, 8, 34)}>上课前点好，</MaskLine>
          <MaskLine progress={enter(frame, 16, 34)} className="is-green">
            下课就喝到。
          </MaskLine>
        </h1>
        <p className="v-intro-sub" style={fadeStyle(enter(frame, 32, 34), 24)}>
          在钉钉里点单，用学生卡付款。收银单号和制作进度，会自己回到你手上。
        </p>
        <div className="v-intro-meta" style={fadeStyle(enter(frame, 48, 30), 18)}>
          <span>
            <b>免登录</b> · 钉钉账号直达
          </span>
          <span>
            <b>学生卡</b> · 一键支付
          </span>
          <span>
            <b>每 3 秒</b> · 进度刷新
          </span>
        </div>
      </div>

      <div className="v-disc" style={{ transform: `scale(${zoom})` }} />
      <div
        className="v-arch v-intro-arch"
        style={{
          width: 520,
          height: 690,
          opacity: photoIn,
          transform: `scale(${zoom}) translateY(${(1 - photoIn) * 30}px)`,
        }}
      >
        <Img src={photo('latte.jpg')} />
      </div>

      <div className="v-hours-card" style={fadeStyle(enter(frame, 54, 30), 20)}>
        <span>Business hours</span>
        <b>11:40–12:30 · 15:30–17:00</b>
      </div>

      <span className="v-vertical-mark">OTIA CAFÉ · STUDENT EDITION · 2026</span>
      <SceneIndex index={1} />
    </SceneFade>
  );
}
