# coding=utf8

"""GitHub Markdown Local Server.

Usage:
  gmls [-p PORT|-f||-h|-v] [-i PATTERNS]

Options:
  -p PORT           server port [default: 5000]
  -i PATTERNS       ignore patterns for freezer
  -f --freeze       freeze site to static htmls
  -h --help         show this message
  -v --version      show version
"""

__version__ = '0.1.1'

import os
import mimetypes
import fnmatch
from binaryornot.check import is_binary
from docopt import docopt
from flask import abort
from flask import Flask
from flask import redirect
from flask import render_template
from flask import send_from_directory
from flask import url_for
from .flask_frozen import Freezer, walk_directory
from houdini import escape_html
from misaka import HtmlRenderer
from misaka import Markdown
from misaka import SmartyPants
from misaka import EXT_TABLES
from misaka import EXT_FENCED_CODE
from misaka import EXT_NO_INTRA_EMPHASIS
from misaka import EXT_AUTOLINK
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

DEFAULT_INDEX = "README.html"
cwd = os.getcwd()
dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=os.path.join(dir, 'static'),
            template_folder=os.path.join(dir, 'templates'))
app.config['FREEZER_DESTINATION'] = os.path.join(cwd, 'gmls.htmls')
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
freezer = Freezer(app)
ignores = ["gmls.htmls*", ".git*", "*.pyc", "*.sw[opn]"]


def try_md2html(name):
    suffixes = ['.md', '.mkd', '.markdown']
    main = name
    tail = ''
    if '#' in name:
        main = name[:name.find('#')]
        tail = name[name.find('#'):]
    for suffix in suffixes:
        if main.endswith(suffix):
            return main[:-len(suffix)] + '.html' + tail
    return name


def find_md_by_html(name):
    if name.endswith('.html'):
        fname = name[:-len('.html')]
        mdfile = fname + '.md'
        mkdfile = fname + '.mkd'
        markdownfile = fname + '.markdown'
        if os.path.exists(mdfile):
            return mdfile
        elif os.path.exists(mkdfile):
            return mkdfile
        elif os.path.exists(markdownfile):
            return markdownfile
    return name


def match_ignores(name):
    for pattern in ignores:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


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

    def autolink(self, link, is_email):
        if is_email:
            return u'<a href="mailto:{0}">{0}</a>'.format(link)
        if not link.startswith(('http', 'https', '//')):
            link = try_md2html(link)
        return u'<a href="{0}">{0}</a>'.format(link)

    def link(self, link, title, content):
        if not link.startswith(('http', 'https', '//')):
            link = try_md2html(link)
        if title:
            return u'<a href="{0}">{1}</a>'.format(link, content)
        return u'<a href="{0}" title="{2}">{1}</a>'.format(link, content, title)


render = GmlsHtmlRenderer()
markdown = Markdown(render, extensions=(
    EXT_TABLES |
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
        readme = None
        for entry in os.listdir(path):
            if not entry.startswith('.') and not match_ignores(entry):
                path_ = os.path.join(path, entry)
                if os.path.isdir(path_):
                    entry += '/'
                link = try_md2html(entry)
                if link == DEFAULT_INDEX:
                    readme = open(os.path.join(path, entry))\
                        .read().decode('utf8')
                li = u'* [{0}]({1})'.format(entry, link)
                lilist.append(li)
        content = '\n'.join(lilist)
        if readme:
            content = u'{0}\n\n-----\n\n{1}'.format(content, readme)
    else:
        # handle file
        if path.endswith('.html'):
            path = find_md_by_html(path)
        elif path.endswith(('.md', '.mkd', '.markdown')):
            path = try_md2html(path)
            return redirect(url_for('handle', path=path))
        else:
            # binary/plain text non-md files
            if not is_binary(path):
                mimetype = 'text/plain'
            else:
                mimetype = mimetypes.guess_type(path)[0]
            return send_from_directory(cwd, path, mimetype=mimetype)

        # not found
        if not os.path.isfile(path):
            return abort(404)
        # handle markdown files
        try:
            content = open(path).read().decode('utf8')
        except IOError:
            return abort(404)
    html = markdown.render(content)
    return render_template('layout.html', path=path, html=html,
                           os=os, cwd=cwd)


@freezer.register_generator
def handle_url_generator():
    for path in walk_directory(cwd):
        if not match_ignores(path):
            path = try_md2html(path)
            print path
            yield 'handle', {'path': path}


def main():
    args = docopt(__doc__, version=__version__)

    if args['-i']:
        for pattern in args['-i'].split(','):
            pattern = pattern.strip()
            if pattern:
                ignores.append(pattern)
    if args['--freeze']:
        freezer.freeze()
    else:
        if not args['-p'].isdigit():
            exit(__doc__)
        port = int(args['-p'])
        app.run(port=port, debug=True)


if __name__ == '__main__':
    main()
