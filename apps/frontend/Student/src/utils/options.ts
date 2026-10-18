import type { Language, SelectedOption } from '../types';

/** 商品和订单快照共用同一套规格显示；语言切换不需要重新请求。 */
export const optionsText = (options: SelectedOption[], lang: Language) =>
  options.map((option) => (lang === 'cn' ? option.name : option.nameEn || option.name)).join(' · ');
