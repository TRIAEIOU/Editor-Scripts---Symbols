# Editor Scripts & Symbols
Anki addon (https://ankiweb.net/shared/info/2065559429) to run custom scripts and insert symbols/strings in the Anki editor using keyboard shortcuts or popup menus (Anki forum https://forums.ankiweb.net/t/editor-js-snippets-support-thread/14958).

Configure symbols/strings, JavaScript or Python snippets to be inserted/executed in the editor from keyboard shortcuts (Qt format, see https://doc.qt.io/qt-5/qkeysequence.html).

<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/e/e0a25dd14a1fc50f0f868ff38698913a42a71b99.png" height="200">
<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/b/b1cd176578f2ea2549c111e525e7a39719c58c18.png" height="250">
<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/1/18a683d2c9fa656bce473a884611b2550e93bed4.png" height="300">

## General configuration
Addon configuration of scripts and symbols to run/insert is made in the addon configuration. To speed up and facilitate editing of configured scripts and symbols a CodeMirror 6 editor with JSON syntax highlighting is available from the context menu from the editor fields. Alternatively you can use the built in Anki addon configuration editor available from the Tools → Addons → Configure addon menu. The ESS editor has the following key board shortcuts
- https://codemirror.net/6/docs/ref/#commands.defaultKeymap
- https://codemirror.net/6/docs/ref/#search.searchKeymap
- https://codemirror.net/6/docs/ref/#commands.historyKeymap
- https://codemirror.net/6/docs/ref/#language.foldKeymap
- https://codemirror.net/6/docs/ref/#lint.lintKeymap
- Ctrl+B is set to "jump to matching bracket"
- Ctrl+Enter is "save and close editor"
- Shift+Escape is "discard and close editor"
- &lt;unconfigured&gt; is "open configuration editor"

Addon general configuration is under ´Settings´.
- `Editor shortcut`: Keyboard shorcut to open the ESS editor from the Anki editor. (optional, default none)
- `Popup shortcut`: Keyboard shortcut to open root menu (corresponding to the 'Scripts & Symbols' node) at caret position when in an editor field. (optional)
- `Size mode`: Size mode for config editor, valid options are `last` (same size as last time), `parent` (same size as editor window) and `XXXXxYYYY` where XXXX is the width in pixels and YYYY is the height. (optional, default last)
- `CSS`: Custom CSS to be applied to the config editor, for instance `.cm-editor .cm-content {white-space: pre-wrap; word-break: break-word;}` to word wrap (see https://codemirror.net/6/examples/styling/ for styling). (optional, default none)
- `Last geometry`: Used by addon to store last geometry, do not edit.

## Editing scripts and symbols
Add scripts or symbols by adding JSON objects and lists in hierarchal "node tree" under "Scripts & Symbols" in the configuration. The current version of the configuration is backed up in the addon directory before saving new configuration (overwritten on next save). Each node is one of the following:

- Menu: Node is menu containing end nodes and/or submenus. Keys:
	- `1. Menu`: Menu name.
	- `2. Shortcut`: Keyboard shortcut to open menu at caret position. (optional)
	- `3. Items`: JSON list of children.
- Symbol: Node is symbol/string to insert. Keys:
    - `1. Symbol`: Symbol/string to insert
    - `2. Shortcut`: Keyboard shortcut to insert symbol/string. (optional)
    - `3. HTML`: Set to string "true" to interpret string as HTML: "HTML": "true" (optional, defaults to false).
- Script/JavaScript: Node is JavaScript to execute in editor. The script is executed through document.execCommand(), the note contents are in the shadow root (document.activeElement.shadowRoot). The clipboard contents are made available in the object "ess_clipboard": ess_clipboard = {html: [clipboard HTML content], text: [clipboard text content]}. Keys:
	- `1. Script`: Title/name of script.
	- `2. Shortcut`: Keyboard shortcut to execute script. (optional)
	- `3. Language`: Script language, must be "JS".
	- `4. Pre`: JavaScript command(s) to prepend to the file contents. (optional)
	- `5. File`: File to load script commands from in [addon]/user_files. (optional)
	- `6. Post`: JavaScript command(s) to append to the file contents. (optional)
- Script/Python: Node is Python to execute in editor. The script is executed through compile/exec statements. The Anki Editor object instance is available through the variable "editor", the QApplication clipboard is available through the variable "clipboard" and the main window object through the variable "mw". Keys:
    - `1. Script`: Title/name of script.
	- `2. Shortcut`: Keyboard shortcut to execute script. (optional)
    - `3. Language`: Script language, must be "PY".
    - `4. Pre`: Python command(s) to prepend to the file contents. (optional)
    - `5. File`: File to load script commands from in [addon]/user_files. (optional)
    - `6. Post`: Python command(s) to append to the file contents. (optional)

Sample configuration below.
<pre><code>{
	"Settings": {
		"Editor shortcut": "",
		"Popup shortcut": "Ctrl+Alt+j",
		"Size mode": "last",
		"CSS": ""
	},
	"Scripts & Symbols": [
		{
			"1. Menu": "Symbols",
			"2. Shortcut": "Shift+Alt+S",
			"3. Items": [
				{
					"1. Menu": "Arrows",
					"2. Shortcut": "Shift+Alt+A",
					"3. Items": [
						{
							"1. Symbol": "←",
							"2. Shortcut": "Alt+Left",
							"3. HTML": "false"
						},
						{
							"1. Symbol": "→",
							"2. Shortcut": "Alt+Right",
							"3. HTML": "false"
						}
					]
				},
				{
					"1. Symbol": "α",
					"2. Shortcut": "Alt+a",
					"3. HTML": "false"
				},
				{
					"1. Symbol": "β",
					"2. Shortcut": "Alt+b",
					"3. HTML": "false"
				}
			]
		},
		{
			"1. Script": "Lowercase",
			"2. Shortcut": "Shift+Alt+L",
			"3. Language": "JS",
			"4. Pre": "(function(){const sel = document.activeElement.shadowRoot.getSelection(); for (i = 0; i < sel.rangeCount; i++) { const rng = sel.getRangeAt(i); let input = new XMLSerializer().serializeToString(rng.extractContents()); input = input.toLowerCase(); rng.insertNode(rng.createContextualFragment(input)); sel.addRange(rng);}})();",
			"5. File": "",
			"6. Post": ""
		}
	]
}</code></pre>

## Misc
Feel free to share your script snippets in https://forums.ankiweb.net/t/useful-javascript-snippets-for-the-editor/14536

## CHANGELOG
- Reimplementation from "Editor JS snippets": new format of config file (see above) to allow arbitrary submenu structure (unfortunately breaks previous configs), added python script support, added clipboard content to JavaScript environment, change addon name to match use.
- 2022-02-04 Add option to not cache script files, i.e. reload them from disk each script execution.
- 2022-05-13 Qt5 → 6 bug fixes (QMenu and QKeySequence).
- 2022-05-18 Qt5 → 6 bug fixes (QMenu and QKeySequence).
- 2022-06-02 Code refactor, update config.json format, adding addon CodeMirror 6 config.json dialog and automatic reload to context menu, remove cache option (scripts now always reloaded on each invocation), add automatic backup of config on save.