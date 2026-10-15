<!-- Generado por IES-OS sync-adapters. Fuente canonica: contratos, skills y memoria del framework/proyecto. Edita las fuentes, no este archivo; 'python scripts/sync-adapters.py' detecta drift. -->


# Workflow: ies-init

Abrir o crear el proyecto IES y la sesion de trabajo.

## Pasos

1. Ejecuta `ies doctor` y confirma la raiz de control y el actor (fila context).
2. Ejecuta `ies init <RUTA>` con la ruta explicita del proyecto (en brownfield conserva tu .gitignore y anade el bloque de IES).
3. Revisa el status mostrado y las tasks activas.
4. Si es un proyecto nuevo, revisa y aprueba el baseline commit propuesto.
