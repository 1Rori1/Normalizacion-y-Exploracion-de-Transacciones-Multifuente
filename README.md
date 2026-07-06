# Normalizacion-y-Exploracion-de-Transacciones-Multifuente

## 1. Decisiones de Diseño y Arquitectura
- **Modularidad:** Separación limpia de la configuración (`config.json`), la lógica del motor (`normalizer.py`) y la capa de presentación (`app.py`).
- **Estrategia de Normalización:** Se usa Duck-Typing mediante firmas de llaves JSON para inferir automáticamente el origen del dato sin requerir headers explícitos.
- **Tratamiento de Inconsistencias:** Los errores no rompen la ejecución; se aíslan los registros corruptos (`INVALID`) guardando su traza de error para auditoría, mientras que los registros sanos avanzan hacia las métricas operativas.

## 2. Ajustes sobre Sugerencias de IA
- El diseño inicial proponía regex estrictas para montos. Se ajustó para manejar montos basados en enteros/centavos (Fuente B), dividiendo dinámicamente por 100 de forma condicional según la procedencia.
