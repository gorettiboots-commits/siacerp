import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colores, fuentes } from '../theme';
import { obtenerDetalleOC } from '../servicios/ordenes_compra';
import type { DetalleOCMovil } from '../tipos';

interface Props {
  route: { params: { ordenId: number; folio: string } };
  navigation: { goBack: () => void };
}

export function PantallaDetalleOC({ route, navigation }: Props) {
  const { ordenId, folio } = route.params;
  const [detalles, setDetalles] = useState<DetalleOCMovil[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarDetalle();
  }, [ordenId]);

  const cargarDetalle = async () => {
    setCargando(true);
    const datos = await obtenerDetalleOC(ordenId);
    setDetalles(datos);
    setCargando(false);
  };

  const renderDetalle = ({ item }: { item: DetalleOCMovil }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.nombre}>{item.insumo_nombre}</Text>
        <Text style={styles.precio}>${item.precio_unitario.toFixed(2)}</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cantidad}>Cantidad: {item.cantidad}</Text>
        <Text style={styles.subtotal}>
          Subtotal: ${(item.cantidad * item.precio_unitario).toFixed(2)}
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.titulo}>{folio}</Text>
        <Text style={styles.subtitulo}>Detalle de orden de compra</Text>
      </View>

      {cargando ? (
        <ActivityIndicator size="large" color={colores.primario} style={styles.cargando} />
      ) : detalles.length === 0 ? (
        <Text style={styles.vacio}>No hay detalles para esta orden</Text>
      ) : (
        <FlatList
          data={detalles}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderDetalle}
          contentContainerStyle={styles.lista}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  header: {
    padding: 20,
    backgroundColor: colores.primario,
  },
  titulo: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  subtitulo: {
    fontSize: fuentes.subtitulo,
    color: '#e0e7ff',
    marginTop: 4,
  },
  cargando: { flex: 1, justifyContent: 'center' },
  vacio: {
    textAlign: 'center',
    color: colores.textoSuave,
    marginTop: 40,
    fontSize: fuentes.cuerpo,
  },
  lista: { padding: 16, gap: 12 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 16,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  nombre: {
    fontSize: fuentes.cuerpo,
    fontWeight: '600',
    color: colores.texto,
    flex: 1,
  },
  precio: {
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
    color: colores.primario,
  },
  cardBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  cantidad: {
    fontSize: fuentes.etiqueta,
    color: colores.textoSuave,
  },
  subtotal: {
    fontSize: fuentes.etiqueta,
    color: colores.textoSuave,
  },
});
