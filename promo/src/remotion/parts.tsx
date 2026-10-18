import type { CSSProperties, ReactNode } from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { Icon, type IconName } from '../components/Icon';
import { Phone } from '../components/Phone';
import { IMG } from '../data';

export const PAPER = '#fafaf7';
export const FOREST = '#0c1f1a';
export const GREEN = '#1b5e47';
export const CREAM = '#f6f1e4';

export const EASE = Easing.bezier(0.23, 1, 0.32, 1);

export const photo = (file: string) => IMG(file);

export function enter(frame: number, delay = 0, duration = 30) {
  return interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: EASE,
  });
}

export function fadeStyle(progress: number, distance = 0): CSSProperties {
  return {
    opacity: progress,
    transform: distance ? `translate3d(0, ${(1 - progress) * distance}px, 0)` : undefined,
  };
}

export function MaskLine({
  progress,
  children,
  className = '',
}: {
  progress: number;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={`v-mask ${className}`}>
      <span style={{ transform: `translate3d(0, ${(1 - progress) * 108}%, 0)` }}>{children}</span>
    </span>
  );
}

export function SceneFade({
  duration,
  children,
  background = PAPER,
  fadeIn = 10,
  fadeOut = 10,
}: {
  duration: number;
  children: ReactNode;
  background?: string;
  fadeIn?: number;
  fadeOut?: number;
}) {
  const frame = useCurrentFrame();
  const opacity =
    fadeOut > 0
      ? interpolate(frame, [0, fadeIn, duration - fadeOut, duration], [0, 1, 1, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : interpolate(frame, [0, fadeIn], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
  return <AbsoluteFill style={{ background, opacity }}>{children}</AbsoluteFill>;
}

export function Backdrop({ variant = 'paper' }: { variant?: 'paper' | 'warm' | 'forest' }) {
  const background = variant === 'forest' ? FOREST : variant === 'warm' ? '#f4f0e7' : PAPER;
  return (
    <AbsoluteFill style={{ background }}>
      <div className="v-glow" />
      <div className="v-grain" />
    </AbsoluteFill>
  );
}

export function CopyBlock({
  x,
  y,
  width = 760,
  kicker,
  kickerIndex,
  title,
  body,
  bullets = [],
  delay = 0,
  accent = () => false,
}: {
  x: number;
  y: number;
  width?: number;
  kicker: string;
  kickerIndex?: string;
  title: string[];
  body: string;
  bullets?: string[];
  delay?: number;
  accent?: (line: string) => boolean;
}) {
  const frame = useCurrentFrame();
  const kickerIn = enter(frame, delay, 22);
  const bodyIn = enter(frame, delay + 22, 26);

  return (
    <div className="v-copy" style={{ left: x, top: y, width }}>
      <p className="v-kicker" style={fadeStyle(kickerIn, 18)}>
        {kickerIndex ? <b>{kickerIndex}</b> : null}
        {kicker}
      </p>
      <h2 className="v-title">
        {title.map((line, index) => (
          <MaskLine
            key={line}
            progress={enter(frame, delay + 4 + index * 5, 26)}
            className={accent(line) ? 'is-green' : ''}
          >
            {line}
          </MaskLine>
        ))}
      </h2>
      <p className="v-body" style={fadeStyle(bodyIn, 22)}>
        {body}
      </p>
      {bullets.length ? (
        <ul className="v-bullets">
          {bullets.map((bullet, index) => {
            const p = enter(frame, delay + 32 + index * 6, 22);
            return (
              <li key={bullet} style={fadeStyle(p, 16)}>
                <span className="v-check">
                  <Icon name="check" size={14} />
                </span>
                {bullet}
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

export function PhoneEnter({
  x,
  y,
  width,
  rotate = 0,
  delay = 0,
  children,
  float = true,
  scale = 1,
}: {
  x: number;
  y: number;
  width: number;
  rotate?: number;
  delay?: number;
  children: ReactNode;
  float?: boolean;
  scale?: number;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 200, stiffness: 84, mass: 0.95 },
  });
  const drift = float ? Math.sin((frame + delay) / 46) * 6 : 0;

  return (
    <div
      className="v-phone"
      style={{
        left: x,
        top: y,
        width,
        opacity: Math.min(1, progress * 1.6),
        transform: `translate3d(0, ${(1 - progress) * 110 + drift}px, 0) rotate(${rotate}deg) scale(${
          (0.93 + 0.07 * progress) * scale
        })`,
      }}
    >
      <Phone width={width}>{children}</Phone>
    </div>
  );
}

export function FloatTag({
  x,
  y,
  delay = 26,
  rotate = -3,
  children,
}: {
  x: number;
  y: number;
  delay?: number;
  rotate?: number;
  children: ReactNode;
}) {
  const frame = useCurrentFrame();
  const progress = enter(frame, delay, 28);
  return (
    <div
      className="v-float-tag"
      style={{
        left: x,
        top: y,
        opacity: progress,
        transform: `translate3d(0, ${(1 - progress) * 26}px, 0) rotate(${rotate}deg)`,
      }}
    >
      {children}
    </div>
  );
}

export function SceneIndex({ index, total = 6, light = false }: { index: number; total?: number; light?: boolean }) {
  return (
    <span className={`v-scene-index ${light ? 'is-light' : ''}`}>
      {String(index).padStart(2, '0')} <i>/</i> {String(total).padStart(2, '0')}
    </span>
  );
}

export function PhotoArch({
  x,
  y,
  width,
  height,
  file,
  className = '',
}: {
  x: number;
  y: number;
  width: number;
  height: number;
  file: string;
  className?: string;
}) {
  return (
    <div className={`v-arch ${className}`} style={{ left: x, top: y, width, height }}>
      <Img src={photo(file)} />
    </div>
  );
}
