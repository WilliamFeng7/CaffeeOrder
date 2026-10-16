/**
 * photo.ts
 *
 * 商品图地址 (Product photo URLs).
 *
 * The bundled menu photos under /static/menu/ come in two widths:
 * `<name>.jpg` (1200px: the product sheet, the home feature) and
 * `<name>-640.jpg` (cards and thumbnails), so a 64px thumbnail no longer
 * downloads and decodes a 1200×900 photo. Uploaded images have one size and
 * are used for both. Where a small file is missing, v-img-fade falls back to
 * the full one (`data-full`).
 */
const MENU = '/static/menu/';

// The bundled photos were replaced in place (same names); the version tag makes
// browsers that cached the old ones fetch the new ones. Bump it whenever those
// files change.
const VERSION = '2';

const isMenuPhoto = (path: string) => path.startsWith(MENU) && path.endsWith('.jpg');

/** Full-size photo. */
export const photoUrl = (path?: string | null): string =>
  path && isMenuPhoto(path) ? `${path}?v=${VERSION}` : (path ?? '');

/** Card / thumbnail size of the same photo. */
export const thumbUrl = (path?: string | null): string =>
  path && isMenuPhoto(path) ? `${path.slice(0, -4)}-640.jpg?v=${VERSION}` : (path ?? '');
