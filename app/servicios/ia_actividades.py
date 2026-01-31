import re
import random
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sqlalchemy.orm import Session

from app.modelos import ContenidoLectura, Actividad, Pregunta
from app.esquemas.actividad_ia import GenerarActividadesIARequest
from app.logs.logger import logger


MODEL_NAME = "lmqg/mt5-small-esquad-qag"

logger.info(f"Cargando modelo QAG en español: {MODEL_NAME}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)
model.eval()

logger.info("Modelo QAG cargado correctamente en CPU.")



MIN_LEN_PARA_IA = 120     # si el texto tiene menos de esto, mejor preguntas guiadas
MAX_TEXTO = 900           # recorte del texto para que no se pase de tokens
MAX_NEW_TOKENS = 256
NUM_BEAMS = 4



def _limpiar_texto(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip())


def _candidatos_distractores(texto: str):
    """
    Saca candidatos del texto para distractores (sin spaCy).
    """
    texto = _limpiar_texto(texto)
    caps = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b", texto)
    nums = re.findall(r"\b\d{1,4}\b", texto)
    words = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{6,}", texto)

    pool = caps + nums + words

    uniq = []
    seen = set()
    for x in pool:
        x = _limpiar_texto(x)
        if len(x) < 2:
            continue
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq[:40]


def _armar_opciones(correcta: str, otras_respuestas: list, texto: str):
    """
    3 opciones: correcta + 2 distractores.
    """
    correcta = _limpiar_texto(correcta)
    if not correcta:
        return None

    pool = [_limpiar_texto(x) for x in otras_respuestas if x and _limpiar_texto(x).lower() != correcta.lower()]

    if len(pool) < 2:
        pool += _candidatos_distractores(texto)

    # limpiar únicos
    pool2 = []
    seen = set([correcta.lower()])
    for x in pool:
        if not x:
            continue
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        pool2.append(x)

    if len(pool2) < 2:
        return None

    distractores = random.sample(pool2, 2)
    opciones = [correcta] + distractores
    random.shuffle(opciones)
    return opciones



def _preguntas_guiadas_para_ninos(texto: str) -> dict:
    """
    Se usa cuando el texto es muy corto o cuando el modelo devuelve poco.
    Evita preguntas raras y asegura claridad para 7–10 años.
    """
    return {
        "titulo": "Comprensión de Lectura",
        "descripcion": "Actividad educativa (modo niños 7–10)",
        "preguntas": [
            {
                "tipo": "texto_libre",
                "pregunta": "¿De qué trata el texto? (Cuenta la idea principal)",
                "opciones": [],
                "respuesta_correcta": "",
                "explicacion": "Escribe con tus palabras de qué se trata."
            },
            {
                "tipo": "multiple_choice",
                "pregunta": "¿Qué harías tú si fueras el personaje o estuvieras en esa situación?",
                "opciones": [
                    "Haría algo amable y ayudaría",
                    "Me quedaría sin hacer nada",
                    "Pediría ayuda a un adulto"
                ],
                "respuesta_correcta": "Haría algo amable y ayudaría",
                "explicacion": "Piensa en una buena acción y explica por qué."
            },
            {
                "tipo": "verdadero_falso",
                "pregunta": "Verdadero o falso: Puedo entender mejor si leo despacio y con atención.",
                "opciones": ["verdadero", "falso"],
                "respuesta_correcta": "verdadero",
                "explicacion": "Leer con calma ayuda a comprender."
            }
        ]
    }


def _pregunta_complemento_nino(idx: int) -> dict:
    """
    Preguntas de relleno (bonitas) si el modelo devolvió menos de 3 pares QA.
    """
    opciones = [
        {
            "tipo": "texto_libre",
            "pregunta": "¿Qué parte del texto te gustó más? ¿Por qué?",
            "opciones": [],
            "respuesta_correcta": "",
            "explicacion": "Elige una parte y explica tu razón."
        },
        {
            "tipo": "texto_libre",
            "pregunta": "Escribe una oración que resuma el texto.",
            "opciones": [],
            "respuesta_correcta": "",
            "explicacion": "Una sola oración clara."
        },
        {
            "tipo": "verdadero_falso",
            "pregunta": "Verdadero o falso: El texto tiene un mensaje o enseñanza.",
            "opciones": ["verdadero", "falso"],
            "respuesta_correcta": "verdadero",
            "explicacion": "Piensa en lo que aprendiste."
        },
    ]
    return opciones[idx % len(opciones)]



def extraer_pares_qa(raw: str):
    """
    Intenta parsear:
    question: ... , answer: ... | question: ... , answer: ...
    pero tolera:
    - coma opcional
    - '|' opcional
    - salto a 'question:' sin separador
    """
    raw = _limpiar_texto(raw)

    pattern = r"question:\s*(.*?)\s*(?:,)?\s*answer:\s*(.*?)(?=\s*\|\s*question:|\s*question:|$)"
    pares = re.findall(pattern, raw, flags=re.IGNORECASE)

    out = []
    vistos = set()

    for q, a in pares:
        q = _limpiar_texto(q).strip('"').strip("'")
        a = _limpiar_texto(a).strip('"').strip("'")

        if not q:
            continue
        if not q.endswith("?"):
            q += "?"

        key = q.lower()
        if key in vistos:
            continue
        vistos.add(key)

        out.append((q, a))

    return out



def generar_json_actividad_ia(texto: str, opciones: GenerarActividadesIARequest) -> dict:
    """
    Genera actividad en dict JSON (para tu BD) usando QAG en español.
    Optimizado para niños 7–10.
    """
    logger.info("🔥 ENTRÉ a generar_json_actividad_ia() (se va a generar con IA)")

    texto = _limpiar_texto(texto)
    if not texto:
        logger.warning("⚠️ Texto vacío. Usando preguntas guiadas.")
        return _preguntas_guiadas_para_ninos(texto)

    texto_resumido = texto[:MAX_TEXTO] if len(texto) > MAX_TEXTO else texto


    if len(texto_resumido) < MIN_LEN_PARA_IA:
        logger.warning(f"⚠️ Texto muy corto (len={len(texto_resumido)}). Usando modo guiado niños.")
        return _preguntas_guiadas_para_ninos(texto_resumido)

    dificultad = getattr(opciones, "dificultad", "media")
    logger.info(f"📤 Texto a IA len={len(texto_resumido)} dificultad={dificultad}")


    prompt = (
        "Genera preguntas claras y fáciles en español para niños de 7 a 10 años "
        "sobre este texto. No uses palabras difíciles.\n\n"
        f"TEXTO: {texto_resumido}"
    )

    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)

        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                num_beams=NUM_BEAMS,
                early_stopping=True
            )

        raw = tokenizer.decode(output[0], skip_special_tokens=True)
        logger.info(f"📥 RAW MODELO (inicio): {raw[:500]}")
        logger.info(f"📏 RAW MODELO len={len(raw)}")

        pares = extraer_pares_qa(raw)
        logger.info(f"PARES QA parseados: {len(pares)}")

        # Rescate por '?' si no parseó nada
        if len(pares) == 0:
            logger.warning("⚠️ No se extrajeron pares QA. Intentando rescate por '?'.")
            trozos = [t.strip() for t in raw.split("?") if len(t.strip()) > 10]
            qs = [(t + "?").strip() for t in trozos[:3]]

            if len(qs) >= 2:
                preguntas_rescate = []
                for q in qs[:3]:
                    preguntas_rescate.append({
                        "tipo": "texto_libre",
                        "pregunta": q,
                        "opciones": [],
                        "respuesta_correcta": "",
                        "explicacion": "Responde usando la lectura."
                    })
                # completar si faltan
                while len(preguntas_rescate) < 3:
                    preguntas_rescate.append(_pregunta_complemento_nino(len(preguntas_rescate)))

                return {
                    "titulo": "Comprensión de Lectura",
                    "descripcion": "Actividad educativa (IA español - rescate niños)",
                    "preguntas": preguntas_rescate
                }

            logger.warning("Rescate falló. Usando modo guiado niños.")
            return _preguntas_guiadas_para_ninos(texto_resumido)

        # Tomar máximo 3 pares
        pares = pares[:3]
        respuestas = [a for (_, a) in pares if a]

        preguntas = []

        # Multiple choice (si la respuesta es corta)
        q1, a1 = pares[0]
        opciones_mc = None
        if a1 and len(a1.split()) <= 5:
            opciones_mc = _armar_opciones(a1, respuestas[1:], texto_resumido)

        if opciones_mc:
            preguntas.append({
                "tipo": "multiple_choice",
                "pregunta": q1,
                "opciones": opciones_mc,
                "respuesta_correcta": a1,
                "explicacion": "Elige la respuesta correcta según el texto."
            })
        else:
            preguntas.append({
                "tipo": "texto_libre",
                "pregunta": q1,
                "opciones": [],
                "respuesta_correcta": "",
                "explicacion": "Responde con tus propias palabras."
            })

        # Verdadero/Falso (suave para niños)
        if len(pares) >= 2:
            _, a2 = pares[1]
            frase = a2 if a2 else "algo del texto"
            preguntas.append({
                "tipo": "verdadero_falso",
                "pregunta": f"Verdadero o falso: “{frase}” aparece en el texto.",
                "opciones": ["verdadero", "falso"],
                "respuesta_correcta": "verdadero",
                "explicacion": "Busca en el texto dónde se menciona."
            })
        else:
            preguntas.append(_pregunta_complemento_nino(1))

        # Texto libre (tercera pregunta si existe)
        if len(pares) >= 3:
            q3, _ = pares[2]
            preguntas.append({
                "tipo": "texto_libre",
                "pregunta": q3,
                "opciones": [],
                "respuesta_correcta": "",
                "explicacion": "Responde con tus propias palabras."
            })
        else:
            preguntas.append(_pregunta_complemento_nino(2))

 
        while len(preguntas) < 3:
            preguntas.append(_pregunta_complemento_nino(len(preguntas)))

        final_json = {
            "titulo": "Comprensión de Lectura",
            "descripcion": "Actividad educativa (IA en español, niños 7–10)",
            "preguntas": preguntas
        }

        logger.info(f"✅ JSON armado con {len(preguntas)} preguntas (niños)")
        return final_json

    except Exception as e:
        logger.error(f"❌ Error generando con IA ES: {e}")
        logger.warning("🔄 Usando modo guiado niños por error inesperado")
        return _preguntas_guiadas_para_ninos(texto_resumido)



def crear_preguntas_por_defecto(texto: str) -> list:
    return [
        {
            "tipo": "texto_libre",
            "pregunta": "¿De qué trata principalmente el texto?",
            "opciones": [],
            "respuesta_correcta": "",
            "explicacion": "Describe la idea principal con tus propias palabras."
        },
        {
            "tipo": "multiple_choice",
            "pregunta": "¿Qué aprendiste de la lectura?",
            "opciones": [
                "Información nueva e interesante",
                "Una historia entretenida",
                "Datos importantes"
            ],
            "respuesta_correcta": "Información nueva e interesante",
            "explicacion": "La lectura nos enseña cosas nuevas."
        },
        {
            "tipo": "verdadero_falso",
            "pregunta": "La lectura fue interesante y educativa.",
            "opciones": ["verdadero", "falso"],
            "respuesta_correcta": "verdadero",
            "explicacion": "Las lecturas nos ayudan a aprender."
        }
    ]


def crear_estructura_por_defecto(texto: str) -> dict:
    return {
        "titulo": "Actividad de Comprensión Lectora",
        "descripcion": "Actividad generada automáticamente",
        "preguntas": crear_preguntas_por_defecto(texto)
    }



def generar_actividad_ia_para_contenido(
    db: Session,
    contenido: ContenidoLectura,
    opciones: GenerarActividadesIARequest
):
    logger.info(f"🚀 Generando actividades IA para contenido_id={contenido.id}")

    texto = contenido.contenido or ""

    try:
        json_data = generar_json_actividad_ia(texto, opciones)
    except Exception as e:
        logger.error(f"❌ Error crítico generando JSON: {e}")
        logger.warning("🔄 Usando modo guiado niños por error crítico")
        json_data = _preguntas_guiadas_para_ninos(texto)

    preguntas = json_data.get("preguntas") or []
    if not isinstance(preguntas, list) or len(preguntas) == 0:
        logger.warning("⚠️ JSON sin preguntas válidas. Usando modo guiado niños.")
        json_data = _preguntas_guiadas_para_ninos(texto)
        preguntas = json_data["preguntas"]

    actividad = Actividad(
        contenido_id=contenido.id,
        tipo="preguntas",
        titulo=json_data.get("titulo", "Actividad IA"),
        descripcion=json_data.get("descripcion", "Actividad generada por IA"),
        configuracion={"generado_por_ia": True, "modelo": MODEL_NAME, "modo": "ninos_7_10"},
        puntos_maximos=len(preguntas) * 10,
        tiempo_estimado=len(preguntas) * 2,
        dificultad=getattr(opciones, "dificultad", "media"),
        activo=True
    )

    db.add(actividad)
    db.flush()

    orden = 1
    for p in preguntas:
        pregunta = Pregunta(
            actividad_id=actividad.id,
            texto_pregunta=p.get("pregunta", "Pregunta sin texto"),
            tipo_respuesta=p.get("tipo", "texto_libre"),
            opciones=p.get("opciones"),
            respuesta_correcta=p.get("respuesta_correcta"),
            puntuacion=10,
            explicacion=p.get("explicacion", "Sin explicación disponible"),
            orden=orden
        )
        db.add(pregunta)
        orden += 1

    db.commit()
    db.refresh(actividad)

    logger.info(f"Actividad IA creada exitosamente con {len(actividad.preguntas)} preguntas.")
    return actividad
