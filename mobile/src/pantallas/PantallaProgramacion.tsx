import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
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
} from '../servicios/programacion';

const COLORES_ESTATUS: Record<string, string> = {
  programado: colores.exito,
  programacion_incompleta: '#F59E0B',
  en_proceso: '#3B82F6',
  producido: '#8B5CF6',
};

export function PantallaProgramacion() {
  const [semanas, setSemanas] = useState<ProgramacionSemanaMovil[]>([]);
  const [semanaSeleccionada, setSemanaSeleccionada] = useState<number | null>(null);
  const [lineas, setLineas] = useState<ProgramacionLineaMovil[]>([]);
  const [totales, setTotales] = useState({ lineas: 0, pares: 0, clientes: 0 });
  const [cargando, setCargando] = useState(true);
  const [cargandoLineas, setCargandoLineas] = useState(false);

  useEffect(() => {
    cargarSemanas();
  }, []);

  const cargarSemanas = async () => {
    setCargando(true);
    const resultado = await listarSemanas();
    if (resultado.ok) {
      setSemanas(resultado.datos);
      // Seleccionar la primera semana por defecto
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
    if (resLineas.ok) {
      setLineas(resLineas.datos);
    }
    if (resTotales.ok) {
      setTotales(resTotales.datos);
    }
    setCargandoLineas(false);
  };

  const onSemanaPress = async (semanaId: number) => {
    const nuevaSeleccion = semanaSeleccionada === semanaId ? null : semanaId;
    setSemanaSeleccionada(nuevaSeleccion);
    await cargarLineas(nuevaSeleccion);
  };

  const fmt_talla = (talla: string | number) => {
    const v = parseFloat(String(talla));
    return Number.isInteger(v) ? String(v) : String(v);
  };

  const renderLinea = ({ item }: { item: ProgramacionLineaMovil }) => {
    const colorEstatus = COLORES_ESTATUS[item.estatus] || colores.textoSuave;
    const tallas = item.tallas || [];
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.cardHeaderLeft}>
            <Text style={styles.cardFolio}>{item.folio_prog || '—'}</Text>
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
          {item.modelo || ''} {item.piel ? `/ ${item.piel}` : ''} {item.color ? `/ ${item.color}` : ''}
        </Text>

        {/* Tallas como chips */}
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
          {item.fecha_prog && (
            <Text style={styles.cardFecha}>{item.fecha_prog}</Text>
          )}
        </View>
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
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Programación Semanal</Text>
        <Text style={styles.subtitulo}>
          {totales.lineas} líneas · {totales.pares} pares · {totales.clientes} clientes
        </Text>
      </View>

      {/* Selector de semana */}
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

      {/* Líneas de programación */}
      {cargandoLineas ? (
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      ) : (
        <FlatList
          data={lineas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderLinea}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>
                {semanaSeleccionada
                  ? 'No hay líneas esta semana'
                  : 'Selecciona una semana'}
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
  lista: { paddingHorizontal: 16, paddingBottom: 16 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
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
  cardFecha: { fontSize: fuentes.pequena, color: colores.textoSuave },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
