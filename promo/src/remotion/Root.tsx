import { Composition } from 'remotion';
import { Promo, PROMO_DURATION, PROMO_FPS } from './Promo';

export function RemotionRoot() {
  return (
    <Composition
      id="Promo"
      component={Promo}
      durationInFrames={PROMO_DURATION}
      fps={PROMO_FPS}
      width={1920}
      height={1080}
    />
  );
}
