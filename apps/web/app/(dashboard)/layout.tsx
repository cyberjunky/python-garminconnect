import { DashboardNav } from "@/components/DashboardNav";
import pkg from "../../package.json";

function appVersion(): string {
  const sha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7);
  return sha ? `v${pkg.version} · ${sha}` : `v${pkg.version}`;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Saltar al contenido
      </a>
      <DashboardNav version={appVersion()} />
      <div className="app-main" id="main-content" tabIndex={-1}>
        {children}
      </div>
    </div>
  );
}
