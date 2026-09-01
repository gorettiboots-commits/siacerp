import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { colores, fuentes } from '../theme';
import type { OCStackParamList } from '../navegacion';
import type { OrdenCompraMovil } from '../tipos';
import { listarOCs, buscarOCs } from '../servicios/ordenes_compra';

type Nav = NativeStackNavigationProp<OCStackParamList, 'ListaOCs'>;

const COLORES_ESTATUS: Record<string, string> = {
  pendiente: '#F59E0B',
  recibida: colores.exito,
  cancelada: colores.peligro,
  recibida_con_diferencias: '#F97316',
};

export function PantallaOrdenesCompra() {
  const navigation = useNavigation<Nav>();
  const [ordenamiento, setOrdenamiento] = useState('todas');
  const [termino, setTermino] = useState('');
  const [ordenes, setOrdenes] = useState<OrdenCompraMovil[]>([]);
  const [cargando, setCargando] = useState(true);

  const cargarOrdenes = async (filtro?: string) => {
    try {
      setCargando(true);
      const resultado = termino.trim()
        ? await buscarOCs(termino)
        : await listarOCs(filtro || undefined);
      if (resultado.ok) {
        setOrdenes(resultado.datos);
      }
      setCargando(false);
    } catch (e: any) {
      console.error('[OC] Error:', e.message);
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarOrdenes();
  }, []);

  const handleBuscar = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarOCs(termino)
      : await listarOCs(ordenamiento !== 'todas' ? ordenamiento : undefined);
    if (resultado.ok) {
      setOrdenes(resultado.datos);
    }
    setCargando(false);
  };

  const renderOrden = ({ item }: { item: OrdenCompraMovil }) => {
    const colorEstatus = COLORES_ESTATUS[item.estatus] || colores.textoSuave;
    return (
      <Pressable
        style={styles.card}
        onPress={() => navigation.navigate('DetalleOC', { ordenId: item.id })}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardFolio}>{item.folio}</Text>
          <View style={[styles.badgeEstatus, { backgroundColor: colorEstatus }]}>
            <Text style={styles.textoBadge}>{item.estatus}</Text>
          </View>
        </View>
        <Text style={styles.cardProveedor}>{item.proveedor_nombre}</Text>
        <View style={styles.cardFooter}>
          <Text style={styles.cardTotal}>${item.total.toLocaleString('es-MX', { minimumFractionDigits: 2 })}</Text>
          <Text style={styles.cardFecha}>{item.fecha_emision?.slice(0, 10) || ''}</Text>
        </View>
        {item.tipo === 'factura' && (
          <View style={styles.badgeFactura}>
            <Text style={styles.textoBadgeFactura}>FACTURA</Text>
          </View>
        )}
      </Pressable>
    );
  };

  return (
    <View style={styles.contenedor}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Órdenes de Compra</Text>
        <Text style={styles.subtitulo}>{ordenes.length} órdenes</Text>
      </View>

      {/* Buscador */}
      <View style={styles.busqueda}>
        <TextInput
          style={styles.inputBusqueda}
          placeholder="Buscar por folio o proveedor..."
          value={termino}
          onChangeText={setTermino}
          onSubmitEditing={handleBuscar}
          returnKeyType="search"
        />
        <Pressable style={styles.botonBuscar} onPress={handleBuscar}>
          <Text style={styles.textoBotonBuscar}>🔍</Text>
        </Pressable>
      </View>

      {/* Filtros */}
      <View style={styles.filtros}>
        {['todas', 'pendiente', 'recibida', 'cancelada'].map(filtro => (
          <Pressable
            key={filtro}
            style={[styles.filtro, ordenamiento === filtro && styles.filtroActivo]}
            onPress={() => {
              setOrdenamiento(filtro);
              cargarOrdenes(filtro === 'todas' ? undefined : filtro);
            }}
          >
            <Text style={[styles.textoFiltro, ordenamiento === filtro && styles.textoFiltroActivo]}>
              {filtro === 'todas' ? 'Todas' : filtro.charAt(0).toUpperCase() + filtro.slice(1)}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Lista */}
      {cargando ? (
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      ) : (
        <FlatList
          data={ordenes}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderOrden}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No se encontraron órdenes</Text>
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
  busqueda: { flexDirection: 'row', paddingHorizontal: 16, marginBottom: 8, gap: 8 },
  inputBusqueda: {
    flex: 1,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colores.tarjeta,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
  },
  botonBuscar: {
    backgroundColor: colores.primario,
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  textoBotonBuscar: { fontSize: 18 },
  filtros: { flexDirection: 'row', paddingHorizontal: 16, marginBottom: 8, gap: 8 },
  filtro: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  filtroActivo: { backgroundColor: colores.primario, borderColor: colores.primario },
  textoFiltro: { fontSize: fuentes.pequena, color: colores.textoSuave },
  textoFiltroActivo: { color: '#ffffff', fontWeight: 'bold' },
  lista: { paddingHorizontal: 16, paddingBottom: 16 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  cardFolio: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  badgeEstatus: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  textoBadge: { fontSize: 10, color: '#ffffff', fontWeight: 'bold' },
  cardProveedor: { fontSize: fuentes.cuerpo, color: colores.texto, marginBottom: 6 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTotal: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardFecha: { fontSize: fuentes.pequena, color: colores.textoSuave },
  badgeFactura: {
    position: 'absolute',
    top: 14,
    right: 14,
    backgroundColor: '#059669',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  textoBadgeFactura: { fontSize: 9, color: '#ffffff', fontWeight: 'bold' },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
