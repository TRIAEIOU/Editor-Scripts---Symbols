import { KeyBinding } from '@codemirror/view';
import {
  cursorMatchingBracket,
} from '@codemirror/commands';
import {
  gotoLine,
} from '@codemirror/search';

export const essKeymap: ReadonlyArray<KeyBinding> = [
    { key: 'Mod-b', run: cursorMatchingBracket },
    { key: 'Mod-g', run: gotoLine }
];
