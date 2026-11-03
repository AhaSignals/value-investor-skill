# value-investor-skill

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md)

## ¿Vale esta acción lo que cuesta hoy?

Investiga el negocio, comprueba las hipótesis de valoración y descubre qué tendría que ocurrir para justificar el precio. Un skill de investigación para tu asistente de IA, publicado por **[AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=es_methodology)**.

[Probar la demo en el navegador](https://ahasignals.com/value-investor-skill/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=es_demo) · [Ejemplo antes y después](docs/demo.md) · [Licencia MIT](LICENSE)

![Una acción ficticia a 40 dólares: el mismo precio, distintas hipótesis](assets/demo.svg)

### Empieza con Claude, GPT o DeepSeek

Pega las [instrucciones de investigación listas para usar](prompts/START_HERE.md) en Claude, ChatGPT o DeepSeek y pide una respuesta en español. No necesitas terminal. También hay un plugin para Claude Code y una instalación local para Codex. [Guía por aplicación](docs/hosts.md). Las herramientas que puedes ejecutar dependen de tu aplicación.

### Pruébalo en un minuto

Necesitas Python 3.9 o posterior. Esta **demo ficticia sin conexión** no requiere paquetes pip, claves API, datos de mercado de pago ni llamadas a modelos de IA.

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py demo --out output/demo
```

Abre `output/demo/before/research.html` y `output/demo/after/research.html`. En Windows puedes usar `py -3` en lugar de `python3`. Para repetir la demo, elige otra carpeta de salida: no se sobrescriben investigaciones existentes.

### Instala el skill

```bash
python3 scripts/install.py --host codex
# Claude Code:
python3 scripts/install.py --host claude
```

Vuelve a cargar los skills de tu asistente y pídele:

> Usa value-investor-skill para investigar esta empresa a partir de fuentes primarias. Explica en español qué hipótesis justifican su precio, qué pruebas las respaldan y qué evidencia en contra cambiaría la conclusión. No inventes los datos que falten.

El asistente necesita acceso a las fuentes o documentos que tú proporciones. Siguen vigentes los costes y las condiciones de tu servicio de IA y de los proveedores de datos. El instalador no sobrescribe instalaciones existentes.

### ¿Qué supone un precio de 40 dólares?

Estos valores por acción son hipótesis ficticias de valor presente.

| Escenario favorable | Escenario desfavorable | Peso favorable que da un precio de 40 dólares |
| ---: | ---: | ---: |
| 80 dólares | 20 dólares | 33,3 % |
| 60 dólares | 20 dólares | 50,0 % |

Cada fila es un cálculo independiente con dos estados. **Estos pesos no son probabilidades de un acontecimiento ni un intervalo de confianza.** La siguiente pregunta es qué evidencia respalda 80 dólares en lugar de 60.

Cuando se retira la fuente que respalda el calendario de lanzamiento en la demo, las valoraciones dependientes pasan a `NEEDS_REVIEW` y se deja de mostrar un nuevo resultado numérico. Se conservan la investigación original y los escenarios no afectados.

### Qué aporta AhaSignals

- Separa el precio de mercado de la economía de los escenarios. Cambiar el precio no cambia las valoraciones aportadas.
- Distingue la fecha de publicación de la de observación y registra qué cálculos dependen de cada fuente.
- Incluye efectivo, deuda, costes futuros, nuevo capital y dilución en un mismo cálculo por acción.
- Añade versiones sin borrar las conclusiones anteriores.
- Mantiene `NOT_ESTIMATED` cuando no hay una probabilidad validada y `NO_QUOTE` cuando no se emite una recomendación de inversión.

Esta versión ofrece cálculos de escenarios e historial de investigación. No analiza automáticamente todo el mercado, no estima probabilidades calibradas ni ofrece asesoramiento personalizado o ejecución de operaciones. Los metadatos declarados de las fuentes no autentican por sí solos su contenido.

### Sigue investigando

[Formato de entrada](references/input-contract.md) · [Protocolo de investigación](references/research-protocol.md) · [Fuentes y revisiones de AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=es_methodology) · [Comunicar una corrección de traducción](https://github.com/AhaSignals/value-investor-skill/issues)

Esta es una guía de inicio en español. La CLI, los informes generados y la especificación detallada siguen en inglés. El idioma de las respuestas de IA depende del servicio utilizado. Agradecemos las revisiones de traducción.

AhaSignals es un editor de investigación independiente. Uso exclusivo para investigación y educación; no constituye asesoramiento de inversión ni de negociación. Los nombres de terceros indican fuentes o compatibilidad, sin afiliación ni respaldo. El código y los datos ficticios originales usan la licencia MIT; no se conceden derechos de redistribución de documentos de terceros.
