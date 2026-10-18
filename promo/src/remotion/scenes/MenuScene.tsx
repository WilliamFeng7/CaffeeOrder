import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Backdrop, CopyBlock, PhoneEnter, SceneFade, SceneIndex, enter } from '../parts';
import { SheetScreen } from '../../components/screens/SheetScreen';
import { Icon } from '../../components/Icon';

export function MenuScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sheetProgress =
    frame < 58
      ? 0
      : frame < 86
        ? enter(frame, 58, 28)
        : frame < 202
          ? 1
          : 1 - enter(frame, 202, 26);

  const temp = frame > 120 ? '冰' : '热';
  const sugar = frame > 148 ? '半糖' : '标准';
  const added = frame >= 172;

  const cartIn = spring({
    frame: Math.max(0, frame - 222),
    fps,
    config: { damping: 16, stiffness: 140, mass: 0.7 },
  });

  return (
    <SceneFade duration={250}>
      <Backdrop />

      <PhoneEnter x={232} y={30} width={470} rotate={1.2} delay={2}>
        <div style={{ position: 'relative', height: '100%' }}>
          <SheetScreen sheetProgress={sheetProgress} temp={temp} sugar={sugar} added={added} />
          {frame >= 222 ? (
            <div
              className="phone-cart"
              style={{
                opacity: Math.min(1, cartIn * 1.4),
                transform: `translateY(${(1 - cartIn) * 34}px)`,
              }}
            >
              <span className="bag">
                <Icon name="bag" size={20} />
                <span className="bag-badge">1</span>
              </span>
              <span className="total">¥15.00</span>
              <span className="go">去结算</span>
            </div>
          ) : null}
        </div>
      </PhoneEnter>

      <CopyBlock
        x={1130}
        y={272}
        width={700}
        kicker="点一杯"
        kickerIndex="02"
        title={['温度、糖度，', '都按你的来。']}
        body="选项来自菜单本身，不写死。价格随选随变，加价写在旁边。"
        bullets={['热、冰，无糖到多糖', '售罄会提前标出', '加入购物车再一起结算']}
        delay={6}
      />

      <SceneIndex index={3} />
    </SceneFade>
  );
}
