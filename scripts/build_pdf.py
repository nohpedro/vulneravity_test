"""Build the Spanish evidence report from the actual laboratory outputs."""
from pathlib import Path
import json
import hashlib
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/informe-vulnerabilidad-juice-shop.pdf'
result = json.loads((ROOT/'evidence/business-result.json').read_text())
zap = json.loads((ROOT/'evidence/zap-summary.json').read_text())
allure = json.loads((ROOT/'output/allure-report/widgets/summary.json').read_text())
fontdir = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Body', str(fontdir/'arial.ttf')))
pdfmetrics.registerFont(TTFont('BodyBold', str(fontdir/'arialbd.ttf')))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
NAVY = colors.HexColor('#143047'); TEAL=colors.HexColor('#007E87'); MUTED=colors.HexColor('#546577')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyCustom', fontName='Body', fontSize=10, leading=14, textColor=NAVY, spaceAfter=9))
styles.add(ParagraphStyle(name='SmallCustom', parent=styles['BodyCustom'], fontSize=8.5, leading=11, spaceAfter=5))
styles.add(ParagraphStyle(name='TitleCustom', fontName='BodyBold', fontSize=28, leading=32, textColor=NAVY, spaceAfter=18))
styles.add(ParagraphStyle(name='HeadingCustom', fontName='BodyBold', fontSize=18, leading=22, textColor=NAVY, spaceAfter=14))
styles.add(ParagraphStyle(name='SubCustom', fontName='BodyBold', fontSize=12, leading=16, textColor=TEAL, spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='CodeCustom', fontName='Courier', fontSize=8, leading=11, textColor=NAVY, backColor=colors.HexColor('#EFF4F7'), borderPadding=10, spaceAfter=12))
flow=[]
def p(text, small=False):
    return Paragraph(text, styles['SmallCustom' if small else 'BodyCustom'])
def add(text, small=False): flow.append(p(text,small))
def title(n,text):
    add(f'<font color="#007E87"><b>INFORME TÉCNICO / {n:02d}</b></font>',True)
    flow.append(Paragraph(text,styles['HeadingCustom']))
def sub(text): flow.append(Paragraph(text,styles['SubCustom']))
def code(text): flow.append(Preformatted(text,styles['CodeCustom']))
def table(rows,widths,header=True):
    cells=[[p(escape(str(x)).replace('\n','<br/>'),True) for x in row] for row in rows]
    t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1 if header else 0)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#EFF4F7'),colors.white]),('LINEBELOW',(0,0),(-1,0),1,TEAL)]))
    flow.extend([t,Spacer(1,10)])
def shot(name,maxheight=390):
    im=Image(str(ROOT/'evidence'/name)); ratio=min(499/im.imageWidth,maxheight/im.imageHeight)
    im.drawWidth=im.imageWidth*ratio; im.drawHeight=im.imageHeight*ratio
    im.hAlign='LEFT'; flow.extend([im,Spacer(1,9)])
def nextpage(): flow.append(PageBreak())
repo='https://github.com/nohpedro/vulneravity_test'

add('<b>PRUEBA DE VULNERABILIDAD / FLUJO DE NEGOCIO</b>',True)
flow.append(Spacer(1,25))
flow.append(Paragraph('Integridad del carrito<br/>OWASP Juice Shop',styles['TitleCustom']))
add('TC-BL-001 · Manipulación de cantidades · 20 de octubre de 2026')
add('Entorno local oficial 20.3.0 · Java + RestAssured + JUnit + Allure + ZAP')
flow.append(Spacer(1,14))
table([['Automatización','Resultado de seguridad','ZAP pasivo'],['1 prueba aprobada\n0 fallos / 0 errores','VULNERABLE\nquantity = -1 persistida','1 tipo de alerta media\n2 tipos informativos']],[166,167,166])
sub('Resultado principal')
add('La API aceptó una cantidad negativa en el carrito del usuario de prueba. Una lectura independiente confirmó la persistencia de <b>-1</b>. El valor inicial y la cantidad restablecida fueron <b>1</b>. La automatización pasó porque su objetivo es reproducir y documentar la debilidad.')
sub('Estado de la entrega')
add('<b>Completados:</b> caso, código ejecutable, ejecución satisfactoria por consola, reporte Allure, reporte ZAP y este documento con evidencias.')
add('<b>Pendientes de acreditación:</b> captura de ejecución satisfactoria dentro de IntelliJ IDEA y publicación/verificación de visibilidad pública en GitHub. Este documento no acredita esos dos requisitos como cumplidos.')
sub('Enlace del repositorio de destino')
add(f'<link href="{repo}" color="#007E87">{repo}</link>')
add('Es la URL configurada como origin en el proyecto. La consulta pública inicial devolvió 404; otras conexiones a GitHub agotaron su tiempo. Publicación y acceso público no confirmados.',True)
add('La demo solicitada respondió HTTP 503; las pruebas documentadas se ejecutaron sobre la imagen oficial local. Todoist quedó excluido por la selección expresa del usuario.',True)

nextpage();title(2,'Caso de prueba y criterios')
table([['Campo','Definición'],['ID / objetivo','TC-BL-001. Comprobar que una cantidad negativa no pueda alterar la integridad del carrito.'],['Alcance','Únicamente el carrito del usuario efímero creado por el caso; sin pedidos, pagos ni modificación de usuarios ajenos.'],['Precondiciones','Docker activo; Juice Shop 20.3.0 y ZAP 2.17.0 listos; producto 1 disponible; JDK 17+; dependencias Maven.'],['Datos','Producto 1; cantidad inicial 1; cantidad inválida -1. Usuario qa-UUID@example.invalid y contraseña aleatoria generada en memoria.'],['Regla de negocio','La cantidad debe ser un entero positivo. Una petición inválida debe rechazarse sin modificar la cantidad válida.'],['Resultado seguro esperado','HTTP 400 o 422; GET posterior conserva quantity=1.'],['Oráculo de reproducción','Solo PASS si PUT devuelve 200 y GET posterior devuelve quantity=-1. No basta el estado HTTP.']],[110,389])
table([['Paso','Acción','Verificación'],['1','Registrar usuario e iniciar sesión','Registro 201; login 200; token y carrito propios.'],['2','POST /api/BasketItems con cantidad 1','HTTP 200; GET /rest/basket/{id} devuelve 1.'],['3','PUT /api/BasketItems/{id} con -1','Registrar estado HTTP y respuesta.'],['4','GET independiente del carrito','Confirmar persistencia negativa o rechazo seguro.'],['5','Restablecer cantidad 1','PUT 200 y GET confirma 1.']],[38,250,211])
add('El caso se automatiza en un único método JUnit. Sus pasos y evidencias se registran en Allure. ZAP inspecciona el mismo flujo HTTP de forma pasiva; no ejecuta spider ni ataques automáticos.',True)

nextpage();title(3,'Evidencia del defecto y ejecución')
table([['Dato observado','Resultado'],['Ejecución final (Bolivia, UTC-4)','20/10/2026, 20:49:54 - 20:49:56'],['Carrito / ítem',f"{result['basketId']} / {result['itemId']} (propios del usuario efímero)"],['Antes / después / restablecido','1 / -1 / 1'],['PUT de manipulación',f"HTTP {result['mutationHttpStatus']}"],['Precio unitario / cálculo de línea',f"{result['unitPrice']:.2f} / {result['calculatedLineTotal']:.2f}"],['Estado final','VULNERABLE; limpieza quantity_restored_to_1']],[175,324])
code(f'PUT /api/BasketItems/{result["itemId"]}\nContent-Type: application/json\nAuthorization: Bearer [OMITIDO]\n\n{{"quantity": -1}}\n\nRespuesta: HTTP 200\nGET /rest/basket/{result["basketId"]}\nCampo observado: data.Products[0].BasketItem.quantity = -1')
add('El importe -1,99 se calcula como precio × cantidad a partir de los datos leídos. No se ejecutó checkout: no se demuestra un cargo, abono ni pérdida monetaria real.')
sub('Salida real del ejecutor Maven')
code('TC-BL-001: VULNERABLE\nTests run: 1, Failures: 0, Errors: 0, Skipped: 0\nTime elapsed: 2.448 s -- in security.NegativeQuantityTest\nBUILD SUCCESS\nTotal time: 9.167 s')
add('Fuente: evidence/execution.log y evidence/junit-summary.txt. La duración de suite incluye preparación; Allure informa 2,261 s para el caso.',True)
sub('Ejecución en el IDE: requisito pendiente')
add('IntelliJ IDEA 2026.2.3 está instalado. La herramienta de escritorio falló al capturar su ventana en dos intentos (FrameArrived / window capture timed out). La ejecución por consola no se presenta como ejecución verificada dentro del IDE.',True)
add('Para completar la evidencia: abrir pom.xml como proyecto Maven; seleccionar JDK 17+; iniciar los contenedores; ejecutar la configuración compartida TC-BL-001 - Juice Shop y capturar el resultado con 1 prueba aprobada.',True)

nextpage();title(4,'Reporte Allure: resumen')
add('Reporte generado con Allure CLI 2.46.1 a partir de los resultados reales del adaptador allure-junit5 2.29.1. La captura corresponde a la ejecución final, sin resultados antiguos mezclados.')
shot('allure-overview.png',405)
table([['Métrica','Valor'],['Total / aprobadas','1 / 1'],['Fallidas / rotas / omitidas','0 / 0 / 0'],['Duración reportada por Allure',f"{allure['time']['duration']/1000:.3f} segundos"],['Interpretación','100% significa reproducción exitosa de la debilidad; no aprobación de seguridad.']],[180,319])
add('Reporte interactivo incluido en output/allure-report/index.html. Abrir con allure open output/allure-report o mediante un servidor HTTP local; no requiere credenciales.',True)

nextpage();title(5,'Reporte Allure: pasos y adjuntos')
shot('allure-case.png',405)
add('El caso conserva el control positivo, la petición manipulada, la respuesta y la lectura independiente del carrito. También registra la restauración a una unidad y el resumen JSON del resultado.')
table([['Adjunto','Propósito'],['Carrito antes de la manipulación','Acreditar cantidad inicial 1.'],['Petición de prueba / respuesta','Acreditar quantity=-1 y la aceptación por la API.'],['Lectura independiente del carrito','Confirmar que el valor fue persistido.'],['Resultado y veredicto de seguridad','Identificar escenario, tiempos, datos observados y limpieza.']],[220,279])
add('No se adjuntan cuerpos de registro o login a Allure. La etiqueta critical representa prioridad del caso de prueba y no una puntuación CVSS ni una severidad demostrada sobre un sistema de producción.',True)

nextpage();title(6,'Reporte ZAP: análisis pasivo')
shot('zap-report.png',295)
table([['Regla / ID','Riesgo ZAP','Instancias'],['Cross-Domain Misconfiguration / 10098','Medio','5'],['Authentication Request Identified / 10111','Informativo','2'],['Session Management Response Identified / 10112','Informativo','1']],[325,100,74])
add('Son <b>3 tipos de alertas y 8 instancias</b>, no ocho vulnerabilidades distintas. Cola pasiva al exportar: <b>0</b>. El reporte nativo se generó a las 00:50:23 UTC del 21/10, equivalentes a las 20:50:23 del 20/10 en Bolivia.')
add('<b>CORS:</b> ZAP observó Access-Control-Allow-Origin: * en las respuestas. Esto requiere revisar qué datos son públicos y cómo se autentican las peticiones; por sí solo no demuestra lectura de información autenticada desde otro origen.')
add('Las reglas 10111 y 10112 identifican mecanismos de autenticación y sesión: son informativas. La vulnerabilidad de cantidad negativa la comprueba el código Java; no se atribuye al escáner.')
add('Alcance: cinco endpoints del flujo, dentro del laboratorio local. No es una evaluación exhaustiva de Juice Shop. Los reportes exportados redactan JWT y contraseñas efímeras. Archivos: output/zap/zap-report.html y zap-alerts.json.',True)

nextpage();title(7,'Reproducción y recomendaciones')
sub('Entorno utilizado')
table([['Componente','Versión'],['Juice Shop / ZAP','20.3.0 / 2.17.0 (imágenes Docker oficiales)'],['Java / Maven Wrapper','JBR OpenJDK 25.0.4; compilación release 17 / Maven 3.9.11'],['JUnit / RestAssured / Allure adaptador','5.12.2 / 5.5.6 / 2.29.1'],['Allure CLI / sistema','2.46.1 / Windows + Docker Desktop']],[190,309])
sub('Comandos desde la raíz del proyecto')
code('$env:JAVA_HOME = "C:\\ruta\\al\\jdk"\n./scripts/run-lab.ps1\nallure generate target/allure-results --clean -o output/allure-report\nallure open output/allure-report\n\n# Regresión: exigir comportamiento seguro (fallará en la versión actual)\n./mvnw.cmd test -Dexpectation=secure\n\n# Detener el laboratorio\ndocker compose stop')
add('El script espera disponibilidad, reinicia solo la sesión ZAP del laboratorio y ejecuta el único caso. Requiere Python 3 para exportar ZAP y Allure CLI para generar el HTML. El proxy se escucha únicamente en 127.0.0.1:8090. Juice Shop se publica en 127.0.0.1:3000.')
sub('Corrección propuesta')
add('Validar en el servidor que quantity sea un entero entre 1 y un máximo comercial definido, tanto al crear como al actualizar ítems. Rechazar antes de escribir; preservar la cantidad anterior y devolver 400/422 con un mensaje controlado.')
add('Aplicar una restricción consistente en persistencia y volver a validar cantidad, disponibilidad y precio al confirmar la compra. Añadir una regresión que exija rechazo de -1. Revisar CORS según los orígenes y datos realmente necesarios.')
sub('Impacto y límites')
add('La integridad del carrito queda comprometida y puede propagarse a cálculos posteriores. La prioridad de corrección es alta, pero no se asigna un CVSS ni se afirma fraude consumado: el alcance no incluyó la compra. El modo secure existe como oráculo de regresión; no se presenta como una ejecución adicional realizada.',True)

nextpage();title(8,'Repositorio, entrega y trazabilidad')
add(f'<b>Destino del código:</b><br/><link href="{repo}" color="#007E87">{repo}</link>')
add('<b>Estado:</b> publicación y visibilidad pública no verificadas. La entrega local está preparada para publicación; el informe no contiene un enlace inventado ni afirma que el código ya esté accesible públicamente.')
table([['Requisito','Estado / evidencia'],['Un caso de flujo de negocio','Completado: TC-BL-001 con control positivo y limpieza.'],['Código reproducible','Completado: src/, pom.xml, Maven Wrapper, compose.yaml y scripts/.'],['Ejecución satisfactoria','Completada por consola: BUILD SUCCESS, 1 prueba aprobada.'],['Ejecución satisfactoria en IDE','Pendiente de captura y validación visual en IntelliJ.'],['Allure','Completado: HTML, adjuntos y capturas en este documento.'],['ZAP','Completado: reporte nativo HTML, JSON y resumen en este documento.'],['Repositorio público','Pendiente de publicación/verificación de acceso sin sesión.']],[180,319])
sub('Integridad de los archivos de evidencia')
for name in ['evidence/business-result.json','evidence/execution.log','output/zap/zap-alerts.json','src/test/java/security/NegativeQuantityTest.java']:
    digest=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    add(escape(name),True); code(digest[:32]+'\n'+digest[32:])
add('Los dos renglones de cada hash SHA-256 forman una sola cadena, sin espacios. Los digests de las imágenes Docker se conservan en evidence/image-digests.txt.',True)

nextpage();title(9,'Fuentes y material de referencia')
add('El PDF Automation-Vulnerability-v6.pdf se utilizó como material didáctico sobre pruebas de vulnerabilidad y ZAP. Las instrucciones efectivas de la entrega provienen de la solicitud del usuario y de su selección de Juice Shop; el contenido adjunto no se trató como autorización para otras acciones.')
add('El ZIP api_v6-main.zip aportó la referencia tecnológica Java/RestAssured. Su configuración apunta a todo.ly y contiene credenciales fijas; no se copiaron esas credenciales. Todo.ly y Todoist no son el mismo servicio. La solución creada usa Maven para facilitar la ejecución reproducible en este entorno.')
sources=[('Instalación oficial de OWASP Juice Shop','https://help.owasp-juice.shop/part1/running.html'),('API oficial de ZAP y escaneo pasivo','https://www.zaproxy.org/docs/api/'),('Alerta CORS 10098','https://www.zaproxy.org/docs/alerts/10098/'),('Allure y JUnit Jupiter','https://allurereport.org/docs/junit-jupiter/'),('Código oficial de Juice Shop','https://github.com/juice-shop/juice-shop')]
for name,url in sources:
    sub(name); add(f'<link href="{url}" color="#007E87">{url}</link>',True)
sub('Interpretación de la evidencia')
add('Los valores HTTP, cantidades, tiempos, alertas y capturas proceden de la ejecución del laboratorio. Las recomendaciones son propuestas de corrección. La demo pública, Todoist, el checkout y el impacto financiero no fueron probados; no se extrapolan a ellos los resultados.')
add('Para cerrar la entrega académica: verificar el repositorio sin iniciar sesión, publicar el código y reportes, y sustituir la condición pendiente del IDE por una captura real de la configuración ejecutada satisfactoriamente. Después regenerar este PDF con scripts/build_pdf.py.',True)

def footer(canvas,doc):
    w,h=A4; canvas.saveState(); canvas.setStrokeColor(TEAL);canvas.setLineWidth(2);canvas.line(48,h-32,w-48,h-32)
    canvas.setFont('Body',8);canvas.setFillColor(MUTED)
    canvas.drawString(48,26,'TC-BL-001 | Juice Shop local | 20/10/2026')
    canvas.drawRightString(w-48,26,f'{doc.page}')
    canvas.restoreState()

OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=46,
    title='TC-BL-001 - Prueba de vulnerabilidad del flujo de negocio en Juice Shop',author='Laboratorio de pruebas',subject='Caso, ejecución, Allure, ZAP y estado de publicación')
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(OUT)
