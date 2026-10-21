# TC-BL-001: cantidad negativa en OWASP Juice Shop

Un único caso Java / RestAssured / JUnit / Allure verifica la integridad del carrito a través del proxy ZAP. El proyecto adapta el enfoque RestAssured del ZIP de referencia; utiliza Maven Wrapper en lugar de Gradle. No copia las credenciales ni los escenarios de todo.ly (servicio diferente de Todoist).

## Resultado verificado

El 20 de octubre de 2026, Juice Shop 20.3.0 local respondió HTTP 200 a `quantity=-1` y devolvió `-1` en la consulta posterior del carrito. Una prueba pasó, sin fallos ni errores, en modo de **reproducción de vulnerabilidad**. La aplicación sigue siendo **VULNERABLE**. Se restableció la cantidad a 1. No se realizó ningún pedido ni pago.

La demo `https://demo.owasp-juice.shop/` devolvió 503 durante la preparación. Los resultados corresponden exclusivamente a la imagen oficial local; no acreditan un resultado sobre la demo pública. Todoist quedó fuera del alcance por elección del usuario.

## Ejecutar

Requisitos: Docker Desktop iniciado, JDK 17+, Python 3 para exportar ZAP y Allure CLI 2.46.1 para el HTML. Maven Wrapper descarga Maven 3.9.11. Las imágenes están fijadas en `compose.yaml`; los digests observados están en `evidence/image-digests.txt`.

```powershell
$env:JAVA_HOME = 'C:\ruta\al\jdk'
./scripts/run-lab.ps1
allure generate target/allure-results --clean -o output/allure-report
allure open output/allure-report
```

Linux/macOS: `docker compose up -d`, esperar disponibilidad, `./mvnw clean test`, `python3 scripts/export_zap.py` y los mismos comandos de Allure. El API de ZAP requiere cabecera `Host: zap` por el mapeo local del puerto 8090 a 8080. El ejecutor Java usa el proxy 127.0.0.1:8090; ZAP resuelve `juice-shop` dentro de la red de Compose.

En IntelliJ IDEA: abrir `pom.xml` como proyecto Maven, seleccionar JDK 17+, iniciar Docker Compose y ejecutar la configuración compartida **TC-BL-001 - Juice Shop**, o el método JUnit `negativeQuantityInOwnBasket`. La ejecución de consola fue verificada; la evidencia gráfica de ejecución en el IDE está pendiente por fallo de la herramienta de captura. No se presenta una captura simulada.

## Oráculo y regresión

El modo predeterminado `reproduce` solo pasa si la modificación responde 200 **y** un GET independiente confirma -1. `./mvnw test -Dexpectation=secure` exige HTTP 400/422 y que la cantidad se mantenga en 1; en la versión vulnerable se espera fallo. Cambiar el modo no cambia el número de casos. Las etiquetas de severidad en Allure son una prioridad de prueba; la severidad analítica del informe es provisional y no corresponde a un CVSS calculado.

Flujo: usuario efímero propio -> inicio de sesión -> agregar una unidad del producto 1 -> comprobar cantidad 1 -> PUT con cantidad -1 -> GET del carrito propio -> comprobar persistencia -> restablecer y comprobar cantidad 1. Las cuentas de laboratorio desaparecen al recrear el contenedor sin volúmenes. No se registra tráfico de autenticación en Allure; las exportaciones ZAP redactan JWT y contraseñas efímeras.

## Evidencia y alcance de ZAP

- `evidence/business-result.json`: observaciones de negocio y limpieza.
- `evidence/execution.log`, `evidence/junit-summary.txt`: ejecución real por consola.
- `output/allure-report/index.html`: reporte Allure generado (abrir mediante servidor HTTP).
- `output/zap/zap-report.html`, `output/zap/zap-alerts.json`: reporte nativo y alertas ZAP exportadas.
- `evidence/zap-summary.json`: agrupación y cola pasiva terminada.
- `output/pdf/informe-vulnerabilidad-juice-shop.pdf`: informe de entrega con caso, resultados y limitaciones.

ZAP realiza análisis **pasivo** del tráfico del caso. No se ejecuta spider ni escaneo activo. Su alerta CORS es una observación de configuración que requiere validación adicional, no prueba de robo de datos. La persistencia de la cantidad negativa la detecta la aserción Java, no una regla automática de ZAP.

## Repositorio de entrega

Destino Git configurado: https://github.com/nohpedro/vulneravity_test

La publicación y la visibilidad pública deben verificarse. Durante la preparación hubo HTTP 404 y posteriores fallos de conectividad a GitHub; el enlace no se presenta como publicación confirmada.

## Cierre

`docker compose stop` detiene el laboratorio conservando los contenedores. `docker compose down` elimina únicamente los contenedores y red de este proyecto, incluidos los datos efímeros del laboratorio. ZAP se expone solo en loopback, con API sin clave para uso local; no debe publicarse su puerto en redes externas.

## Referencias

- https://help.owasp-juice.shop/part1/running.html
- https://www.zaproxy.org/docs/api/
- https://www.zaproxy.org/docs/alerts/10098/
- https://allurereport.org/docs/junit-jupiter/
