import anthropic
import os
from typing import Dict

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT = """Eres un experto en contenido viral para Instagram especializado en noticias de redes sociales, inteligencia artificial y creación de contenido.

Basándote en esta noticia, crea un script para un CARRUSEL DE 5 SLIDES en español.

NOTICIA:
Título: {title}
Resumen: {summary}
Fuente: {source}
Tema: {topic}

REGLAS POR SLIDE:
- SLIDE 1 (HOOK): Pregunta impactante o dato sorprendente. Máximo 8 palabras. Genera curiosidad inmediata.
- SLIDE 2 (QUÉ PASÓ): Contexto breve y claro. 25-35 palabras. Qué ocurrió y por qué es noticia.
- SLIDE 3 (EL DATO CLAVE): Número, estadística o hecho concreto que sorprenda. 20-30 palabras.
- SLIDE 4 (POR QUÉ TE IMPORTA): Impacto directo en el creador de contenido o marketer. 25-35 palabras.
- SLIDE 5 (CTA): Incluye "Sígueme" para más contenido así. 10-15 palabras. Usa emojis. Estilo de marca personal.

TONO: Informativo y directo, como noticia de última hora. No clickbait, pero sí dinámico.

Responde SOLO con el script, sin explicaciones. Formato exacto:

🎯 SLIDE 1 — HOOK
[texto]

📌 SLIDE 2 — CONTEXTO
[texto]

📊 SLIDE 3 — EL DATO
[texto]

💡 SLIDE 4 — POR QUÉ TE IMPORTA
[texto]

🔔 SLIDE 5 — CTA
[texto]"""


def generate_carousel_script(article: Dict) -> str:
    prompt = PROMPT.format(
        title=article["title"],
        summary=article.get("summary") or "Sin resumen disponible.",
        source=article["source"],
        topic=article.get("topic", "tendencias digitales"),
    )
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
