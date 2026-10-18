# OTIA Café · 学生端宣传页与宣传片

这是一个独立的小项目，为 CoffeeOrder 的学生端做了一支 38 秒宣传片，以及一个面向学生的宣传页。它不依赖后端，也不需要登录；所有数据都是演示数据（价格、营业时间、菜单来自项目里的种子数据）。

## 产出

- `out/otia-cafe-promo.mp4`：38 秒成片，1920×1080，H.264，带原创配乐。
- `out/landing-hero.png`：宣传页首屏截图。
- `out/frame-pickup.jpg`：成片「制作完成」一帧。

## 打开

```bash
cd ~/Desktop/CoffeeOrder/promo
npm install
npm run dev
# http://localhost:5180
```

页面上的短片是真正的 Remotion 合成（不是录屏），用 `@remotion/player` 嵌在网页里，自动静音循环播放，也可以全屏、拖动进度、按章节跳转。

## 短片

```bash
npm run studio   # 打开 Remotion Studio，逐帧看 / 改
npm run render   # 导出 1920×1080 MP4 到 out/otia-cafe-promo.mp4
npm run bgm      # 重新合成 / 编码原创配乐
```

- 1920×1080，30fps，38 秒，1140 帧，带原创配乐。
- 六个场景：开场 → 打开钉钉 → 选规格 → 学生卡支付 → 取餐进度 → 结尾。
- 第一次 `render` 如果本机没有 Remotion 的 Chrome Headless Shell，会自动下载；也可以加
  `--browser-executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` 使用本机 Chrome。
- 所有图片都在 `src/assets/menu/`，来自后端 `static/menu`；视频和页面共用。配乐在 `src/assets/audio/`。

## 配乐

片子的 BGM 是为这个项目原创合成的，没有采样、没有版权问题：

- `src/assets/audio/otia-bgm.mp3`：38 秒，48 kHz 立体声，192 kbps，约 -16.5 LUFS。
- `scripts/make_bgm.py`：用 numpy 合成 felt piano、暖 pad、贝斯、刷鼓和黑胶底噪，按六个场景的时间点编排；改完脚本后重新生成 WAV，再用 ffmpeg 做响度归一化和 MP3 编码（命令在脚本顶部）。
- 网页播放器默认静音（浏览器不允许自动带声播放），点短片章节栏右侧的「开启声音」即可；导出的 MP4 自带音轨。

## 页面结构

```text
src/
  App.tsx                 宣传页：Hero / 流程 / 短片 / 功能 / 取餐 / 菜单 / 学生卡 / FAQ / CTA
  data.ts                 菜单、价格、功能点、取餐状态、营业时间
  components/
    Film.tsx              @remotion/player + 自定义播放控件 + 海报
    Phone.tsx             390×844 手机壳（按宽度缩放）
    screens/              首页、菜单、规格面板、结算、取餐（页面和短片共用）
    Reveal.tsx            IntersectionObserver 进场
  remotion/
    index.ts              Remotion 入口
    Root.tsx              Composition 注册
    Promo.tsx             时间线：六个 Sequence
    scenes/               六个场景
    parts.tsx             场景背景、标题入场、手机入场等
  styles/
    tokens.css            色彩 / 字体 / 动效 token
    page.css              宣传页
    phone.css             手机 UI
    video.css             短片排版
```

## 设计

- 直接沿用学生端的视觉系统：`#FAFAF7` 暖白、`#1B5E47` 森林绿、`#C8963E` 焦糖金、发丝线、12/16/24 圆角。
- 标题用 `New York / Songti SC`，正文用系统 SF / PingFang，不请求 Google Fonts。
- 动效沿用 `packages/shared/styles/motion.css` 的曲线：`cubic-bezier(0.23,1,0.32,1)`，进场慢、出场快；页面滚动用 IntersectionObserver，尊重 `prefers-reduced-motion`。
- 短片里手机 UI 是按学生端源码重建的 DOM（不是截图），所以文字、价格、进度都能逐帧控制。
- 价格、菜单、营业时段、状态术语均来自 `GLOSSARY.md` 与 `apps/backend/sql/mysql/V2__cafe.sql`。

## 需要改的地方

- 真实钉钉入口：页面里的「钉钉 → 工作台 → OTIA Café」和「复制打开路径」是提示，不是深链。学校提供 corpId / 应用地址后，把 `src/App.tsx` 里的入口换成真实 URL 即可。
- 演示姓名、学号、余额：`林同学 / 2024 0317 / ¥50.00`，在 `src/components/screens/` 与 `src/App.tsx` 中。
- 菜单价格：`src/data.ts`；同时改 `src/remotion/scenes/` 里出现的金额（当前拿铁 ¥15）。
- 页脚版本号：`学生端 v3.0`，在 `src/App.tsx`。

## 说明

- 没有修改 `apps/frontend/Student`、`apps/admin`、`apps/backend` 里的任何现有代码；`promo` 独立安装依赖、独立构建。
- 页面在 390 / 768 / 1024 / 1440 宽度下检查过，无横向滚动；图片、键盘焦点、`prefers-reduced-motion` 都处理了。
