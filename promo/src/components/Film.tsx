import { useCallback, useEffect, useRef, useState } from 'react';
import { Player, type PlayerRef } from '@remotion/player';
import { Icon } from './Icon';
import { Promo, PROMO_DURATION } from '../remotion/Promo';
import poster from '../assets/poster.jpg';

const FPS = 30;

function clock(seconds: number) {
  const s = Math.max(0, Math.min(PROMO_DURATION / FPS, seconds));
  return `00:${String(Math.floor(s)).padStart(2, '0')}`;
}

const CHAPTERS = [
  { label: '打开钉钉', at: 0.2 },
  { label: '点一杯', at: 10 },
  { label: '去取餐', at: 24.5 },
];

export function Film() {
  const playerRef = useRef<PlayerRef>(null);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const [playing, setPlaying] = useState(true);
  const [frame, setFrame] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const reduceMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const [hasStarted, setHasStarted] = useState(false);
  const [muted, setMuted] = useState(true);
  const [posterReady, setPosterReady] = useState(false);

  useEffect(() => {
    const player = playerRef.current;
    if (!player) return;
    const onTime = (event: { detail: { frame: number } }) => {
      setFrame(event.detail.frame);
      if (event.detail.frame > 0) setHasStarted(true);
    };
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    player.addEventListener('timeupdate', onTime);
    player.addEventListener('play', onPlay);
    player.addEventListener('pause', onPause);
    return () => {
      player.removeEventListener('timeupdate', onTime);
      player.removeEventListener('play', onPlay);
      player.removeEventListener('pause', onPause);
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => setPosterReady(true), 700);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const onChange = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener('fullscreenchange', onChange);
    return () => document.removeEventListener('fullscreenchange', onChange);
  }, []);

  const toggleSound = useCallback(() => {
    const player = playerRef.current;
    if (!player) return;
    if (muted) {
      player.unmute();
      setMuted(false);
    } else {
      player.mute();
      setMuted(true);
    }
  }, [muted]);

  const toggle = useCallback(() => {
    const player = playerRef.current;
    if (!player) return;
    if (player.isPlaying()) player.pause();
    else player.play();
  }, []);

  const seek = (seconds: number) => {
    const player = playerRef.current;
    if (!player) return;
    player.seekTo(Math.round(seconds * FPS));
    player.play();
  };

  const toggleFullscreen = async () => {
    const node = frameRef.current;
    if (!node) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await node.requestFullscreen();
    } catch {
      /* Fullscreen is a nicety; the player still works. */
    }
  };

  const progress = Math.min(1, frame / PROMO_DURATION);

  return (
    <div className="film" id="film">
      <div className="film-head wrap">
        <div>
          <p className="kicker">
            <b>02</b> · 宣传片
          </p>
          <h2 className="section-title">
            38 秒，<br />
            认识你的学生端。
          </h2>
        </div>
        <div className="film-note">
          <p>从打开钉钉，到柜台取餐。一杯咖啡的完整路径，都在这一小段里。</p>
          <span>原创配乐 · 1080p · 38s · 默认静音</span>
        </div>
      </div>

      <div className="film-stage wrap">
        <div className="film-frame" ref={frameRef} role="region" aria-label="OTIA Café 学生端宣传片">
          <Player
            ref={playerRef}
            component={Promo}
            durationInFrames={PROMO_DURATION}
            compositionWidth={1920}
            compositionHeight={1080}
            fps={FPS}
            autoPlay={!reduceMotion}
            loop
            initiallyMuted
            controls={false}
            clickToPlay={false}
            doubleClickToFullscreen={false}
            style={{ width: '100%', height: '100%', background: 'transparent', position: 'relative', zIndex: 1 }}
          />
          {posterReady && !hasStarted ? (
            <button
              type="button"
              className="film-poster"
              style={{ backgroundImage: `linear-gradient(rgba(12,31,26,0.28), rgba(12,31,26,0.28)), url(${poster})` }}
              onClick={() => {
                playerRef.current?.seekTo(0);
                playerRef.current?.unmute();
                setMuted(false);
                playerRef.current?.play();
              }}
              aria-label="播放宣传片"
            >
              <span className="film-poster-play">
                <Icon name="play" size={22} />
              </span>
            </button>
          ) : null}

          <div className="film-controls">
            <button type="button" className="film-play" onClick={toggle} aria-label={playing ? '暂停短片' : '播放短片'}>
              <Icon name={playing ? 'pause' : 'play'} size={14} />
            </button>
            <button
              type="button"
              className="film-track"
              aria-label="短片进度"
              onClick={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                seek(((event.clientX - rect.left) / rect.width) * (PROMO_DURATION / FPS));
              }}
            >
              <span className="film-fill" style={{ transform: `scaleX(${progress})` }} />
            </button>
            <span className="film-time">
              {clock(frame / FPS)} / {clock(PROMO_DURATION / FPS)}
            </span>
            <button type="button" className="film-fs" onClick={toggleFullscreen} aria-label="全屏">
              <Icon name="expand" size={15} />
            </button>
          </div>
        </div>

        <div className="film-chapters">
          {CHAPTERS.map((chapter, index) => (
            <button type="button" key={chapter.label} onClick={() => seek(chapter.at)}>
              <span>0{index + 1}</span>
              {chapter.label}
              <em>00:{String(Math.floor(chapter.at)).padStart(2, '0')}</em>
            </button>
          ))}
          <button
            type="button"
            className={`film-sound ${muted ? '' : 'is-on'}`}
            onClick={toggleSound}
            aria-pressed={!muted}
          >
            <Icon name={muted ? 'volume-off' : 'volume'} size={15} />
            {muted ? '开启声音' : '声音已开'}
          </button>
          <span className="film-caption">原创配乐 · 点章节直接跳转</span>
        </div>
      </div>
    </div>
  );
}
