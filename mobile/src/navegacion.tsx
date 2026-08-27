import type { NavigatorScreenParams } from '@react-navigation/native';

// ─── Tipos de parámetros por pantalla ───────────────────────

export type AuthStackParamList = {
  Login: undefined;
};

export type InventarioStackParamList = {
  ListaInsumos: undefined;
  DetalleInsumo: { insumoId: number };
};

export type OCStackParamList = {
  ListaOCs: undefined;
  DetalleOC: { ordenId: number };
};

export type ProduccionStackParamList = {
  ListaOPs: undefined;
  DetalleOP: { opId: number };
  AvanceEstacion: { seguimientoId: number; opId: number };
};

export type EtiquetasStackParamList = {
  Inicio: undefined;
  Flejes: undefined;
  Partidas: undefined;
  Preview: undefined;
};

// ─── Tabs principales ───────────────────────────────────────

export type TabParamList = {
  InventarioTab: NavigatorScreenParams<InventarioStackParamList>;
  OCTab: NavigatorScreenParams<OCStackParamList>;
  ProduccionTab: NavigatorScreenParams<ProduccionStackParamList>;
  EtiquetasTab: NavigatorScreenParams<EtiquetasStackParamList>;
};

// ─── Root navigator ─────────────────────────────────────────

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<TabParamList>;
};
