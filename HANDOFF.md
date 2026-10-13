# Handoff — shell del dashboard y collect en la nube

## 1. Objetivo

Dejar Fitness Coach con barra izquierda y, solo en Inicio, diálogo con GPT, últimas conversaciones y tarjeta Hoy. El botón Actualizar debe lanzar el collect de Garmin en GitHub Actions, sin Cursor.

## 2. Estado actual

Hecho en la rama `cursor/shell-chat-hoy-43bc` (PR 1, base `master`). Build de Next en `apps/web` pasa.

Verificado en producción (https://web-chi-eight-31.vercel.app), deploy manual del usuario: barra Hoy, Retos, Mesociclos y 70.3; chat y tarjeta Hoy en Inicio; Retos con preparación, sesión, atender, va bien, macrociclo y tendencia 14d. El token de dispatch ya está en Vercel. Tras renovar la sesión Garmin, el sitio mostró última actualización 2026-09-26 08:41 Bogotá y readiness VERDE.

No verificado en ese deploy: la etiqueta de versión al pie de la barra. El HTML público no contiene `v0.1.0`; ese cambio es el commit posterior al deploy. El chat con OpenAI no se probó de punta a punta.

## 3. Archivos tocados

- `apps/web/app/layout.tsx` — shell sidebar + main; pasa la versión al menú.
- `apps/web/app/globals.css` — columna izquierda a altura de viewport y estilos del chat.
- `apps/web/components/DashboardNav.tsx` — menú vertical, Actualizar con espera al job, versión al pie.
- `apps/web/app/page.tsx` — Inicio: chat, tarjeta Hoy, recuperación y regla del día.
- `apps/web/app/retos/page.tsx` — página nueva con las tarjetas de preparación y sesión.
- `apps/web/lib/dashboard.ts` — lectura de Supabase y textos de atender / va bien, compartida.
- `apps/web/components/TodayCard.tsx` — tarjeta Hoy extraída del grupo de Inicio.
- `apps/web/components/CoachChat.tsx` — compositor y últimas 4 conversaciones en el navegador.
- `apps/web/app/api/chat/route.ts` — respuesta de OpenAI con la condición leída en el servidor.
- `apps/web/lib/condition.ts` — snapshot de readiness, carga e índice para el prompt.
- `apps/web/app/api/refresh/route.ts` — dispara el workflow y consulta si el run terminó.
- `apps/web/lib/supabase.ts` — el cliente se crea al usarlo, no al importar.
- `apps/web/.env.example` — nombres de `ACTIONS_DISPATCH_TOKEN` y `OPENAI_API_KEY`.

## 4. Decisiones

- El chat y la tarjeta Hoy solo están en Inicio. Mesociclos y 70.3 ocupan el centro. Lo pidió Diego.
- Garmin no se llama desde Vercel. La sesión vive en el secreto `GARMINTOKENS_B64` de GitHub. Actualizar solo hace `workflow_dispatch` de `coaching-daily-collect.yml`.
- La API key de OpenAI y el PAT de Actions son variables de servidor en Vercel. No van al repo ni al navegador.
- El historial del chat queda en `localStorage` de ese navegador, no en Supabase.
- El índice del chat usa `apps/web/lib/preparation.ts` sobre la última fila de Supabase. Si los datos tienen más de 18 horas, el prompt pide decirlo.
- La versión visible es la de `apps/web/package.json` y, en Vercel, el SHA corto del commit.

## 5. Errores

- Build local: Supabase exigía la URL al importar el módulo de chat. Se aplazó la creación del cliente en `apps/web/lib/supabase.ts`.
- Actualizar decía que faltaba `ACTIONS_DISPATCH_TOKEN`. Diego creó un PAT fino con Actions en lectura y escritura y lo guardó en Vercel, Production. Hizo falta otro `vercel deploy --prod`.
- Luego el job fallaba: la sesión Garmin del secreto estaba vencida y no hay correo ni contraseña en GitHub. En el Mac, `scripts/refresh_garmin_session.py` imprimió `SESSION_OK` y se actualizó el secreto. El collect de la mañana del 26 sí escribió Supabase.
- Este agente no puede hacer `vercel deploy` ni `gh workflow run`: no hay sesión de Vercel y el token de GitHub del agente recibe 403 al disparar Actions.
- La versión no se ve porque el deploy público es anterior al commit que la agrega.

## 6. Pendientes

1. Publicar el commit de la versión y confirmar el texto al pie de la barra.
2. Definir `OPENAI_API_KEY` en Vercel (Production) y comprobar un mensaje del chat.
3. Fusionar el PR 1 a `master` cuando Diego lo acepte. El cron sigue en `master`; la UI nueva no.
4. Conectar el repo a Vercel si se quiere deploy en cada push. Hoy es manual.

## 7. Próximo paso

En el Mac, actualizar la rama y publicar producción. Recargar el sitio y mirar el pie izquierdo.

## 8. Comandos

Desde la raíz del repo, con la rama `cursor/shell-chat-hoy-43bc`:

- `git pull`
- `cd apps/web && npm install && npm run build`
- `cd apps/web && vercel deploy --prod`
- Renovar Garmin en el Mac y publicar el secreto: `./scripts/publish_garmin_tokens_secret.sh --run-collect` (repo `dalarconics/python-garminconnect`).

No hay tests de la UI. El collect de Garmin es el workflow Coaching Daily Collect en GitHub Actions.
