# Estándares y Arquitectura Docker - Scouter

Este proyecto (`scouter`) se adhiere estrictamente a los estándares y arquitectura Docker del workspace definidos a nivel global.

## 1. Política de Puertos Asignados

Para asegurar que los proyectos puedan convivir simultáneamente sin colisiones a nivel de host, se ha asignado un bloque secuencial de 100 puertos específicos para este proyecto.

**Bloque de Puertos Asignado para `scouter`:**
- **Rango:** `15900 - 15999`
- **Estado:** Activo

**Reglas de Oro:**
- Los puertos internos de los contenedores (ej. 3306, 6379, 8000) NO se modifican.
- La conectividad interna entre contenedores se resuelve vía DNS de Docker.
- Cualquier puerto expuesto al host en `docker-compose.yml` debe mapearse obligatoriamente dentro del rango **15900 al 15999**.

### Asignación Específica (Offset de Puertos)

Basado en el estándar de offset del workspace, los sufijos de puertos para este bloque (15900) se distribuyen de acuerdo a los servicios requeridos por `scouter`:

| Servicio | Offset | Puerto | Fase |
|---------------------------|--------|--------|----------|
| Next.js (Frontend) | +00 | 15900 | MVP |
| FastAPI (Backend) | +01 | 15901 | MVP |

## 2. Política de Higiene y Mantenimiento de Almacenamiento

- El mantenimiento del disco (Garbage Collection) está delegado directamente al demonio de Docker (`/etc/docker/daemon.json`), con un umbral de retención de **10 GB**.
- No se ejecutan comandos manuales (`docker builder prune`) para evitar poner en riesgo otros volúmenes.

## 3. Estandarización Estructural (Docker Compose)

El archivo `docker-compose.yml` de este proyecto respeta los siguientes estándares (arquitectura KISS):

1. **Sin Nombres Estáticos de Contenedor:** No se usa la directiva `container_name`. Compose asigna los nombres dinámicamente.
2. **Redes y Volúmenes Relativos:** No se nombran explícitamente los volúmenes o redes globales para evitar colisiones.
3. **Reutilización y DRY:** Se utilizan YAML Anchors (ej. `&app-base`) para centralizar la configuración.
4. **Sintaxis Moderna:** Se omite la directiva obsoleta `version:`.

## 4. Patrones Compose (Extension Fields)

- Los campos de extensión (`x-`) siempre se declaran en la raíz del documento `docker-compose.yml`, nunca dentro del bloque `services:`, para evitar que Compose levante servicios fantasma.
