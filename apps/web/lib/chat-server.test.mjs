import { register } from "node:module";
register(new URL("../tests/chat-server/ts-resolver.mjs", import.meta.url));

import "../tests/chat-server/architecture.test.mjs";
import "../tests/chat-server/domain.test.mjs";
import "../tests/chat-server/use-cases.test.mjs";
import "../tests/chat-server/coach-provider.test.mjs";
import "../tests/chat-server/sanitized-logging.test.mjs";
import "../tests/chat-server/api-routes.test.mjs";
import "../../../supabase/tests/coach_history/schema_validation.test.mjs";
