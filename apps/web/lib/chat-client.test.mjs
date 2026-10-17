import { register } from "node:module";
register(new URL("../tests/chat-server/ts-resolver.mjs", import.meta.url));

await import("../tests/chat-client/architecture-viewmodel.test.mjs");
await import("../tests/chat-client/viewmodel-sync.test.mjs");
await import("../tests/chat-client/optin-import.test.mjs");
await import("../tests/chat-client/model-select-static.test.mjs");
await import("../tests/chat-client/login-auth.test.mjs");
await import("../tests/chat-client/layout-preservation.test.mjs");
