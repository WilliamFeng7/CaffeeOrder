<script setup lang="ts">
/**
 * One icon set for Student / Admin / Barista: Phosphor line icons, inlined as
 * SVG (see src/icons.ts). Sized by the surrounding font size (1em) and colored
 * by `currentColor`, so `text-xl text-primary` works as it did for the old icon
 * font. Decorative by default; pass `label` when the icon carries meaning on its
 * own.
 *
 *   <AppIcon name="coffee" />                  regular (outline)
 *   <AppIcon name="coffee" weight="fill" />    selected / active state
 */
import { computed } from 'vue';
import { ICONS, type IconName, type IconWeight } from '../icons';

const props = withDefaults(defineProps<{
  name: IconName;
  weight?: IconWeight;
  size?: string | number;
  label?: string;
}>(), {
  weight: 'regular',
  size: '1em',
  label: undefined,
});

const paths = computed(() => ICONS[props.name]?.[props.weight] ?? ICONS[props.name]?.regular ?? []);
</script>

<template>
  <svg
    class="app-icon"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 256 256"
    :width="size"
    :height="size"
    fill="currentColor"
    focusable="false"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<style>
/* Unscoped on purpose. The defaults sit in :where() (zero specificity), so any
   utility on the icon (text-xl, hidden, block...) still wins; without a size
   class an icon is 24px, as it was with the old icon font. */
:where(.app-icon) {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: -0.125em;
  font-size: 1.5rem;
}

/* Padding goes around the glyph (as with the icon font), not inside a 1em box:
   Tailwind's border-box would squeeze a padded icon down to a dot. */
.app-icon {
  box-sizing: content-box;
}
</style>
