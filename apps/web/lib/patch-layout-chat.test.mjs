import { register } from "node:module";

// Registrador de TypeScript y alias '@/...'
register(new URL("../tests/chat-server/ts-resolver.mjs", import.meta.url));

// Suites de pruebas para SPEC-004 (I-PATCH-051)
await import("../tests/patch-layout-chat/metrics-geometry.test.mjs");
await import("../tests/patch-layout-chat/layout-hierarchy.test.mjs");
await import("../tests/patch-layout-chat/viewmodel-token-sync.test.mjs");
await import("../tests/patch-layout-chat/history-merge.test.mjs");
