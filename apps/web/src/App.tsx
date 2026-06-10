// App 根: ErrorBoundary + I18n + SEO + Lazy Routes + 13 路由
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { lazy, Suspense } from "react";
import { I18nProvider } from "./lib/i18n";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { SEO } from "./components/SEO";
import { Layout } from "./components/Layout";

// Lazy-loaded pages for code-splitting
const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Cast = lazy(() => import("./pages/Cast").then((m) => ({ default: m.Cast })));
const Result = lazy(() => import("./pages/Result").then((m) => ({ default: m.Result })));
const MethodInfo = lazy(() => import("./pages/MethodInfo").then((m) => ({ default: m.MethodInfo })));
const History = lazy(() => import("./pages/History").then((m) => ({ default: m.History })));
const About = lazy(() => import("./pages/About").then((m) => ({ default: m.About })));
const Daily = lazy(() => import("./pages/Daily").then((m) => ({ default: m.Daily })));
const FengShui = lazy(() => import("./pages/FengShui").then((m) => ({ default: m.FengShui })));
const Almanac = lazy(() => import("./pages/Almanac").then((m) => ({ default: m.Almanac })));
const Compatibility = lazy(() => import("./pages/Compatibility").then((m) => ({ default: m.Compatibility })));
const Reading = lazy(() => import("./pages/Reading").then((m) => ({ default: m.Reading })));
const ReadingHistory = lazy(() => import("./pages/ReadingHistory").then((m) => ({ default: m.ReadingHistory })));
const ResultSample = lazy(() => import("./pages/ResultSample").then((m) => ({ default: m.ResultSample })));
const NotFound = lazy(() => import("./pages/NotFound").then((m) => ({ default: m.NotFound })));
const DateSelect = lazy(() => import("./pages/DateSelect").then((m) => ({ default: m.DateSelect })));
const Knowledge = lazy(() => import("./pages/Knowledge").then((m) => ({ default: m.Knowledge })));

// Method pages
const TarotPage = lazy(() => import("./pages/methods/TarotPage").then((m) => ({ default: m.TarotPage })));
const LiuyaoPage = lazy(() => import("./pages/methods/LiuyaoPage").then((m) => ({ default: m.LiuyaoPage })));
const XuankongPage = lazy(() => import("./pages/methods/XuankongPage").then((m) => ({ default: m.XuankongPage })));
const NumerologyPage = lazy(() => import("./pages/methods/NumerologyPage").then((m) => ({ default: m.NumerologyPage })));
const BaziV2Page = lazy(() => import("./pages/methods/BaziV2Page").then((m) => ({ default: m.BaziV2Page })));
const BaziPage = lazy(() => import("./pages/methods/BaziPage").then((m) => ({ default: m.BaziPage })));
const ZiweiPage = lazy(() => import("./pages/methods/ZiweiPage").then((m) => ({ default: m.ZiweiPage })));
const WesternPage = lazy(() => import("./pages/methods/WesternPage").then((m) => ({ default: m.WesternPage })));
const VedicPage = lazy(() => import("./pages/methods/VedicPage").then((m) => ({ default: m.VedicPage })));
const QimenPage = lazy(() => import("./pages/methods/QimenPage").then((m) => ({ default: m.QimenPage })));
const ChengguPage = lazy(() => import("./pages/methods/ChengguPage").then((m) => ({ default: m.ChengguPage })));
const LiurenPage = lazy(() => import("./pages/methods/LiurenPage").then((m) => ({ default: m.LiurenPage })));
const TiebanPage = lazy(() => import("./pages/methods/TiebanPage").then((m) => ({ default: m.TiebanPage })));
const MeihuaPage = lazy(() => import("./pages/methods/MeihuaPage").then((m) => ({ default: m.MeihuaPage })));
const BazhaiPage = lazy(() => import("./pages/methods/BazhaiPage").then((m) => ({ default: m.BazhaiPage })));
const LenormandPage = lazy(() => import("./pages/methods/LenormandPage").then((m) => ({ default: m.LenormandPage })));
const XiaoliurenPage = lazy(() => import("./pages/methods/XiaoliurenPage").then((m) => ({ default: m.XiaoliurenPage })));

// Aggregate
const AggregatePage = lazy(() => import("./pages/AggregatePage").then((m) => ({ default: m.AggregatePage })));

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
                <Route path="/cast" element={<Cast />} />
                <Route path="/result" element={<Result />} />
                <Route path="/methods/:id" element={<MethodInfo />} />
                <Route path="/fengshui" element={<FengShui />} />
                <Route path="/history" element={<History />} />
                <Route path="/daily" element={<Daily />} />
                <Route path="/almanac" element={<Almanac />} />
                <Route path="/compatibility" element={<Compatibility />} />
                <Route path="/dateselect" element={<DateSelect />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/reading" element={<Reading />} />
                <Route path="/reading-history" element={<ReadingHistory />} />
                <Route path="/about" element={<About />} />
                {/* Method-specific pages */}
                <Route path="/method/bazi" element={<BaziPage />} />
                <Route path="/method/bazi-v2" element={<BaziV2Page />} />
                <Route path="/method/ziwei" element={<ZiweiPage />} />
                <Route path="/method/qimen" element={<QimenPage />} />
                <Route path="/method/liuyao" element={<LiuyaoPage />} />
                <Route path="/method/meihua" element={<MeihuaPage />} />
                <Route path="/method/chenggu" element={<ChengguPage />} />
                <Route path="/method/liuren" element={<LiurenPage />} />
                <Route path="/method/tieban" element={<TiebanPage />} />
                <Route path="/method/western" element={<WesternPage />} />
                <Route path="/method/vedic" element={<VedicPage />} />
                <Route path="/method/tarot" element={<TarotPage />} />
                <Route path="/method/lenormand" element={<LenormandPage />} />
                <Route path="/method/numerology" element={<NumerologyPage />} />
                <Route path="/method/xuankong" element={<XuankongPage />} />
                <Route path="/method/bazhai" element={<BazhaiPage />} />
                <Route path="/method/xiaoliuren" element={<XiaoliurenPage />} />
                {/* Aggregate */}
                <Route path="/aggregate" element={<AggregatePage />} />
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
