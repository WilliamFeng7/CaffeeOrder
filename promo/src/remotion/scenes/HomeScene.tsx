import { Backdrop, CopyBlock, FloatTag, PhoneEnter, SceneFade, SceneIndex } from '../parts';
import { HomeScreen } from '../../components/screens/HomeScreen';
import { Icon } from '../../components/Icon';

export function HomeScene() {
  return (
    <SceneFade duration={220}>
      <Backdrop />

      <CopyBlock
        x={130}
        y={296}
        width={780}
        kicker="打开钉钉"
        kickerIndex="01"
        title={['你的菜单，', '已经在等你。']}
        body="不用下载，也不用再填一次学号。打开，就是你的账号。"
        bullets={['打开就是你的账号', '首页看到现在排队几单', '店长推荐直接点']}
        delay={4}
      />

      <FloatTag x={922} y={176} delay={30} rotate={-3.5}>
        <span className="tag-icon">
          <Icon name="chat" size={20} />
        </span>
        <div>
          <b>钉钉免登录</b>
          <small>学号已经带出来了</small>
        </div>
      </FloatTag>

      <PhoneEnter x={1190} y={40} width={460} rotate={-2.4} delay={10}>
        <HomeScreen />
      </PhoneEnter>

      <SceneIndex index={2} />
    </SceneFade>
  );
}
