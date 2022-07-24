import {EditorView, keymap, highlightSpecialChars, drawSelection, highlightActiveLine, highlightActiveLineGutter, dropCursor, rectangularSelection, crosshairCursor, lineNumbers} from "@codemirror/view"
import {EditorState} from "@codemirror/state"
import {defaultHighlightStyle, syntaxHighlighting, indentOnInput, bracketMatching, foldGutter, foldKeymap} from "@codemirror/language"
import {defaultKeymap, history, historyKeymap} from "@codemirror/commands"
import {searchKeymap, highlightSelectionMatches} from "@codemirror/search"
import {closeBrackets, closeBracketsKeymap} from "@codemirror/autocomplete"
import {lintKeymap} from "@codemirror/lint"
import {json} from "@codemirror/lang-json"
import {essKeymap} from "./ess_keymap"

export function create(doc) {
  return new EditorView({
    state: EditorState.create({
      doc: doc,
      lineWrapping: true,
      extensions: [
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightSpecialChars(),
        history(),
        foldGutter(),
        drawSelection(),
        dropCursor(),
        EditorState.allowMultipleSelections.of(true),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle, {fallback: true}),
        bracketMatching(),
        closeBrackets(),
        rectangularSelection(),
        crosshairCursor(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        keymap.of([
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
          ...foldKeymap,
          ...lintKeymap,
          ...essKeymap
        ]),
        json()
      ]
    }),
    parent: document.body
  });
}