// Translates automatic-JSX-runtime calls (used by VOODO) into classic React.createElement,
// since the FiftyOne App only exposes the classic React global.
import * as React from "react";

const R: any = React;
export const Fragment = R.Fragment;

function shim(type: any, props: any, key?: any) {
  const { children, ...rest } = props ?? {};
  if (key !== undefined) (rest as any).key = key;
  if (children === undefined) return R.createElement(type, rest);
  if (Array.isArray(children)) return R.createElement(type, rest, ...children);
  return R.createElement(type, rest, children);
}

export const jsx = R.jsx ?? shim;
export const jsxs = R.jsxs ?? shim;
export const jsxDEV = R.jsxDEV ?? shim;
