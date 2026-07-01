declare module "@fiftyone/plugins" {
  export enum PluginComponentType { Component = "Component", Panel = "Panel" }
  export interface PanelOptions { surfaces?: string; [k: string]: any }
  export interface RegisterComponentParams {
    name: string; label: string; component: any; type: PluginComponentType;
    panelOptions?: PanelOptions; activator?: (ctx?: any) => boolean;
  }
  export function registerComponent(p: RegisterComponentParams): void;
}
declare module "@fiftyone/spaces" {
  export function usePanelId(): string;
  export function usePanelStatePartial<T>(key: string, def?: T, local?: boolean): [T, (v: T) => void];
}
declare module "@fiftyone/playback" {
  export interface TimelineSubscription { id: string; loadRange: (r: [number, number]) => Promise<void>; renderFrame: (n: number) => void }
  export interface TimelineHookResult { subscribe: (s: TimelineSubscription) => void; isTimelineInitialized: boolean }
  export function useTimeline(name: string): TimelineHookResult;
  export function useDefaultTimelineNameImperative(): { getName: () => string };
  export function dispatchTimelineSetFrameNumberEvent(p: { timelineName: string; newFrameNumber: number }): void;
}
declare module "@fiftyone/operators" {
  export function useOperatorExecutor(uri: string): {
    execute: (params?: Record<string, any>, options?: { callback?: (raw: { result: any; error: any }) => void }) => void;
    isExecuting?: boolean;
  };
}
declare module "@fiftyone/state" {
  export const nullableModalSampleId: any;
}
declare module "recoil" {
  export function useRecoilValue<T>(atom: any): T;
}
declare module "@voxel51/voodo" {
  export const Text: any;
  export const Stack: any;
  export const Card: any;
  export enum TextVariant { Sm = "Sm", Md = "Md", Lg = "Lg" }
}
declare module "@voxel51/voodo/theme.css";
