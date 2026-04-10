import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastmcp import FastMCP
from pydantic import BaseModel
from strands import Agent
from strands.models.openai import OpenAIModel
from openai import AsyncOpenAI
from config import create_model

model = create_model()

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


SLIDE_PARSER_PROMPT = """You are a slide parser. Parse the following text into structured slides.

Input format may be:
- "Slide 1: Title | Content..."
- "Slide 1\nTitle\nContent"
- "---" separators
- Or any other format describing multiple slides

Output a JSON array of slides, each with:
- "title": string (slide title)
- "content": string (slide body content, can include simple formatting like **bold**, line breaks)

Text to parse:
{input_text}

Respond ONLY with valid JSON array. No markdown code blocks, no explanation."""


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Presentation</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #1a1a2e; color: #eee; min-height: 100vh; }}
        .slide-container {{ width: 100vw; height: 100vh; display: flex;
                           align-items: center; justify-content: center; }}
        .slide {{ display: none; width: 80%; max-width: 900px; padding: 60px;
                  background: #16213e; border-radius: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }}
        .slide.active {{ display: block; }}
        .slide h1 {{ color: #e94560; margin-bottom: 30px; font-size: 2.5em; }}
        .slide p {{ font-size: 1.4em; line-height: 1.8; white-space: pre-wrap; }}
        .nav {{ position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
               display: flex; gap: 15px; }}
        .nav button {{ padding: 12px 24px; background: #e94560; border: none;
                      color: white; border-radius: 8px; cursor: pointer; font-size: 1em; }}
        .nav button:hover {{ background: #ff6b6b; }}
        .progress {{ position: fixed; top: 0; left: 0; height: 4px; background: #e94560; transition: width 0.3s; }}
        .slide-number {{ position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
                       color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="progress" id="progress"></div>
    <div class="slides">
        {slides_html}
    </div>
    <div class="slide-number" id="slideNumber"></div>
    <div class="nav">
        <button onclick="prevSlide()">← Previous</button>
        <button onclick="nextSlide()">Next →</button>
    </div>
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        
        function showSlide(n) {{
            slides.forEach((s, i) => s.classList.toggle('active', i === n));
            document.getElementById('progress').style.width = ((n + 1) / totalSlides * 100) + '%';
            document.getElementById('slideNumber').textContent = (n + 1) + ' / ' + totalSlides;
            currentSlide = n;
        }}
        
        function nextSlide() {{
            if (currentSlide < totalSlides - 1) showSlide(currentSlide + 1);
        }}
        
        function prevSlide() {{
            if (currentSlide > 0) showSlide(currentSlide - 1);
        }}
        
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        }});
        
        showSlide(0);
    </script>
</body>
</html>"""


async def parse_slides_with_llm(text: str, model) -> list[dict]:
    """Use LLM to parse slide text into structured data."""
    agent = Agent(model=model, system_prompt=SLIDE_PARSER_PROMPT)
    result = await agent.invoke_async(f"Parse this slide text:\n\n{text}")

    result_str = str(result).strip()

    if result_str.startswith("```json"):
        result_str = result_str[7:]
    if result_str.startswith("```"):
        result_str = result_str[3:]
    if result_str.endswith("```"):
        result_str = result_str[:-3]
    result_str = result_str.strip()

    return json.loads(result_str)


def generate_html(slides: list[dict]) -> str:
    """Generate single HTML presentation file."""
    slides_html = []
    for slide in slides:
        content = slide.get("content", "").replace("{", "{{").replace("}", "}}")
        title = slide.get("title", "").replace("{", "{{").replace("}", "}}")
        slides_html.append(f"""
        <div class="slide">
            <h1>{title}</h1>
            <p>{content}</p>
        </div>
        """)
    return HTML_TEMPLATE.format(slides_html="\n".join(slides_html))


mcp = FastMCP(name="html-generator-mcp")


@mcp.tool
async def generate_presentation(slide_text: str) -> str:
    """Generate HTML presentation from slide text.

    Input: Text block describing slides (e.g., "Slide 1: Title | Content...")
    Output: JSON with path and summary
    """
    model = create_model()
    slides = await parse_slides_with_llm(slide_text, model)
    html = generate_html(slides)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"presentation_{timestamp}_{unique_id}.html"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(html)

    print(f"\n{'=' * 60}")
    print(f"Generated HTML:")
    print(f"{'=' * 60}")
    print(html)
    print(f"{'=' * 60}\n")

    return json.dumps(
        {
            "path": str(output_path),
            "filename": filename,
            "slide_count": len(slides),
            "preview": f"Generated {len(slides)} slides. File: {filename}",
        }
    )


def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
