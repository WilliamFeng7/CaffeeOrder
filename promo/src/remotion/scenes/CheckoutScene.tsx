import { interpolate, useCurrentFrame } from 'remotion';
import { Backdrop, CopyBlock, PhoneEnter, SceneFade, SceneIndex } from '../parts';
import { CheckoutScreen } from '../../components/screens/CheckoutScreen';

export function CheckoutScene() {
  const frame = useCurrentFrame();
  const paid = frame >= 116;
  const pressing = frame >= 104 && frame < 113;
  const balance = interpolate(frame, [116, 138], [50, 35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneFade duration={220}>
      <Backdrop />

      <CopyBlock
        x={136}
        y={284}
        width={730}
        kicker="付款"
        kickerIndex="03"
        title={['学生卡里的钱，', '直接付。']}
        body="结算页就显示卡里余额。点一下，付款完成，订单同时到咖啡师端。"
        bullets={['不用扫码，不用输密码', '余额和总额都看得见', '每笔订单都能在「我的」查到']}
        delay={4}
      />

      <PhoneEnter x={1232} y={22} width={452} rotate={-1.6} delay={8}>
        <CheckoutScreen
          paid={paid}
          balance={balance}
          pressing={pressing}
          successProgress={interpolate(frame, [116, 132], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })}
        />
      </PhoneEnter>



      <SceneIndex index={4} />
    </SceneFade>
  );
}
