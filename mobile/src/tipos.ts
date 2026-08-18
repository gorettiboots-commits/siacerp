export interface PartidaFleje {
  id: string;
  texto: string;
  cantidad: number;
}

export interface DatosEtiquetaPartida {
  modelo: string;
  corte: string;
  color: string;
  talla: string;
  cantidad: number;
}

export interface SolicitudImpresion {
  tipo: 'flejes' | 'partidas';
  partidas_fleje: PartidaFleje[];
  partidas: DatosEtiquetaPartida[];
  solicitado_en: string;
  origen: 'movil';
}