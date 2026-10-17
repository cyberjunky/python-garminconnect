# Evidencia Safari Real — Matriz S (SPEC-002 §5, T-0025)

- **Navegador**: Safari 27.0.1 (`/Applications/Safari.app`)
- **User-Agent**: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0.1 Safari/605.1.15`
- **Zoom**: 100%
- **Servidor local aislado**: `http://127.0.0.1:3126` -> Next `http://127.0.0.1:3125` + fixture Supabase loopback `http://127.0.0.1:44199`
- **Checkpoint base**: `8139f9bb74c5d101f39ea303f34533a84c1486dd` (código base `aeaa5da9a02c0070cb4f4259da13f1cb27ba16ab`)

## 1. Comparativa Baseline vs Candidato (Defecto de centrado en 1600px)

| Estado | Ruta | Viewport (`clientWidth`) | `A` (`.app-main`) | `W` (`main`) | Padding izq/der | Margen izq / der (`Δ`) | Overflow global | Resultado P01 | Captura |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| Baseline (0.3.0) | `/` | 1600px | 1360px | 880px | 28/28px | 0px / 480px (`Δ=480px`) | 0px | FAIL (sesgo izq) | `baseline-inicio-1600.png` |
| Baseline (0.3.0) | `/` | 375px | 375px | 375px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | PASS | `baseline-inicio-375.png` |
| Baseline (0.3.0) | `/chat?conversation=layout-synthetic` | 1600px | — | chatMain 1600px / composer 880px | — | composer 340px / 340px (`Δ=0px`) | 0px | PASS | `baseline-chat-1600.png` |

## 2. Matriz S Candidata (14 celdas en Safari real, v0.4.0-rc.1)

| # | Ruta | `clientWidth` | `<=800px` | `A` (`.app-main`) | `W` (`main` / `.chat-main`) | Padding izq/der | Margen izq / der (`Δ`) | Overflow global | Scroll interno / Burbujas | P01/P02/P03 | Captura |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | `/` | 375px | true | 375px | 375px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | n/a | PASS | `candidate-inicio-375.png` |
| 2 | `/` | 800px | true | 800px | 800px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | n/a | PASS | `candidate-inicio-800.png` |
| 3 | `/` | 801px | false | 561px | 561px | 28/28px | 0px / 0px (`Δ=0px`) | 0px | n/a | PASS | `candidate-inicio-801.png` |
| 4 | `/` | 1600px | false | 1360px | 1120px | 28/28px | 120px / 120px (`Δ=0px`) | 0px | n/a | PASS | `candidate-inicio-1600.png` |
| 5 | `/retos` | 375px | true | 375px | 375px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | scrollWidth=680px, canReachEnd=true, docScrollX=0px | PASS | — |
| 6 | `/retos` | 1600px | false | 1360px | 1120px | 28/28px | 120px / 120px (`Δ=0px`) | 0px | scrollWidth=1024px, canReachEnd=true, docScrollX=0px | PASS | `candidate-retos-1600.png` |
| 7 | `/mesociclos` | 375px | true | 375px | 375px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | n/a | PASS | — |
| 8 | `/mesociclos` | 1600px | false | 1360px | 1120px | 28/28px | 120px / 120px (`Δ=0px`) | 0px | n/a | PASS | `candidate-mesociclos-1600.png` |
| 9 | `/70-3-cartagena` | 375px | true | 375px | 375px | 16/16px | 0px / 0px (`Δ=0px`) | 0px | n/a | PASS | — |
| 10 | `/70-3-cartagena` | 1600px | false | 1360px | 1120px | 28/28px | 120px / 120px (`Δ=0px`) | 0px | n/a | PASS | `candidate-cartagena-1600.png` |
| 11 | `/chat?conversation=layout-synthetic` | 375px | true | — | 375px | 0/0px | 0px / 0px (`Δ=0px`) | 0px | composer=335px (Δm=0px), user=flex-end, assistant=flex-start | PASS | `candidate-chat-375-historial.png` |
| 12 | `/chat?conversation=layout-synthetic` | 800px | true | — | 800px | 0/0px | 0px / 0px (`Δ=0px`) | 0px | composer=760px (Δm=0px), user=flex-end, assistant=flex-start | PASS | — |
| 13 | `/chat?conversation=layout-synthetic` | 801px | false | — | 801px | 0/0px | 0px / 0px (`Δ=0px`) | 0px | composer=761px (Δm=0px), user=flex-end, assistant=flex-start | PASS | — |
| 14 | `/chat?conversation=layout-synthetic` | 1600px | false | — | 1600px | 0/0px | 340px / 340px (`Δ=0px`) | 0px | composer=880px (Δm=0px), user=flex-end, assistant=flex-start | PASS | `candidate-chat-1600.png` |

## 3. Ciclo de Navegación P03 (375px y 1600px)

| Viewport | Paso | Ruta destino | Resultado |
|---|---|---|---|
| 375x812 | `dashboard:/` | `/` | PASS |
| 375x812 | `dashboard:/retos` | `/retos` | PASS |
| 375x812 | `dashboard:/mesociclos` | `/mesociclos` | PASS |
| 375x812 | `dashboard:/70-3-cartagena` | `/70-3-cartagena` | PASS |
| 375x812 | `chat:open-with-id` | `/chat?conversation=layout-synthetic` | PASS |
| 375x812 | `chat:history-open` | `/chat?conversation=layout-synthetic` | PASS |
| 375x812 | `chat:select-history-item` | `/chat?conversation=layout-synthetic-history-2` | PASS |
| 375x812 | `chat:back-to-dashboard` | `/` | PASS |
| 1600x900 | `dashboard:/` | `/` | PASS |
| 1600x900 | `dashboard:/retos` | `/retos` | PASS |
| 1600x900 | `dashboard:/mesociclos` | `/mesociclos` | PASS |
| 1600x900 | `dashboard:/70-3-cartagena` | `/70-3-cartagena` | PASS |
| 1600x900 | `chat:open-with-id` | `/chat?conversation=layout-synthetic` | PASS |
| 1600x900 | `chat:history-open` | `/chat?conversation=layout-synthetic` | PASS |
| 1600x900 | `chat:select-history-item` | `/chat?conversation=layout-synthetic-history-2` | PASS |
| 1600x900 | `chat:back-to-dashboard` | `/` | PASS |
