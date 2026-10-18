import { useCurrentFrame } from 'remotion';
import { Backdrop, CopyBlock, PhoneEnter, SceneFade, SceneIndex, enter } from '../parts';
import { PickupScreen, type Stage } from '../../components/screens/PickupScreen';

export function PickupScene() {
  const frame = useCurrentFrame();
  const stage: Stage = frame < 66 ? 'created' : frame < 154 ? 'processing' : 'ready';
  const toast = stage === 'ready';
  const halo = enter(frame, 154, 24);

  return (
    <SceneFade duration={240}>
      <Backdrop />

      <span className="v-ghost" style={{ left: 8, top: 232 }}>
        A012
      </span>

      <div
        className="v-ready-halo"
        style={{
          left: 96,
          top: 78,
          width: 650,
          height: 910,
          borderRadius: 360,
          opacity: halo,
          transform: `scale(${0.96 + halo * 0.04})`,
        }}
      />

      <PhoneEnter x={178} y={28} width={470} rotate={1.2} delay={4}>
        <PickupScreen stage={stage} toast={toast} />
      </PhoneEnter>

      <CopyBlock
        x={1140}
        y={266}
        width={690}
        kicker="去取餐"
        kickerIndex="04"
        title={['收银单号，', '进度都在手上。']}
        body="咖啡师录单后，单号会自己出现。做好再下楼，不用站在柜台前等。"
        bullets={['待录单 → 制作中 → 制作完成', '每 3 秒自己刷新', '做好会提醒，凭单号取餐']}
        delay={6}
      />

      <SceneIndex index={5} />
    </SceneFade>
  );
}
