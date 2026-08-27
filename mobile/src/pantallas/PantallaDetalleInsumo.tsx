import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';

import { colores, fuentes } from '../theme';
import type { InventarioStackParamList } from '../navegacion';
import type { InsumoMovil } from '../tipos';
import { obtenerInsumo } from '../servicios/inventario';

type Route = RouteProp<InventarioStackParamList, 'DetalleInsumo'>;

export function PantallaDetalleInsumo() {
  const navigation = useNavigation();
  const route = useRoute<Route>();
  const { insumoId } = route.params;

  const [insumo, setInsumo] = useState<InsumoMovil | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarInsumo();
  }, []);

  const cargarInsumo = async () => {
    const resultado = await obtenerInsumo(insumoId);
    if (resultado.ok && resultado.datos) {
      setInsumo(resultado.datos);
    }
    setCargando(false);
  };

  if (cargando) {
    return (
      <View style={styles.cargando}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  if (!insumo) {
    return (
      <View style={styles.vacio}>
        <Text style={styles.textoVacio}>Insumo no encontrado</Text>
        <Pressable style={styles.botonVolver} onPress={() => navigation.goBack()}>
          <Text style={styles.textoBotonVolver}>← Volver</Text>
        </Pressable>
      </View>
    );
  }

  const esBajo = insumo.stock_actual <= insumo.stock_minimo;

  return (
    <ScrollView style={styles.contenedor}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()}>
          <Text style={styles.volver}>← Volver</Text>
        </Pressable>
      </View>

      {/* Código y nombre */}
      <View style={styles.codigoSection}>
        <Text style={styles.codigo}>{insumo.codigo}</Text>
        <Text style={styles.nombre}>{insumo.nombre}</Text>
      </View>

      {/* Stock */}
      <View style={[styles.stockCard, esBajo && styles.stockCardBajo]}>
        <Text style={styles.stockLabel}>Stock Actual</Text>
        <Text style={[styles.stockValor, esBajo && styles.stockValorBajo]}>
          {insumo.stock_actual}
        </Text>
        <Text style={styles.stockUnidad}>{insumo.unidad_medida}</Text>
        {esBajo && (
          <Text style={styles.stockAlerta}>
            ⚠️ Por debajo del mínimo ({insumo.stock_minimo})
          </Text>
        )}
      </View>

      {/* Detalles */}
      <View style={styles.detalles}>
        <View style={styles.fila}>
          <Text style={styles.etiqueta}>Categoría</Text>
          <Text style={styles.valor}>{insumo.categoria}</Text>
        </View>
        <View style={styles.fila}>
          <Text style={styles.etiqueta}>Unidad de medida</Text>
          <Text style={styles.valor}>{insumo.unidad_medida}</Text>
        </View>
        <View style={styles.fila}>
          <Text style={styles.etiqueta}>Stock mínimo</Text>
          <Text style={styles.valor}>{insumo.stock_minimo}</Text>
        </View>
        <View style={styles.fila}>
          <Text style={styles.etiqueta}>Estado</Text>
          <Text style={[styles.valor, esBajo ? styles.estadoCritico : styles.estadoNormal]}>
            {esBajo ? 'Crítico' : 'Normal'}
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  header: { paddingHorizontal: 16, paddingTop: 12 },
  volver: { color: colores.primario, fontSize: fuentes.cuerpo },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
  botonVolver: { backgroundColor: colores.primario, borderRadius: 8, paddingVertical: 10, paddingHorizontal: 20 },
  textoBotonVolver: { color: '#ffffff', fontWeight: 'bold' },
  codigoSection: { paddingHorizontal: 16, paddingVertical: 12 },
  codigo: { fontSize: fuentes.titulo, fontWeight: 'bold', color: colores.primario },
  nombre: { fontSize: fuentes.cuerpo, color: colores.texto, marginTop: 4 },
  stockCard: {
    marginHorizontal: 16,
    backgroundColor: colores.tarjeta,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colores.exito,
    marginBottom: 16,
  },
  stockCardBajo: { borderColor: colores.peligro },
  stockLabel: { fontSize: fuentes.etiqueta, color: colores.textoSuave },
  stockValor: { fontSize: 36, fontWeight: 'bold', color: colores.exito, marginTop: 4 },
  stockValorBajo: { color: colores.peligro },
  stockUnidad: { fontSize: fuentes.cuerpo, color: colores.textoSuave, marginTop: 2 },
  stockAlerta: { fontSize: fuentes.pequena, color: colores.peligro, marginTop: 8, fontWeight: '600' },
  detalles: {
    marginHorizontal: 16,
    backgroundColor: colores.tarjeta,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  fila: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
  },
  etiqueta: { fontSize: fuentes.cuerpo, color: colores.textoSuave },
  valor: { fontSize: fuentes.cuerpo, color: colores.texto, fontWeight: '500' },
  estadoNormal: { color: colores.exito },
  estadoCritico: { color: colores.peligro },
});
