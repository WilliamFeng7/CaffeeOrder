import { AbsoluteFill, Audio, Sequence } from 'remotion';
import { Intro } from './scenes/Intro';
import { HomeScene } from './scenes/HomeScene';
import { MenuScene } from './scenes/MenuScene';
import { CheckoutScene } from './scenes/CheckoutScene';
import { PickupScene } from './scenes/PickupScene';
import { Outro } from './scenes/Outro';
import bgm from '../assets/audio/otia-bgm.mp3';
import '../styles/tokens.css';
import '../styles/phone.css';
import '../styles/video.css';

export const PROMO_FPS = 30;
export const PROMO_DURATION = 1140;

const SCENES = [
  { from: 0, duration: 120, Component: Intro },
  { from: 110, duration: 220, Component: HomeScene },
  { from: 320, duration: 250, Component: MenuScene },
  { from: 560, duration: 220, Component: CheckoutScene },
  { from: 770, duration: 240, Component: PickupScene },
  { from: 1000, duration: 140, Component: Outro },
] as const;

export function Promo() {
  return (
    <AbsoluteFill className="video-root">
      <Audio src={bgm} />
      {SCENES.map(({ from, duration, Component }) => (
        <Sequence key={from} from={from} durationInFrames={duration} name={Component.name}>
          <Component />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
}
