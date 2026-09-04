import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colores, fuentes } from '../theme';
import type {
  ProgramacionSemanaMovil,
  ProgramacionLineaMovil,
} from '../tipos';
import {
  listarSemanas,
  lineasConTallas,
  totalesSemana,
  imprimirLinea,
} from '../servicios/programacion';

const COLORES_ESTATUS: Record<string, string> = {
  programado: colores.exito,
  programacion_incompleta: '#F59E0B',
  en_proceso: '#3B82F6',
  producido: '#8B5CF6',
};

const PRODUCCION_INICIADA = ['en_proceso', 'producido'];

export function PantallaProgramacion() {
  const [semanas, setSemanas] = useState<ProgramacionSemanaMovil[]>([]);
  const [semanaSeleccionada, setSemanaSeleccionada] = useState<number | null>(null);
  const [lineas, setLineas] = useState<ProgramacionLineaMovil[]>([]);
  const [totales, setTotales] = useState({ lineas: 0, pares: 0, clientes: 0 });
  const [cargando, setCargando] = useState(true);
  const [cargandoLineas, setCargandoLineas] = useState(false);
  const [refrescando, setRefrescando] = useState(false);
  const [imprimiendo, setImprimiendo] = useState<number | null>(null);

  useEffect(() => {
    cargarSemanas();
  }, []);

  const cargarSemanas = async () => {
    setCargando(true);
    const resultado = await listarSemanas();
    if (resultado.ok) {
      setSemanas(resultado.datos);
      if (resultado.datos.length > 0 && semanaSeleccionada === null) {
        setSemanaSeleccionada(resultado.datos[0].id);
        await cargarLineas(resultado.datos[0].id);
      }
    }
    setCargando(false);
  };

  const cargarLineas = async (semanaId: number | null) => {
    setCargandoLineas(true);
    const [resLineas, resTotales] = await Promise.all([
      lineasConTallas(semanaId),
      totalesSemana(semanaId),
    ]);
    if (resLineas.ok) setLineas(resLineas.datos);
    if (resTotales.ok) setTotales(resTotales.datos);
    setCargandoLineas(false);
  };

  const onRefresh = useCallback(async () => {
    setRefrescando(true);
    await cargarSemanas();
    if (semanaSeleccionada) {
      await cargarLineas(semanaSeleccionada);
    }
    setRefrescando(false);
  }, [semanaSeleccionada]);

  const onSemanaPress = async (semanaId: number) => {
    const nuevaSeleccion = semanaSeleccionada === semanaId ? null : semanaId;
    setSemanaSeleccionada(nuevaSeleccion);
    await cargarLineas(nuevaSeleccion);
  };

  const fmt_talla = (talla: string | number) => {
    const v = parseFloat(String(talla));
    return Number.isInteger(v) ? String(v) : String(v);
  };

  const puedeEliminar = (estatus: string): boolean => {
    return !PRODUCCION_INICIADA.includes(estatus);
  };

  const onImprimir = async (linea: ProgramacionLineaMovil) => {
    setImprimiendo(linea.id);
    try {
      const res = await imprimirLinea(linea);
      if (res.ok) {
        Alert.alert('Impresion', res.mensaje);
      } else {
        Alert.alert('Error', res.mensaje);
      }
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Error al enviar a imprimir');
    } finally {
      setImprimiendo(null);
    }
  };

  const renderLinea = ({ item }: { item: ProgramacionLineaMovil }) => {
    const colorEstatus = COLORES_ESTATUS[item.estatus] || colores.textoSuave;
    const tallas = item.tallas || [];
    const enProduccion = !puedeEliminar(item.estatus);

    return (
      <View style={[styles.card, enProduccion && styles.cardEnProduccion]}>
        <View style={styles.cardHeader}>
          <View style={styles.cardHeaderLeft}>
            <Text style={styles.cardFolio}>{item.folio_prog || '--'}</Text>
            {item.folio_pedido && (
              <Text style={styles.cardFolioPedido}>Pedido: {item.folio_pedido}</Text>
            )}
          </View>
          <View style={[styles.badgeEstatus, { backgroundColor: colorEstatus }]}>
            <Text style={styles.textoBadge}>{item.estatus}</Text>
          </View>
        </View>

        <Text style={styles.cardCliente}>{item.cliente || ''}</Text>
        <Text style={styles.cardModelo}>
          {item.modelo || ''} {item.piel ? '/ ' + item.piel : ''} {item.color ? '/ ' + item.color : ''}
        </Text>

        {tallas.length > 0 && (
          <View style={styles.tallasRow}>
            {tallas.map((t, idx) => (
              <View key={idx} style={styles.tallaChip}>
                <Text style={styles.tallaLabel}>#{fmt_talla(t.talla)}</Text>
                <Text style={styles.tallaValor}>{t.pares}</Text>
              </View>
            ))}
          </View>
        )}

        <View style={styles.cardFooter}>
          <View style={styles.cardPares}>
            <Ionicons name="shirt-outline" size={14} color={colores.textoSuave} />
            <Text style={styles.cardParesTexto}>{item.total_pares} pares</Text>
          </View>
          <View style={styles.cardAcciones}>
            {item.fecha_prog && (
              <Text style={styles.cardFecha}>{item.fecha_prog}</Text>
            )}
            <Pressable
              style={styles.botonImprimir}
              onPress={() => onImprimir(item)}
              disabled={imprimiendo === item.id}
            >
              {imprimiendo === item.id ? (
                <ActivityIndicator size="small" color="#ffffff" />
              ) : (
                <Ionicons name="print-outline" size={14} color="#ffffff" />
              )}
              <Text style={styles.textoImprimir}>Imprimir</Text>
            </Pressable>
          </View>
        </View>

        {enProduccion && (
          <View style={styles.proteccionRow}>
            <Ionicons name="lock-closed" size={12} color={colores.textoSuave} />
            <Text style={styles.proteccionTexto}>
              Produccion iniciada - no se puede eliminar
            </Text>
          </View>
        )}
      </View>
    );
  };

  if (cargando) {
    return (
      <View style={styles.cargando}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  return (
    <View style={styles.contenedor}>
      <View style={styles.header}>
        <Text style={styles.titulo}>Programacion Semanal</Text>
        <Text style={styles.subtitulo}>
          {totales.lineas} lineas - {totales.pares} pares - {totales.clientes} clientes
        </Text>
      </View>

      {semanas.length > 0 ? (
        <FlatList
          horizontal
          data={semanas}
          keyExtractor={(item) => item.id.toString()}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.semanasRow}
          renderItem={({ item: s }) => (
            <Pressable
              style={[
                styles.semanaChip,
                semanaSeleccionada === s.id && styles.semanaChipActivo,
              ]}
              onPress={() => onSemanaPress(s.id)}
            >
              <Text
                style={[
                  styles.semanaTexto,
                  semanaSeleccionada === s.id && styles.semanaTextoActivo,
                ]}
                numberOfLines={1}
              >
                {s.nombre}
              </Text>
            </Pressable>
          )}
        />
      ) : (
        <View style={styles.sinSemanas}>
          <Ionicons name="calendar-outline" size={20} color={colores.textoSuave} />
          <Text style={styles.sinSemanasTexto}>
            No hay semanas de programacion sincronizadas
          </Text>
          <Text style={styles.sinSemanasDetalle}>
            Crea una programacion en el escritorio para que aparezca aqui
          </Text>
        </View>
      )}

      {cargandoLineas ? (
        <View style={styles.cargandoLineas}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      ) : (
        <FlatList
          data={lineas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderLinea}
          contentContainerStyle={styles.lista}
          refreshControl={
            <RefreshControl refreshing={refrescando} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Ionicons
                name={semanaSeleccionada ? 'document-text-outline' : 'finger-print-outline'}
                size={40}
                color={colores.textoSuave}
              />
              <Text style={styles.textoVacio}>
                {semanaSeleccionada
                  ? 'No hay lineas esta semana'
                  : 'Selecciona una semana para ver las lineas'}
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  header: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 },
  titulo: { fontSize: fuentes.titulo, fontWeight: 'bold', color: colores.texto },
  subtitulo: { fontSize: fuentes.pequena, color: colores.textoSuave, marginTop: 2 },
  semanasRow: { paddingHorizontal: 16, paddingBottom: 10, gap: 8 },
  semanaChip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 16,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    marginRight: 8,
  },
  semanaChipActivo: { backgroundColor: colores.primario, borderColor: colores.primario },
  semanaTexto: { fontSize: fuentes.pequena, color: colores.textoSuave },
  semanaTextoActivo: { color: '#ffffff', fontWeight: 'bold' },
  sinSemanas: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    alignItems: 'center',
    backgroundColor: colores.tarjeta,
    marginHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  sinSemanasTexto: { fontSize: fuentes.etiqueta, color: colores.textoSuave, marginTop: 8, fontWeight: '500' },
  sinSemanasDetalle: { fontSize: fuentes.pequena, color: colores.textoSuave, marginTop: 4 },
  lista: { paddingHorizontal: 16, paddingBottom: 16 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardEnProduccion: {
    borderColor: '#F59E0B40',
    backgroundColor: '#FFFBEB',
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 },
  cardHeaderLeft: { flex: 1 },
  cardFolio: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  cardFolioPedido: { fontSize: fuentes.pequena, color: colores.textoSuave, marginTop: 2 },
  badgeEstatus: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  textoBadge: { fontSize: 10, color: '#ffffff', fontWeight: 'bold' },
  cardCliente: { fontSize: fuentes.cuerpo, color: colores.texto, fontWeight: '500', marginTop: 4 },
  cardModelo: { fontSize: fuentes.etiqueta, color: colores.textoSuave, marginTop: 2 },
  tallasRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  tallaChip: {
    backgroundColor: colores.fondo,
    borderRadius: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colores.borde,
  },
  tallaLabel: { fontSize: 10, color: colores.textoSuave },
  tallaValor: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  cardPares: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  cardParesTexto: { fontSize: fuentes.etiqueta, color: colores.textoSuave, fontWeight: '500' },
  cardAcciones: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardFecha: { fontSize: fuentes.pequena, color: colores.textoSuave },
  botonImprimir: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#6366F1',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 6,
  },
  textoImprimir: { fontSize: 10, color: '#ffffff', fontWeight: 'bold' },
  proteccionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  proteccionTexto: { fontSize: fuentes.pequena, color: '#F59E0B', fontWeight: '500' },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  cargandoLineas: { paddingVertical: 40, alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo, marginTop: 12, textAlign: 'center' },
});
