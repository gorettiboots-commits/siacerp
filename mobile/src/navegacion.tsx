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

export type ClientesPedidosStackParamList = {
  ListaClientes: undefined;
  ListaPedidos: undefined;
  DetallePedido: { pedidoId: number; folio: string };
};

export type ProgramacionStackParamList = {
  ProgramacionLista: undefined;
};

// ─── Tabs principales ───────────────────────────────────────

export type TabParamList = {
  InventarioTab: NavigatorScreenParams<InventarioStackParamList>;
  OCTab: NavigatorScreenParams<OCStackParamList>;
  ProduccionTab: NavigatorScreenParams<ProduccionStackParamList>;
  EtiquetasTab: NavigatorScreenParams<EtiquetasStackParamList>;
  ClientesPedidosTab: NavigatorScreenParams<ClientesPedidosStackParamList>;
  ProgramacionTab: NavigatorScreenParams<ProgramacionStackParamList>;
  AdminTab: undefined;
  PerfilTab: undefined;
};

// ─── Root navigator ─────────────────────────────────────────

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<TabParamList>;
};
