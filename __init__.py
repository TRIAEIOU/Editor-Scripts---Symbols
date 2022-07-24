import sys, os, codecs, importlib, json, base64, shutil, datetime
from typing import cast
from aqt import mw, gui_hooks
from aqt.utils import *
from aqt.qt import QMenu, QKeySequence, QApplication, QClipboard, QPoint

if qtmajor == 6:
    from . import dialog_qt6 as dialog
elif qtmajor == 5:
    from . import dialog_qt5 as dialog

MENU = "1. Menu"
SHORTCUT = "2. Shortcut"
ITEMS = "3. Items"
SYMBOL = "1. Symbol"
HTML = "3. HTML"
SCRIPT = "1. Script"
LANG = "3. Language"
JS = "js"
PY = "py"
PRE = "4. Pre"
FILE = "5. File"
POST = "6. Post"
NORMAL = {"Menu": "1. Menu", "1. Menu": "1. Menu", "Shortcut": "2. Shortcut", "2. Shortcut": "2. Shortcut", "Items": "3. Items", "3. Items": "3. Items", "Symbol": "1. Symbol", "1. Symbol": "1. Symbol", "HTML": "3. HTML", "3. HTML": "3. HTML", "Script": "1. Script", "1. Script": "1. Script", "Language": "3. Language", "3. Language": "3. Language", "Pre": "4. Pre", "4. Pre": "4. Pre", "File": "5. File", "5. File": "5. File", "Post": "6. Post", "6. Post": "6. Post"}

ADDON_TITLE = "Editor Scripts & Symbols"
SETTINGS = "Settings"
EDITOR_CSS = "CSS"
SIZE_MODE = "Size mode" # "parent", "last", WIDTHxHEIGHT (e.g "1280x1024")
LAST_GEOM = "Last geometry"
ENTRIES = "Scripts & Symbols"
EDITOR_SHORTCUT = "Editor shortcut"
POPUP_SHORTCUT = "Popup shortcut"


###########################################################################
# Editor code
###########################################################################
class ESS_dialog(QDialog):
    ###########################################################################
    # Constructor (populates and shows dialog)
    def __init__(self, _dict, parent, on_accept = None, on_reject = None):
        QDialog.__init__(self, parent)
        self.ui = dialog.Ui_dialog()
        self.ui.setupUi(self)
        self.setModal(False)
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.ui.btns.accepted.connect(self.accept)
        self.ui.btns.rejected.connect(self.reject)
        QShortcut(QKeySequence(Qt.Modifier.CTRL |  Qt.Key.Key_Return), self).activated.connect(self.accept)
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Key.Key_Escape), self).activated.connect(self.reject)
        self.setup_bridge(self.bridge_receiver)
        self.load_geom()
        content = re.sub(r'`', r'\`', json.dumps(_dict, indent=1, sort_keys=True))
        self.ui.web.setHtml(f'''
        <html>
        <head>
            <link rel=stylesheet href="styles.css">
            <script src="ess_editor.bundle.js"></script>
            <style>{config.get(SETTINGS, {}).get(EDITOR_CSS, '')}</style>
        </head>
        <body>
            <script>
                var ess_editor = ess_editor.create(`{content}`);
                ess_editor.focus();
            </script>
        </body>
        </html>
        ''', QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "")))
        self.show()


    ###########################################################################
    # Setup js → python message bridge (to shut Qt up b/c we don't use it)
    # Stolen from AnkiWebView
    def setup_bridge(self, handler):
        class Bridge(QObject):
            def __init__(self, handler: Callable[[str], Any]) -> None:
                super().__init__()
                self._handler = handler
            @pyqtSlot(str, result=str)  # type: ignore
            def cmd(self, str: str) -> Any:
                return json.dumps(self._handler(str))
        
        self._bridge = Bridge(handler)
        self._channel = QWebChannel(self.ui.web)
        self._channel.registerObject("py", self._bridge)
        self.ui.web.page().setWebChannel(self._channel)
        qwebchannel = ":/qtwebchannel/qwebchannel.js"
        jsfile = QFile(qwebchannel)
        if not jsfile.open(QIODevice.OpenModeFlag.ReadOnly):
            print(f"Error opening '{qwebchannel}': {jsfile.error()}", file=sys.stderr)
        jstext = bytes(cast(bytes, jsfile.readAll())).decode("utf-8")
        jsfile.close()
        script = QWebEngineScript()
        script.setSourceCode(
            jstext
            + """
            var pycmd, bridgeCommand;
            new QWebChannel(qt.webChannelTransport, function(channel) {
                bridgeCommand = pycmd = function (arg, cb) {
                    var resultCB = function (res) {
                        // pass result back to user-provided callback
                        if (cb) {
                            cb(JSON.parse(res));
                        }
                    }
                
                    channel.objects.py.cmd(arg, resultCB);
                    return false;                   
                }
                pycmd("domDone");
            });
        """)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setRunsOnSubFrames(False)
        self.ui.web.page().profile().scripts().insert(script)

    ###########################################################################
    # Bridge message receiver
    def bridge_receiver(self, str = None):
        pass

    ###########################################################################
    # Load dialog geometry
    def load_geom(self):
        settings = config.get(SETTINGS, {})
        mode =  settings.get(SIZE_MODE, '').lower()
        if match:= re.match(r'^(\d+)x(\d+)', mode):
            par_geom = self.parent.geometry()
            geom = QRect(par_geom)
            scr_geom = mw.app.primaryScreen().geometry()
            geom.setWidth(int(match.group(1)))
            geom.setHeight(int(match.group(2)))    
            if geom.width() > scr_geom.width():
                geom.setWidth(scr_geom.width())
            if geom.height() > scr_geom.height():
                geom.setHeight(scr_geom.height())
            geom.moveCenter(par_geom.center())
            if geom.x() < 0:
                geom.setX(0)
            if geom.y() < 0:
                geom.setY(0)
            self.setGeometry(geom)
        elif mode == 'last' and settings.get(LAST_GEOM, ''):
            self.restoreGeometry(base64.b64decode(settings[LAST_GEOM]))
        else:
            self.setGeometry(self.window().geometry())

    ###########################################################################
    # Save dialog geometry
    def save_geom(self):
        config.get(SETTINGS, {})[LAST_GEOM] = base64.b64encode(self.saveGeometry()).decode('utf-8')
        mw.addonManager.writeConfig(__name__, config)


    ###########################################################################
    # Main dialog accept
    def accept(self) -> None:
        if self.on_accept:
            def _validate(content):
                try:
                    _dict = json.loads(content)
                except json.JSONDecodeError as err: 
                    emsg = f'Error parsing JSON at line {err.lineno}, position {err.colno}: {err.msg}'
                except Exception as err:
                    emsg = f'Error parsing JSON: {type(err)} - {str(err)}.'
                else:
                    self.on_accept(self, _dict)
                    self.save_geom()
                    return super(__class__, self).accept()
                
                if askUser(f'{emsg}\nClose editor discarding changes?'):
                    self.reject();

            self.ui.web.page().runJavaScript('''(function () {
                return ess_editor.state.doc.toString();
            })();''', _validate)


    ###########################################################################
    # Main dialog reject
    def reject(self):
        if self.on_reject:
            self.ui.web.page().runJavaScript('''(function () {
                return ess_editor.state.doc.toString();
            })();''', lambda string: self.on_reject(self, string))

        self.save_geom()
        QDialog.reject(self) 


###########################################################################
# Actual scripts & symbols code
###########################################################################

###########################################################################
# Load script file to string
def load_file(fname) -> str:
    if not fname:
        return ''
    path = os.path.join(os.path.dirname(__file__), f"user_files/{fname}")
    with codecs.open(path, encoding='utf-8') as fh:
        file = fh.read().strip()
    return file


###########################################################################
# Build and show menu from node and down at current caret position
def show_submenu(nodes, editor):
    def pop_submenu(pos):
        menu = build_menu(nodes, QMenu(editor.web), editor)
        menu.popup(editor.web.mapToGlobal(QPoint(pos[0], pos[1])))

    editor.web.evalWithCallback("""(function () {
        document.activeElement.focus();
        sel = document.activeElement.shadowRoot.getSelection();
        rng = sel.getRangeAt(sel.rangeCount - 1).cloneRange();
        tmp_rng = document.createRange();
        tmp_rng.setStart(sel.anchorNode, sel.anchorOffset);
        tmp_rng.setEnd(sel.focusNode, sel.focusOffset);
        rng.collapse(tmp_rng.collapsed);
        rect = rng.getBoundingClientRect();
        return [rect.x + rect.width, rect.y + rect.height];
    })();""", pop_submenu)


###########################################################################
# Get clipboard contents and return "JS hash table" in string with contents
def clipboard() -> str:
    mime = QApplication.clipboard().mimeData(QClipboard.Mode.Clipboard)
    return {
        'html': mime.html(),
        'text': mime.text()
    }

###########################################################################
# Create command for node
def build_cmd(node) -> dict:
    if ITEMS in node:
        return lambda editor, node=node: show_submenu(node[ITEMS], editor)
    elif LANG in node:
        if node[LANG].lower() == JS:
            return lambda editor, node=node: editor.web.eval(rf"""(function () {{
                let ess_cliboard = {json.dumps(clipboard(), separators=(',', ':'))};
                {node.get(PRE, '')}
                {load_file(node.get(FILE, ''))}
                {node.get(POST, '')}
            }})();""")
        elif node[LANG].lower() == PY:
            return lambda editor, node=node, mw=mw: exec(compile(
                f"{node.get(PRE, '')}\n"
                + f"{load_file(node.get(FILE, ''))}\n"
                + f"{node.get(POST, '')}",
                node.get(FILE, '<string>'), 'exec'), {
                    'editor': editor,
                    'clipboard': QApplication.clipboard(),
                    'mw': mw
                })
        else:
            err = f'Unknown script type: {node[LANG]} - ignoring entry'
            showWarning(text=err, parent=mw, title=ADDON_TITLE, textFormat="rich")
            return None
    elif SYMBOL in node:
        return lambda editor, node=node: editor.web.eval(rf"""(function () {{
                document.execCommand(`{'insertHTML' if node[HTML] == 'true' else 'insertText'}`, false, `{node[SYMBOL]}`)}})();""")

    err = f"<p>Unknown configuration entry:</p><p>{node}</p><ul>"
    showWarning(text=err, parent=mw, title=ADDON_TITLE, textFormat="rich")
    return None


###########################################################################
# Recursively take config dict - parse and add shortcuts
def build_shortcuts(nodes, editor):
    scuts = []
    for node in nodes:
        if SHORTCUT in node:
            scuts.append((node[SHORTCUT], lambda cmd=build_cmd(node), editor=editor: cmd(editor)))
        if ITEMS in node:
            scuts += build_shortcuts(node[ITEMS], editor)
    return scuts


###########################################################################
# Recursively take config dict - parse - return QMenu
def build_menu(nodes, menu, editor) -> QMenu:
    for node in nodes:
        if ITEMS in node:
            menu.addMenu(build_menu(node[ITEMS], QMenu(editor.web), editor)).setText(node[MENU])
        elif label := node[SYMBOL] if node.get(SYMBOL, 0) else node.get(SCRIPT, 0):
            menu.addAction(label, node.get(SHORTCUT, 0), lambda editor=editor, cmd=build_cmd(node): cmd(editor))
    return menu


###########################################################################
# Take config and recursively parse and add shortcuts
def register_shortcuts(scuts, editor):
    if config.get(SETTINGS, {}).get(POPUP_SHORTCUT, 0):
        scuts.append((config[SETTINGS][POPUP_SHORTCUT], lambda editor=editor: show_submenu(config.get(ENTRIES), editor)))
    if config.get(SETTINGS, {}).get(EDITOR_SHORTCUT, 0):
        scuts.append((config[SETTINGS][EDITOR_SHORTCUT], lambda: ESS_dialog(config, editor.parentWindow, save)))
    scuts += build_shortcuts(config.get(ENTRIES, []), editor)
    return scuts


###########################################################################
# Context menu activation - build and append ESS menu items
def mouse_context(wedit, menu):
    menu.addSeparator()
    menu = build_menu(config.get(ENTRIES, []), menu, wedit.editor)
    action = QAction(f'ESS config', menu)
    action.setShortcut(config.get(SETTINGS, {}).get(EDITOR_SHORTCUT, 0))
    action.triggered.connect(lambda: ESS_dialog(config, wedit.editor.parentWindow, save))
    menu.addAction(action)
    menu.addSeparator()
    return menu

###########################################################################
# Save the result from config dialog and reload
def save(dlg, _dict):
    config = _dict
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'meta.json')):
        shutil.copy(os.path.join(os.path.dirname(__file__), 'meta.json'), os.path.join(os.path.dirname(__file__), 'meta.bak'))
    mw.addonManager.writeConfig(__name__, config)
    gui_hooks.editor_did_init_shortcuts.remove(register_shortcuts)
    gui_hooks.editor_will_show_context_menu.remove(mouse_context)
    importlib.reload(__import__(__name__))

###########################################################################
# Normalize config dict to new keys
def normalize(cfg):
    def _normalize(nd):
        if type(nd) == list:
            olist = []
            for el in nd:
                olist.append(_normalize(el))
            return olist
        elif type(nd) == dict:
            odict = {}
            for ikey, ival in nd.items():
                if NORMAL.get(ikey, 0) != 0:
                    odict[NORMAL[ikey]] = _normalize(ival)
            return odict
        else:
            return nd

    # Old format
    if (cfg.get('Items') or cfg.get('Menu') or cfg.get('Shortcut')) and os.path.exists(os.path.join(os.path.dirname(__file__), 'meta.json')):
        showWarning("<p><b>Updating configuration file format<b></p><p>A backup of the current configuration file will be saved in the addon folder for manual recovery in case of update error. The backup will be deleted on next addon update.</p>", parent=mw, title=ADDON_TITLE, textFormat="rich")
        shutil.copy(os.path.join(os.path.dirname(__file__), 'meta.json'), os.path.join(os.path.dirname(__file__), f'meta-{datetime.datetime.now().strftime("%y%m%d-%H%M%S.%f")}.json'))
        out = {
            SETTINGS: {
                SIZE_MODE: "last",
                LAST_GEOM: "",
                EDITOR_CSS: "",
                POPUP_SHORTCUT: cfg.get('Shortcut', ''),
                EDITOR_SHORTCUT: ""
            },
            ENTRIES: _normalize(cfg.get('Items', []))
        }
        return out

    cfg[ENTRIES] = _normalize(cfg.get(ENTRIES, []))
    return cfg


if not 2065559429 in sys.modules:
    config = normalize(mw.addonManager.getConfig(__name__))
    gui_hooks.editor_did_init_shortcuts.append(register_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(mouse_context)
