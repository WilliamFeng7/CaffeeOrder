import { onMounted, onUnmounted, ref } from 'vue';

const SOUND_KEY = 'otia.barista.sound';

/**
 * 收银台 iPad 要的两件事。
 *
 * 屏幕常亮：iPadOS 一两分钟就会锁屏，新订单来了也看不见。页面切到后台时常亮会被系统收回，
 * 所以每次回到前台都重新申请一次。
 *
 * 提示音：iOS 只允许在用户点过屏幕之后发声，所以第一次点屏幕时启动一个 AudioContext，
 * 之后每次来新订单都用它。声音开关记在本机。
 */
export function useCounterDevice() {
    const soundOn = ref(readSoundSetting());
    /** iOS 上还没点过屏幕，暂时发不出声。 */
    const soundBlocked = ref(true);
    let audio: AudioContext | null = null;
    let lock: WakeLockSentinel | null = null;
    let requesting = false;

    async function keepAwake() {
        if (!('wakeLock' in navigator) || document.visibilityState !== 'visible' || lock || requesting) return;
        requesting = true;
        try {
            lock = await navigator.wakeLock.request('screen');
            lock.addEventListener('release', () => {
                lock = null;
            });
        } catch {
            // 有的浏览器要先点一下屏幕，下次点屏幕时再试。
        } finally {
            requesting = false;
        }
    }

    async function unlockAudio() {
        const Context = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!Context) return;
        audio ??= new Context();
        if (audio.state === 'suspended') {
            try {
                await audio.resume();
            } catch {
                // 下次点屏幕再试。
            }
        }
        soundBlocked.value = audio.state !== 'running';
    }

    /** 轻轻的"叮—咚"两声，总长不到 0.6 秒。 */
    function chime() {
        if (!soundOn.value || !audio || audio.state !== 'running') return;
        const start = audio.currentTime;
        tone(audio, 1046.5, start, 0.32);
        tone(audio, 784, start + 0.16, 0.42);
    }

    async function toggleSound() {
        soundOn.value = !soundOn.value;
        try {
            localStorage.setItem(SOUND_KEY, soundOn.value ? 'on' : 'off');
        } catch {
            // 记不住开关时只对本次打开有效。
        }
        if (soundOn.value) {
            await unlockAudio();
            chime();
        }
    }

    const onPointerDown = () => {
        void unlockAudio();
        void keepAwake();
    };
    const onVisibility = () => {
        if (document.visibilityState === 'visible') void keepAwake();
    };

    onMounted(() => {
        void keepAwake();
        window.addEventListener('pointerdown', onPointerDown, { passive: true });
        document.addEventListener('visibilitychange', onVisibility);
    });

    onUnmounted(() => {
        window.removeEventListener('pointerdown', onPointerDown);
        document.removeEventListener('visibilitychange', onVisibility);
        void lock?.release();
        lock = null;
        void audio?.close();
        audio = null;
    });

    return { soundOn, soundBlocked, chime, toggleSound, unlockAudio };
}

function readSoundSetting(): boolean {
    try {
        return localStorage.getItem(SOUND_KEY) !== 'off';
    } catch {
        return true;
    }
}

function tone(audio: AudioContext, frequency: number, start: number, length: number) {
    const oscillator = audio.createOscillator();
    const gain = audio.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.18, start + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + length);
    oscillator.connect(gain);
    gain.connect(audio.destination);
    oscillator.start(start);
    oscillator.stop(start + length + 0.02);
}
