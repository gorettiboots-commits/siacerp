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
import type { ProduccionStackParamList } from '../navegacion';
import type { OrdenProduccionMovil } from '../tipos';
import { listarOPs, buscarOPs } from '../servicios/produccion';

type Nav = NativeStackNavigationProp<ProduccionStackParamList, 'ListaOPs'>;

const COLORES_ESTATUS: Record<string, string> = {
  planeada: '#3B82F6',
  en_proceso: '#F59E0B',
  terminada: colores.exito,
};

export function PantallaProduccion() {
  const navigation = useNavigation<Nav>();
  const [filtro, setFiltro] = useState('activas');
  const [termino, setTermino] = useState('');
  const [ops, setOps] = useState<OrdenProduccionMovil[]>([]);
  const [cargando, setCargando] = useState(true);

  const cargarOPs = async (estatus?: string) => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarOPs(termino)
      : await listarOPs(estatus || undefined);
    if (resultado.ok) {
      setOps(resultado.datos);
    }
    setCargando(false);
  };

  useEffect(() => {
    cargarOPs();
  }, []);

  const handleBuscar = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarOPs(termino)
      : await listarOPs(filtro === 'activas' ? undefined : filtro);
    if (resultado.ok) {
      setOps(resultado.datos);
    }
    setCargando(false);
  };

  const renderOP = ({ item }: { item: OrdenProduccionMovil }) => {
    const colorEstatus = COLORES_ESTATUS[item.estatus] || colores.textoSuave;
    const esUrgente = item.prioridad === 'urgente' || item.prioridad === 'alta';

    return (
      <Pressable
        style={[styles.card, esUrgente && styles.cardUrgente]}
        onPress={() => navigation.navigate('DetalleOP', { opId: item.id })}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardFolio}>{item.folio}</Text>
          <View style={[styles.badgeEstatus, { backgroundColor: colorEstatus }]}>
            <Text style={styles.textoBadge}>{item.estatus}</Text>
          </View>
        </View>
        <Text style={styles.cardModelo}>{item.modelo_nombre}</Text>
        <Text style={styles.cardVariante}>{item.codigo_variante}</Text>
        <View style={styles.cardFooter}>
          <View style={styles.cardPares}>
            <Text style={styles.cardParesValor}>{item.total_pares}</Text>
            <Text style={styles.cardParesLabel}>pares</Text>
          </View>
          <View style={styles.cardEntrega}>
            <Text style={styles.cardEntregaLabel}>Entrega</Text>
            <Text style={styles.cardEntregaFecha}>
              {item.fecha_entrega?.slice(0, 10) || '—'}
            </Text>
          </View>
          {esUrgente && (
            <View style={styles.badgeUrgente}>
              <Text style={styles.textoBadgeUrgente}>URGENTE</Text>
            </View>
          )}
        </View>
      </Pressable>
    );
  };

  return (
    <View style={styles.contenedor}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Producción</Text>
        <Text style={styles.subtitulo}>
          {ops.length} órdenes {filtro === 'activas' ? 'activas' : ''}
        </Text>
      </View>

      {/* Buscador */}
      <View style={styles.busqueda}>
        <TextInput
          style={styles.inputBusqueda}
          placeholder="Buscar por folio, modelo o variante..."
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
        {[
          { clave: 'activas', label: 'Activas' },
          { clave: 'planeada', label: 'Planeadas' },
          { clave: 'en_proceso', label: 'En Producción' },
        ].map(f => (
          <Pressable
            key={f.clave}
            style={[styles.filtro, filtro === f.clave && styles.filtroActivo]}
            onPress={() => {
              setFiltro(f.clave);
              cargarOPs(f.clave === 'activas' ? undefined : f.clave);
            }}
          >
            <Text style={[styles.textoFiltro, filtro === f.clave && styles.textoFiltroActivo]}>
              {f.label}
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
          data={ops}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderOP}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No hay órdenes de producción</Text>
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
  cardUrgente: { borderColor: colores.peligro, borderLeftWidth: 4 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  cardFolio: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  badgeEstatus: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  textoBadge: { fontSize: 10, color: '#ffffff', fontWeight: 'bold' },
  cardModelo: { fontSize: fuentes.cuerpo, color: colores.texto, fontWeight: '500', marginBottom: 2 },
  cardVariante: { fontSize: fuentes.pequena, color: colores.textoSuave, marginBottom: 8 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardPares: { alignItems: 'center' },
  cardParesValor: { fontSize: 18, fontWeight: 'bold', color: colores.texto },
  cardParesLabel: { fontSize: 10, color: colores.textoSuave },
  cardEntrega: { alignItems: 'center' },
  cardEntregaLabel: { fontSize: 10, color: colores.textoSuave },
  cardEntregaFecha: { fontSize: fuentes.cuerpo, color: colores.texto, fontWeight: '500' },
  badgeUrgente: {
    backgroundColor: colores.peligro,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  textoBadgeUrgente: { fontSize: 10, color: '#ffffff', fontWeight: 'bold' },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
