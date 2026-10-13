import { DashboardNav } from "@/components/DashboardNav";
import pkg from "../../package.json";

function appVersion(): string {
  const sha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7);
  return sha ? `v${pkg.version} · ${sha}` : `v${pkg.version}`;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <DashboardNav version={appVersion()} />
      <div className="app-main">{children}</div>
    </div>
  );
}
