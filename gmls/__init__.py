# coding=utf8

"""GitHub Markdown Local Server.

Usage:
  gmls [-p PORT|-h|-v]

Options:
  -p PORT           server port [default: 5000]
  -h --help         show this message
  -v --version      show version
"""

__version__ = '0.0.1'

import os
from docopt import docopt
from flask import abort
from flask import Flask
from flask import render_template
from flask import send_from_directory
from houdini import escape_html
from misaka import HtmlRenderer
from misaka import Markdown
from misaka import SmartyPants
from misaka import EXT_FENCED_CODE
from misaka import EXT_NO_INTRA_EMPHASIS
from misaka import EXT_AUTOLINK
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


cwd = os.getcwd()
dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__,
            static_folder=os.path.join(dir, 'static'),
            template_folder=os.path.join(dir, 'templates'))


class GmlsHtmlRenderer(HtmlRenderer, SmartyPants):

    def _code_no_lexer(self, text):
        text = text.encode('utf8')
        return '<pre><code>{}</code></pre>'.format(escape_html(text))

    def block_code(self, text, lang):
        if not lang:
            return self._code_no_lexer(text)

        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            return self._code_no_lexer(text)

        formatter = HtmlFormatter()

        return highlight(text, lexer, formatter)


render = GmlsHtmlRenderer()
markdown = Markdown(render, extensions=(
    EXT_FENCED_CODE |
    EXT_NO_INTRA_EMPHASIS |
    EXT_AUTOLINK))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def handler(path):
    if path.endswith('/'):
        path = os.path.join(path, 'README.md')

    if not path.endswith(('.md', '.markdown', '.mkd')):
        return send_from_directory(cwd, path)

    try:
        content = open(path).read().decode('utf8')
    except IOError:
        return abort(404)
    html = markdown.render(content)
    return render_template('layout.html', path=path, html=html)


if __name__ == '__main__':
    args = docopt(__doc__, version=__version__)

    if not args['-p'].isdigit():
        exit(__doc__)

    port = int(args['-p'])
    app.run(port=port, debug=True)
