# coding=utf8

"""GitHub Markdown Local Server.

Usage:
  gmls [-p PORT|-h|-v]

Options:
  -p PORT           server port [default: 5000]
  -h --help         show this message
  -v --version      show version
"""

__version__ = '0.0.3'

import os
import mimetypes
from binaryornot.check import is_binary
from docopt import docopt
from flask import abort
from flask import Flask
from flask import redirect
from flask import render_template
from flask import send_from_directory
from flask import url_for
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
app = Flask(__name__, static_folder=os.path.join(dir, 'static'),
            template_folder=os.path.join(dir, 'templates'))


class GmlsHtmlRenderer(HtmlRenderer, SmartyPants):
    def _code_no_lexer(self, text):
        text = text.encode('utf8')
        return '<pre><code>{}</code></pre>'.format(escape_html(text))

    def header(self, text, level):
        text = text.encode('utf8')
        return '''<h{0}><a id="{1}" class="anchor" href="#{1}">
               <span class="octicon octicon-link"></span></a>
               {1}</h{0}>'''.format(level, text)

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


@app.route('/', defaults={'path': './'})  # noqa
@app.route('/<path:path>')
def handle(path):
    if os.path.isdir(path):
        # 'directory' => 'directory/'
        if not path.endswith('/'):
            return redirect(url_for('handle', path=path + '/'))

        # collect entries in this directory
        lilist = []
        for entry in os.listdir(path):
            if not entry.startswith('.'):
                path_ = os.path.join(path, entry)
                if os.path.isdir(path_):
                    entry += '/'
                li = u'* [{0}]({0})'.format(entry)
                lilist.append(li)
        content = '\n'.join(lilist)
    else:
        # handle file
        if not path.endswith(('.md', '.markdown', '.mkd')):
            # not found
            if not os.path.isfile(path):
                return abort(404)

            # binary/plain text non-md files
            if not is_binary(path):
                mimetype = 'text/plain'
            else:
                mimetype = mimetypes.guess_type(path)[0]
            return send_from_directory(cwd, path, mimetype=mimetype)

        # handle markdown files
        try:
            content = open(path).read().decode('utf8')
        except IOError:
            return abort(404)
    html = markdown.render(content)
    return render_template('layout.html', path=path, html=html,
                           os=os, cwd=cwd)


def main():
    args = docopt(__doc__, version=__version__)

    if not args['-p'].isdigit():
        exit(__doc__)

    port = int(args['-p'])
    app.run(port=port, debug=True)


if __name__ == '__main__':
    main()
