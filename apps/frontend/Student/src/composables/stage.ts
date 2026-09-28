/**
 * stage.ts
 *
 * 有几个面板正开着 (How many sheets are open). StudentLayout pushes the app
 * back while any sheet is up; sheets that live deeper in the tree (edit
 * profile, change password) report themselves here.
 */
import { ref } from 'vue';

export const openSheets = ref(0);
