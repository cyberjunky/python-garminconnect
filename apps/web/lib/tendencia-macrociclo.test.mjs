import { register } from "node:module";
register(new URL("../tests/chat-server/ts-resolver.mjs", import.meta.url));

import "../tests/tendencia-macrociclo/recommendations.test.mjs";
import "../tests/tendencia-macrociclo/macrocycle.test.mjs";
import "../tests/tendencia-macrociclo/trend-monthly.test.mjs";
import "../tests/tendencia-macrociclo/architecture.test.mjs";
