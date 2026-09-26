import { onMounted, onUnmounted, ref } from 'vue';

/**
 * Things a wall-mounted kitchen iPad needs that a desktop tab does not.
 *
 * Screen wake lock: iPadOS dims and locks the screen after a minute or two, so
 * new orders arrived on a black screen. The lock is dropped whenever the page is
 * hidden, so it is requested again on every return to the foreground.
 *
 * Audio unlock: iOS only lets a page play sound from an AudioContext that was
 * started inside a user gesture. The old beep built a fresh context per order,
 * outside any gesture, so on the iPad it was always silent. One shared context
 * is resumed on the first tap and reused for every beep.
 */
export function useKitchenDevice() {
    const awake = ref(false);
    const soundReady = ref(false);
    let lock: WakeLockSentinel | null = null;
    let requesting = false;
    let audio: AudioContext | null = null;

    const requestWakeLock = async () => {
        if (!('wakeLock' in navigator) || document.visibilityState !== 'visible' || lock || requesting) return;
        requesting = true;
        try {
            lock = await navigator.wakeLock.request('screen');
            awake.value = true;
            lock.addEventListener('release', () => {
                lock = null;
                awake.value = false;
            });
        } catch {
            // Not allowed yet (some browsers want a tap first); retried on the next tap.
        } finally {
            requesting = false;
        }
    };

    const unlockAudio = () => {
        const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!Ctx) return;
        audio ??= new Ctx();
        const ctx = audio;
        if (ctx.state === 'suspended') {
            void ctx.resume().then(() => { soundReady.value = ctx.state === 'running'; });
        } else {
            soundReady.value = ctx.state === 'running';
        }
    };

    const onTouch = () => {
        unlockAudio();
        void requestWakeLock();
    };

    const onVisibility = () => {
        if (document.visibilityState === 'visible') void requestWakeLock();
    };

    /** Short 800Hz beep; silent until the screen has been touched once. */
    const beep = () => {
        if (!audio || audio.state !== 'running') return;
        const oscillator = audio.createOscillator();
        const gain = audio.createGain();
        oscillator.connect(gain);
        gain.connect(audio.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gain.gain.setValueAtTime(0.3, audio.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + 0.3);
        oscillator.start(audio.currentTime);
        oscillator.stop(audio.currentTime + 0.3);
    };

    onMounted(() => {
        void requestWakeLock();
        window.addEventListener('pointerdown', onTouch, { passive: true });
        document.addEventListener('visibilitychange', onVisibility);
    });

    onUnmounted(() => {
        window.removeEventListener('pointerdown', onTouch);
        document.removeEventListener('visibilitychange', onVisibility);
        void lock?.release();
        lock = null;
        void audio?.close();
        audio = null;
        soundReady.value = false;
    });

    return { awake, soundReady, beep };
}
