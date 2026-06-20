// App 根: v2 重构 — 一法一专页，路由 /m/{method}
// 依据: 前端重构指示v2-一法一专页
import { BrowserRouter, Route, Routes, Navigate, useParams } from "react-router-dom";
import { lazy, Suspense } from "react";
import { I18nProvider } from "./lib/i18n";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SEO } from "./components/SEO";
import { Layout } from "./components/Layout";

// Lazy-loaded pages for code-splitting
const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Result = lazy(() => import("./pages/Result").then((m) => ({ default: m.Result })));
const MethodInfo = lazy(() => import("./pages/MethodInfo").then((m) => ({ default: m.MethodInfo })));
const History = lazy(() => import("./pages/History").then((m) => ({ default: m.History })));
const About = lazy(() => import("./pages/About").then((m) => ({ default: m.About })));
const Daily = lazy(() => import("./pages/Daily").then((m) => ({ default: m.Daily })));
const FengShui = lazy(() => import("./pages/FengShui").then((m) => ({ default: m.FengShui })));
const Almanac = lazy(() => import("./pages/Almanac").then((m) => ({ default: m.Almanac })));
const Compatibility = lazy(() => import("./pages/Compatibility").then((m) => ({ default: m.Compatibility })));
const Cases = lazy(() => import("./pages/Cases").then((m) => ({ default: m.Cases })));
const BirthTimeRectifyPage = lazy(() => import("./pages/BirthTimeRectifyPage").then((m) => ({ default: m.BirthTimeRectifyPage })));
const CompassPage = lazy(() => import("./pages/CompassPage").then((m) => ({ default: m.default })));
const Reading = lazy(() => import("./pages/Reading").then((m) => ({ default: m.Reading })));
const ReadingHistory = lazy(() => import("./pages/ReadingHistory").then((m) => ({ default: m.ReadingHistory })));
const ResultSample = lazy(() => import("./pages/ResultSample").then((m) => ({ default: m.ResultSample })));
const NotFound = lazy(() => import("./pages/NotFound").then((m) => ({ default: m.NotFound })));
const DateSelect = lazy(() => import("./pages/DateSelect").then((m) => ({ default: m.DateSelect })));
const Knowledge = lazy(() => import("./pages/Knowledge").then((m) => ({ default: m.Knowledge })));
const DreamPage = lazy(() => import("./pages/DreamPage").then((m) => ({ default: m.DreamPage })));

// Method pages — v2 routes /m/{method}
const TarotPage = lazy(() => import("./pages/methods/TarotPage").then((m) => ({ default: m.TarotPage })));
const LiuyaoPage = lazy(() => import("./pages/methods/LiuyaoPage").then((m) => ({ default: m.LiuyaoPage })));
const XuankongPage = lazy(() => import("./pages/methods/XuankongPage").then((m) => ({ default: m.XuankongPage })));
const NumerologyPage = lazy(() => import("./pages/methods/NumerologyPage").then((m) => ({ default: m.NumerologyPage })));
const BaziPage = lazy(() => import("./pages/methods/BaziPage").then((m) => ({ default: m.BaziPage })));
const ZiweiPage = lazy(() => import("./pages/methods/ZiweiPage").then((m) => ({ default: m.ZiweiPage })));
const WesternPage = lazy(() => import("./pages/methods/WesternPage").then((m) => ({ default: m.WesternPage })));
const VedicPage = lazy(() => import("./pages/methods/VedicPage").then((m) => ({ default: m.VedicPage })));
const QimenPage = lazy(() => import("./pages/methods/QimenPage").then((m) => ({ default: m.QimenPage })));
const ChengguPage = lazy(() => import("./pages/methods/ChengguPage").then((m) => ({ default: m.ChengguPage })));
const MeihuaPage = lazy(() => import("./pages/methods/MeihuaPage").then((m) => ({ default: m.MeihuaPage })));
const BazhaiPage = lazy(() => import("./pages/methods/BazhaiPage").then((m) => ({ default: m.BazhaiPage })));
const LiurenPage = lazy(() => import("./pages/methods/LiurenPage").then((m) => ({ default: m.LiurenPage })));
const LenormandPage = lazy(() => import("./pages/methods/LenormandPage").then((m) => ({ default: m.LenormandPage })));
const XiaoliurenPage = lazy(() => import("./pages/methods/XiaoliurenPage").then((m) => ({ default: m.XiaoliurenPage })));
const TiebanPage = lazy(() => import("./pages/methods/TiebanPage").then((m) => ({ default: m.TiebanPage })));

// HePan & HeShen (合盘 + 合参)
const HePanPage = lazy(() => import("./pages/HePanPage").then((m) => ({ default: m.HePanPage })));
const HeShenPage = lazy(() => import("./pages/HeShenPage").then((m) => ({ default: m.HeShenPage })));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="space-y-3 text-center">
        <span className="paper-pulse" style={{ width: "1.5rem", height: "1.5rem", display: "inline-block" }} />
        <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>Loading...</div>
      </div>
    </div>
  );
}

export function App() {
  return (
    <I18nProvider>
      <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
        <ErrorBoundary>
          <SEO />
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<Home />} />

                {/* v2 一法一专页 — 核心路由 */}
                {/* 命类 */}
                <Route path="/m/bazi" element={<BaziPage />} />
                <Route path="/m/ziwei" element={<ZiweiPage />} />
                <Route path="/m/tieban" element={<TiebanPage />} />
                {/* 卜类 */}
                <Route path="/m/qimen" element={<QimenPage />} />
                <Route path="/m/liuyao" element={<LiuyaoPage />} />
                <Route path="/m/meihua" element={<MeihuaPage />} />
                <Route path="/m/liuren" element={<LiurenPage />} />
                <Route path="/m/xiaoliuren" element={<XiaoliurenPage />} />
                <Route path="/m/chenggu" element={<ChengguPage />} />
                {/* 相类 */}
                <Route path="/m/hepan" element={<HePanPage />} />
                <Route path="/m/tarot" element={<TarotPage />} />
                <Route path="/m/lenormand" element={<LenormandPage />} />
                <Route path="/m/western" element={<WesternPage />} />
                <Route path="/m/vedic" element={<VedicPage />} />
                <Route path="/m/numerology" element={<NumerologyPage />} />
                {/* 山类 */}
                <Route path="/m/bazhai" element={<BazhaiPage />} />
                <Route path="/m/xuankong" element={<XuankongPage />} />

                {/* 合参（用户主动发起） */}
                <Route path="/cases" element={<Cases />} />
                <Route path="/birth-time" element={<BirthTimeRectifyPage />} />
                <Route path="/compass" element={<CompassPage />} />
                <Route path="/heshen" element={<HeShenPage />} />

                {/* 旧路由重定向 */}
                <Route path="/cast" element={<Navigate to="/" replace />} />
                <Route path="/aggregate" element={<Navigate to="/heshen" replace />} />

                {/* 保留的二级页面 */}
                <Route path="/result" element={<Result />} />
                <Route path="/methods/:id" element={<MethodInfo />} />
                <Route path="/fengshui" element={<FengShui />} />
                <Route path="/history" element={<History />} />
                <Route path="/daily" element={<Daily />} />
                <Route path="/almanac" element={<Almanac />} />
                <Route path="/compatibility" element={<Compatibility />} />
                <Route path="/dateselect" element={<DateSelect />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/dream" element={<DreamPage />} />
                <Route path="/reading" element={<Reading />} />
                <Route path="/reading-history" element={<ReadingHistory />} />
                <Route path="/about" element={<About />} />

                {/* 旧 /method/* 路由 — 301 重定向到 /m/* */}
                <Route path="/method/:id" element={<MethodRedirect />} />

                <Route path="/result-sample" element={<ResultSample />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </I18nProvider>
  );
}

/** 旧 /method/{id} 重定向到 /m/{id} */
function MethodRedirect() {
  const { id } = useParams<{ id: string }>();
  if (!id) return <Navigate to="/" replace />;
  return <Navigate to={`/m/${id}`} replace />;
}
