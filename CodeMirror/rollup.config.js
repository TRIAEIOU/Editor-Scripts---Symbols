import {nodeResolve} from "@rollup/plugin-node-resolve"
import typescript from "@rollup/plugin-typescript"
export default {
  input: "./ess_editor.js",
  output: {
    file: "../ess_editor.bundle.js",
    format: "umd",
    name: "ess_editor"
  },
  plugins: [
    nodeResolve({dedupe: ["@codemirror/state"]}),
    typescript({compilerOptions: {
      lib: ["es5", "es6", "dom"],
      target: "es6"
    }})
  ]
}