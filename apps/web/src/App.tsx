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
const NotFound = lazy(() => import("./pages/NotFound").then((m) => ({ default: m.NotFound })));
const DateSelect = lazy(() => import("./pages/DateSelect").then((m) => ({ default: m.DateSelect })));
const Knowledge = lazy(() => import("./pages/Knowledge").then((m) => ({ default: m.Knowledge })));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="space-y-3 text-center">
        <div className="w-8 h-8 mx-auto rounded-full border-2 border-dashed spin-slow"
          style={{ borderColor: "var(--gold-dim)" }} />
        <div className="text-xs" style={{ color: "var(--muted)" }}>Loading...</div>
      </div>
    </div>
  );
}

export function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
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
                <Route path="/about" element={<About />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </I18nProvider>
  );
}
