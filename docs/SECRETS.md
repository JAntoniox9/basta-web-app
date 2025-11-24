# Manejo seguro de la clave de OpenAI

Nunca publiques tu `OPENAI_API_KEY` en el repositorio (ni en commits, ni en PRs). Usa estos patrones en lugar de escribir la clave real dentro del código o archivos versionados:

## Desarrollo local
- Mantén tu clave en un archivo `.env` que **no** se sube al repo (ya está en `.gitignore`).
- Carga la variable antes de arrancar la app: `export OPENAI_API_KEY="tu_clave"`.
- Si usas un gestor de procesos (uvicorn, gunicorn, npm scripts, etc.), configura la variable de entorno en el comando de arranque en lugar de escribirla en el código.

## Despliegue y CI/CD
- Define `OPENAI_API_KEY` como un **secreto** en tu plataforma (Heroku Config Vars, Vercel/Render Environment Variables, Railway Secrets, etc.).
- En GitHub Actions u otros pipelines, usa el almacén de **Secrets** y pásalo al job como variable de entorno (p. ej. `env: OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}`).
- Si empaquetas con Docker, inyecta la clave en tiempo de ejecución (`docker run -e OPENAI_API_KEY=...`) o usa Docker secrets/Compose env vars; no la escribas dentro de la imagen.

### Pasos concretos en GitHub
1. Ve a **Settings → Secrets and variables → Actions → New repository secret**.
2. Usa el nombre `OPENAI_API_KEY` y pega tu clave (nunca la subas al repo ni la copies a `.env.example`).
3. En tu workflow, expórtala al entorno del job:
   ```yaml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   ```
4. Si llamas a scripts manualmente en el workflow, pásala explícitamente al paso:
   ```yaml
   - name: Ejecutar pruebas
     env:
       OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
     run: python -m compileall app/events
   ```
5. Para despliegues automáticos (Heroku, Render, etc.), envía la variable desde el workflow al proveedor usando sus CLI/API en lugar de escribirla en archivos versionados.

## Buenas prácticas adicionales
- Rota la clave si sospechas que se expuso y elimina cualquier commit que la contenga.
- Limita permisos y cuota de la clave desde el panel de OpenAI.
- No compartas capturas o logs que incluyan la clave.
- Usa valores de ejemplo o placeholders en `.env.example` y documenta que no deben subirse.
