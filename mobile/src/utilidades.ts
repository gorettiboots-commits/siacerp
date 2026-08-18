import { TALLAS } from './componentes/MatrizTallas';

/** Convierte una talla en número para comparar (p. ej. "12.5" -> 12.5). */
function talla_a_numero(talla: string): number {
  return parseFloat(talla);
}

/**
 * Genera la corrida de tallas desde `desde` hasta `hasta` con avance de 0.5
 * (como en calzado). Regresa las tallas existentes en el catálogo dentro del
 * rango inclusive. Si `desde > hasta`, regresa lista vacía.
 */
export function generar_corrida(desde: string, hasta: string): string[] {
  const inicio = talla_a_numero(desde);
  const fin = talla_a_numero(hasta);
  if (!Number.isFinite(inicio) || !Number.isFinite(fin) || inicio > fin) {
    return [];
  }
  return TALLAS.filter((t) => {
    const valor = talla_a_numero(t);
    return valor >= inicio && valor <= fin;
  });
}

/** Formatea una talla sin decimales si es entera ("12" y no "12.0"). */
export function formatear_talla(talla: string): string {
  const valor = talla_a_numero(talla);
  return Number.isInteger(valor) ? String(valor) : talla;
}