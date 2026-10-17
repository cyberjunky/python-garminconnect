# ADR-006: Seleccionar modelos por herramienta sin sustituir el entorno alternativo

- Estado: aceptado para configuracion por instruccion humana directa; calidad comparativa no evaluada.
- Fecha: 2026-10-17
- Task: T-0023
- Decision: DEC-008

## Contexto

El usuario utiliza Antigravity y Codex. Pidio conservar Gemini en Antigravity y
usar Astra 6 / High para HITL y Coordinator en Codex, con los mismos roles y gates
IES. El proyecto tenia activo Antigravity. IES mantiene un solo registro de
entorno/bindings por proyecto, no perfiles activos simultaneos ni autodeteccion.

## Decision

La seleccion de herramienta es explicita y reversible por CLI. Los bindings
activos siguen viviendo exclusivamente en `.ies/models.yaml`; el esfuerzo y
herramienta se materializan en `.ies/environment.yaml`. Estas recetas documentan
la instruccion aprobada, no son otro registro que el compilador consulte.

Codex, contexto actual:

```bash
IES_ACTOR=coordinator ies env set --tool codex --principal-model gpt-6-astra --principal-effort high --subagent-model gpt-6-astra --subagent-effort high --autonomy-default hitl
```

Antigravity, cuando el humano indique trabajar alli:

```bash
IES_ACTOR=coordinator ies env set --tool antigravity --principal-model gemini-3.8-flash --principal-effort high --subagent-model gemini-3.8-flash --subagent-effort high --autonomy-default hitl
```

Los subagentes Codex sin override usan como predeterminado el del principal,
materializado por el CLI porque el esquema requiere identificadores concretos.
No es una prohibicion de elegir otro modelo por task: cualquier diferencia se
declara bajo Working Discipline, sin cambiar roles, modos, techos ni autoridad.
En Antigravity se restauran los valores Gemini existentes antes de T-0023.
Si aparecen overrides por rol nuevos, conservarlos y resolver su traduccion
explicitamente antes de volver a usar estas recetas: el cambio de herramienta
del CLI no conserva automaticamente overrides del entorno anterior.

El Coordinator controla la seleccion compartida. Antes de compilar prompts de
un nuevo contexto comprueba `ies env show` y aplica la receta solo si hace falta.
Una instruccion humana de trabajar en Codex o Antigravity selecciona ese contexto
bajo esta politica; no requiere repetir aprobacion del mismo ajuste rutinario.
No cambiar entorno con tareas concurrentes que dependan del registro compartido;
mantener el prompt ya emitido y declarar una excepcion de transporte por task si
hay dos aplicaciones abiertas. No escribir el ledger manualmente.

HITL es la ventana de consulta/instrucciones del humano, no un rol nuevo del
registry. Coordinator crea y despacha tasks, no implementa. Planner especifica,
Implementer codifica/tests en worktree y Viewer verifica independientemente.
SDLC por contrato, EARS, Clean Code, Clean Architecture, HITL por gate y Working
Discipline son invariantes. La delegacion requiere task/prompt por agente;
paralelismo solo con allowlists y aislamiento efectivos.

El modelo del producto es independiente: GPT-6 Luna High exclusivo sigue como
requisito de T-0022. Ningun cambio de herramienta selecciona Astra para el chat.

## Evidencia y limites

- `ies env set` actualizo Codex y sus bindings; prompts de coordinator/planner
  compilan con `openai/gpt-6-astra` y esfuerzo High.
- La receta Antigravity, ejecutada en copia temporal aislada, reconstruyo
  exactamente el registro previo completo de modelos y paso validacion.
- Roles ajenos al equipo SDD, proveedores, configuracion MLX, tier, modos y techos
  conservados; 64 adaptadores/protegidos mantuvieron su hash.
- No se editaron contratos ni el catalogo global del framework. La etiqueta
  `native_subagents: false` sigue viniendo de ese catalogo; las delegaciones
  nativas de T-0021/T-0022 son evidencia de transporte disponible en esta sesion,
  no de aislamiento futuro. La etiqueta no concede ni quita permisos de rol.
- No se hicieron llamadas de inferencia ni evals comparativas de calidad/costo;
  configurar no demuestra equivalencia ni modelo efectivo de sesiones abiertas.
  Las futuras entregas registran evidencia de calidad por su task, sin sustituir
  esta limitacion por un PASS ficticio de migracion de modelos.

## Alternativas y consecuencias

Reemplazar globalmente Gemini viola la eleccion del usuario. Mantener Gemini
como activo durante Codex vuelve ambiguos los prompts. Inventar un archivo de
perfiles sin soporte del compilador daria apariencia falsa de seleccion automatica.
Se elige la conmutacion nativa existente, con politica persistida y backup local.

El selector de HITL/Coordinator abiertos se verifica en su propia sesion; este
ADR y YAML no pueden cambiarlo. Identidad diferente/no observable se registra
NON_BLOCKING segun Working Discipline; ausencia real de herramientas, permisos o
aislamiento conserva los gates. El flag descriptivo obsoleto no abre trabajo en
el framework ni bloquea el producto por su cuenta.

## Reversion

Para volver a Antigravity usar la receta anterior; el ensayo de T-0023 verifico
igualdad con baseline. Backup completo de environment/models y evidencias:
`.ies/backups/T-0023-context-20261017T121142Z/`. No restaura codigo, datos o ledger
ni deshace aprobaciones. La tarea de configuracion no aprueba SPEC-002.
