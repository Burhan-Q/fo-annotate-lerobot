import { fileURLToPath } from "url";
import { dirname, resolve } from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";

const __dirname = dirname(fileURLToPath(import.meta.url));

// bare import -> runtime global the FiftyOne App exposes (app/packages/plugins/src/externalize.ts)
const externals: Record<string, string> = {
  react: "React",
  "react-dom": "ReactDOM",
  recoil: "recoil",
  "@fiftyone/state": "__fos__",
  "@fiftyone/playback": "__fopb__",
  "@fiftyone/operators": "__foo__",
  "@fiftyone/spaces": "__fosp__",
  "@fiftyone/components": "__foc__",
  "@fiftyone/plugins": "__fop__",
  "@mui/material": "__mui__",
};

// Bundled deps (VOODO) reference process.env/global which don't exist in the browser;
// FiftyOne loads the plugin as a plain <script>. Without this shim the bundle throws
// "process is not defined" at load and never registers ("Unsupported view").
const SHIM_BANNER =
  "globalThis.global=globalThis.global||globalThis;" +
  "globalThis.process=globalThis.process||{env:{NODE_ENV:'production'}," +
  "nextTick:function(f){Promise.resolve().then(f)},platform:'',version:''," +
  "versions:{},argv:[]};";

export default defineConfig({
  plugins: [react(), cssInjectedByJsPlugin()],
  resolve: {
    alias: {
      // VOODO uses the automatic JSX runtime; the App only exposes classic React.
      "react/jsx-runtime": resolve(__dirname, "src/js/jsx-runtime-shim.ts"),
    },
  },
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    minify: true,
    lib: {
      entry: resolve(__dirname, "src/js/index.tsx"),
      name: "AnnotateLerobot",
      // IIFE (not UMD): a UMD build defers to the AMD branch and never calls
      // registerComponent ("Unsupported view"). Keep the index.umd.js filename.
      fileName: () => "index.umd.js",
      formats: ["iife"],
    },
    rollupOptions: {
      external: Object.keys(externals),
      output: { globals: externals, inlineDynamicImports: true, banner: SHIM_BANNER },
    },
  },
});
