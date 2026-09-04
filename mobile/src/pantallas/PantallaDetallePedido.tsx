import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colores, fuentes } from '../theme';
import { obtenerPedido, obtenerDetallePedido } from '../servicios/pedidos';
import type { PedidoClienteMovil, DetallePedidoMovil } from '../tipos';

interface Props {
  route: { params: { pedidoId: number; folio: string } };
  navigation: any;
}

const COLORES_ESTATUS: Record<string, string> = {
  pendiente: '#F59E0B',
  programado: '#3B82F6',
  surtido: colores.exito,
  cancelado: colores.peligro,
};

export function PantallaDetallePedido({ route }: Props) {
  const { pedidoId, folio } = route.params;
  const [pedido, setPedido] = useState<PedidoClienteMovil | null>(null);
  const [detalles, setDetalles] = useState<DetallePedidoMovil[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarDatos();
  }, [pedidoId]);

  const cargarDatos = async () => {
    setCargando(true);
    const resPedido = await obtenerPedido(pedidoId);
    if (resPedido.ok && resPedido.datos) {
      setPedido(resPedido.datos);
    }
    const resDetalle = await obtenerDetallePedido(pedidoId);
    if (resDetalle.ok) {
      setDetalles(resDetalle.datos);
    }
    setCargando(false);
  };

  const renderDetalle = ({ item }: { item: DetallePedidoMovil }) => {
    const totalPares = (item.puntos || []).reduce(
      (sum, p) => sum + (p.pares || 0),
      0,
    );
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardModelo}>{item.modelo}</Text>
          <Text style={styles.cardTotal}>{totalPares} pares</Text>
        </View>
        {(item.piel || item.color) && (
          <Text style={styles.cardDet}>
            {item.piel || ''} {item.color ? `/ ${item.color}` : ''}
          </Text>
        )}
        {(item.puntos && item.puntos.length > 0) && (
          <View style={styles.tallasRow}>
            {item.puntos.map((p, idx) => (
              <View key={idx} style={styles.tallaChip}>
                <Text style={styles.tallaLabel}>#{p.talla}</Text>
                <Text style={styles.tallaValor}>{p.pares}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  if (cargando) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      </SafeAreaView>
    );
  }

  const colorEstatus = pedido
    ? COLORES_ESTATUS[pedido.estatus] || colores.textoSuave
    : colores.textoSuave;

  return (
    <SafeAreaView style={styles.safe}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.headerFolio}>{folio}</Text>
        {pedido && (
          <>
            <Text style={styles.headerCliente}>{pedido.cliente_nombre}</Text>
            <View style={styles.headerRow}>
              <View style={[styles.badgeEstatus, { backgroundColor: colorEstatus }]}>
                <Text style={styles.textoBadge}>{pedido.estatus}</Text>
              </View>
              <Text style={styles.headerFecha}>
                {pedido.fecha_pedido?.slice(0, 10) || ''}
              </Text>
            </View>
            {pedido.folio_pedido && (
              <Text style={styles.headerInfo}>Pedido cliente: {pedido.folio_pedido}</Text>
            )}
            {(pedido.suela || pedido.horma) && (
              <Text style={styles.headerInfo}>
                Suela: {pedido.suela || '—'} · Horma: {pedido.horma || '—'}
              </Text>
            )}
            {pedido.observaciones && (
              <Text style={styles.headerObs}>{pedido.observaciones}</Text>
            )}
          </>
        )}
      </View>

      {/* Boton programar */}
      {pedido && pedido.estatus === 'pendiente' && (
        <View style={styles.programarContainer}>
          <Pressable
            style={styles.botonProgramar}
            onPress={() =>
              navigation.navigate('ProgramarPedido', {
                pedidoId: pedido.id,
                folio: pedido.folio,
              })
            }
          >
            <Ionicons name="calendar-outline" size={20} color="#ffffff" />
            <Text style={styles.textoProgramar}>Programar este pedido</Text>
          </Pressable>
        </View>
      )}

      {/* Detalle */}
      <View style={styles.seccion}>
        <Text style={styles.seccionTitulo}>
          Detalle ({detalles.length} lineas)
        </Text>
      </View>

      <FlatList
        data={detalles}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderDetalle}
        contentContainerStyle={styles.lista}
        ListEmptyComponent={
          <View style={styles.vacio}>
            <Text style={styles.textoVacio}>No hay detalles para este pedido</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  header: {
    padding: 16,
    backgroundColor: colores.primario,
  },
  headerFolio: { fontSize: fuentes.titulo, fontWeight: 'bold', color: '#ffffff' },
  headerCliente: { fontSize: fuentes.subtitulo, color: '#e0e7ff', marginTop: 4 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  badgeEstatus: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4 },
  textoBadge: { fontSize: 11, color: '#ffffff', fontWeight: 'bold' },
  headerFecha: { fontSize: fuentes.etiqueta, color: '#e0e7ff' },
  headerInfo: { fontSize: fuentes.pequena, color: '#c7d2fe', marginTop: 4 },
  headerObs: { fontSize: fuentes.pequena, color: '#c7d2fe', marginTop: 4, fontStyle: 'italic' },
  programarContainer: { paddingHorizontal: 16, paddingTop: 12 },
  botonProgramar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    borderRadius: 10,
  },
  textoProgramar: { fontSize: fuentes.subtitulo, color: '#ffffff', fontWeight: 'bold' },
  seccion: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 4 },
  seccionTitulo: { fontSize: fuentes.subtitulo, fontWeight: 'bold', color: colores.texto },
  lista: { paddingHorizontal: 16, paddingBottom: 16 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardModelo: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardTotal: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  cardDet: { fontSize: fuentes.etiqueta, color: colores.textoSuave, marginTop: 4 },
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
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
