import type { ReactElement } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { getToken } from './api';
import { LoginPage } from './pages/LoginPage';
import { AppShell } from './pages/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { ItemsHubPage } from './pages/ItemsHubPage';
import { ItemsGridPage } from './pages/ItemsGridPage';
import { ConsumptionPage } from './pages/ConsumptionPage';
import { RecommendSkinHubPage } from './pages/RecommendSkinHubPage';
import { RecommendSkinRoute } from './pages/RecommendSkinRoute';
import { TasksPage } from './pages/TasksPage';
import { ArtifactGuidePage } from './pages/ArtifactGuidePage';
import MechanicalLedgerPage from './pages/ledger/MechanicalLedgerPage';
import ItemCatalogPage from './pages/ledger/ItemCatalogPage';
import MechDailyReportPage from './pages/ledger/MechDailyReportPage';

function PrivateRoute({ children }: { children: ReactElement }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app"
        element={
          <PrivateRoute>
            <AppShell />
          </PrivateRoute>
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="items" element={<ItemsHubPage />} />
        <Route path="items/:categoryId" element={<ItemsGridPage />} />
        <Route path="cash" element={<ConsumptionPage />} />
        <Route path="ledger/catalog" element={<ItemCatalogPage />} />
        <Route path="ledger/daily" element={<MechDailyReportPage />} />
        <Route path="ledger" element={<MechanicalLedgerPage />} />
        <Route path="tasks/styles" element={<RecommendSkinHubPage />} />
        <Route path="tasks/style/:skinId" element={<RecommendSkinRoute />} />
        <Route path="tasks/backfill" element={<Navigate to="/app/tasks?tab=backfill" replace />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="guide/artifacts" element={<ArtifactGuidePage />} />
      </Route>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
