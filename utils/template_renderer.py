import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates', 'letters')

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html']),
)

def render_letter(template_name: str, **context) -> str:
    """
    Renders templates/letters/<template_name>.html 
    passing in all kwargs as context.
    Returns a full HTML string.
    """
    template = env.get_template(template_name)
    return template.render(**context)
