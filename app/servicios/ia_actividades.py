import json
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from sqlalchemy.orm import Session

from app.modelos import ContenidoLectura, Actividad, Pregunta
from app.esquemas.actividad_ia import GenerarActividadesIARequest
from app.logs.logger import logger

logger.info("Cargando modelo FLAN-T5-Base...")

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained(
    "google/flan-t5-base",
    torch_dtype=torch.float32
)

logger.info("Modelo cargado correctamente en CPU.")


# IA — Generación del JSON estructurado

def generar_json_actividad_ia(texto: str, opciones: GenerarActividadesIARequest) -> dict:
    """
    Genera una actividad en formato JSON usando FLAN-T5.
    """

    # Acortar el texto si es muy largo
    texto_resumido = texto[:500] if len(texto) > 500 else texto

    prompt = f"""
Genera preguntas educativas para niños basadas en este texto:

TEXTO: "{texto_resumido}"

Crea 3 preguntas en formato JSON válido:

{{
  "titulo": "Comprensión de Lectura",
  "descripcion": "Actividad educativa",
  "preguntas": [
    {{
      "tipo": "multiple_choice",
      "pregunta": "¿Cuál es la idea principal?",
      "opciones": ["A", "B", "C"],
      "respuesta_correcta": "A",
      "explicacion": "Breve explicación"
    }}
  ]
}}

Responde SOLO con el JSON, sin texto adicional.
"""

    logger.info(f"📤 Enviando prompt a la IA (longitud: {len(prompt)} chars)")

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)

    output = model.generate(
        **inputs,
        max_new_tokens=800,
        temperature=0.7,
        do_sample=True,
        top_p=0.9
    )

    result = tokenizer.decode(output[0], skip_special_tokens=True)
    
    logger.info(f"📥 Respuesta de la IA: {result[:200]}...")
    logger.info(f"📏 Longitud completa: {len(result)} chars")

    # Extraer JSON con múltiples estrategias
    try:
        # Estrategia 1: Buscar JSON entre llaves
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            logger.info(f"✅ JSON extraído: {json_str[:100]}...")
            final_json = json.loads(json_str)
        else:
            logger.warning("⚠️ No se encontró JSON con regex, intentando buscar manualmente...")
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
                final_json = json.loads(json_str)
            else:
                raise ValueError("No se encontró estructura JSON en la respuesta")

        # Validar estructura mínima
        if "preguntas" not in final_json:
            logger.warning("⚠️ JSON sin campo 'preguntas', añadiendo estructura por defecto")
            final_json["preguntas"] = []
        
        if not final_json.get("titulo"):
            final_json["titulo"] = "Actividad de Comprensión"
        
        if not final_json.get("descripcion"):
            final_json["descripcion"] = "Actividad generada por IA"
        
        # Si no hay preguntas o son muy pocas, añadir preguntas por defecto
        if len(final_json["preguntas"]) == 0:
            logger.warning("⚠️ No se generaron preguntas, usando preguntas por defecto")
            final_json["preguntas"] = crear_preguntas_por_defecto(texto_resumido)

        logger.info(f"✅ JSON válido con {len(final_json['preguntas'])} preguntas")
        return final_json

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error decodificando JSON: {e}")
        logger.error(f"❌ Texto recibido: {result}")
        logger.warning("🔄 Usando estructura por defecto debido a error de parseo")
        
        return crear_estructura_por_defecto(texto_resumido)
    
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando JSON: {e}")
        logger.error(f"❌ Texto recibido: {result}")
        logger.warning("🔄 Usando estructura por defecto debido a error inesperado")
        
        return crear_estructura_por_defecto(texto_resumido)


def crear_preguntas_por_defecto(texto: str) -> list:
    """Crea preguntas básicas por defecto"""
    return [
        {
            "tipo": "texto_libre",
            "pregunta": "¿De qué trata principalmente el texto?",
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
    """Crea una estructura completa por defecto cuando la IA falla"""
    return {
        "titulo": "Actividad de Comprensión Lectora",
        "descripcion": "Actividad generada automáticamente",
        "preguntas": crear_preguntas_por_defecto(texto)
    }


# ================================
# 🧩 Crear Actividad y Preguntas en BD
# ================================
def generar_actividad_ia_para_contenido(
    db: Session,
    contenido: ContenidoLectura,
    opciones: GenerarActividadesIARequest
):
    logger.info(f"🚀 Generando actividades IA para contenido_id={contenido.id}")

    texto = contenido.contenido
    
    try:
        json_data = generar_json_actividad_ia(texto, opciones)
    except Exception as e:
        logger.error(f"❌ Error crítico generando JSON: {e}")
        logger.warning("🔄 Usando estructura por defecto debido a error crítico")
        json_data = crear_estructura_por_defecto(texto)

    # Crear la actividad
    actividad = Actividad(
        contenido_id=contenido.id,
        tipo="preguntas",
        titulo=json_data.get("titulo", "Actividad IA"),
        descripcion=json_data.get("descripcion", "Actividad generada por IA"),
        configuracion={"generado_por_ia": True},
        puntos_maximos=len(json_data["preguntas"]) * 10,
        tiempo_estimado=len(json_data["preguntas"]) * 2,
        dificultad=opciones.dificultad,
        activo=True
    )

    db.add(actividad)
    db.flush()

    # Crear preguntas
    orden = 1
    for p in json_data["preguntas"]:
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

    logger.info(f"✅ Actividad IA creada exitosamente con {len(actividad.preguntas)} preguntas.")

    return actividad