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
import type { ClientesPedidosStackParamList } from '../navegacion';
import type { PedidoClienteMovil } from '../tipos';
import { listarPedidos, buscarPedidos } from '../servicios/pedidos';

type Nav = NativeStackNavigationProp<ClientesPedidosStackParamList, 'ListaPedidos'>;

const COLORES_ESTATUS: Record<string, string> = {
  pendiente: '#F59E0B',
  programado: '#3B82F6',
  surtido: colores.exito,
  cancelado: colores.peligro,
};

export function PantallaPedidos() {
  const navigation = useNavigation<Nav>();
  const [filtro, setFiltro] = useState('todos');
  const [termino, setTermino] = useState('');
  const [pedidos, setPedidos] = useState<PedidoClienteMovil[]>([]);
  const [cargando, setCargando] = useState(true);

  const cargarPedidos = async (estatus?: string) => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarPedidos(termino)
      : await listarPedidos(estatus || undefined);
    if (resultado.ok) {
      setPedidos(resultado.datos);
    }
    setCargando(false);
  };

  useEffect(() => {
    cargarPedidos();
  }, []);

  const handleBuscar = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarPedidos(termino)
      : await listarPedidos(filtro === 'todos' ? undefined : filtro);
    if (resultado.ok) {
      setPedidos(resultado.datos);
    }
    setCargando(false);
  };

  const renderPedido = ({ item }: { item: PedidoClienteMovil }) => {
    const colorEstatus = COLORES_ESTATUS[item.estatus] || colores.textoSuave;
    return (
      <Pressable
        style={styles.card}
        onPress={() =>
          navigation.navigate('DetallePedido', {
            pedidoId: item.id,
            folio: item.folio,
          })
        }
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardFolio}>{item.folio}</Text>
          <View style={[styles.badgeEstatus, { backgroundColor: colorEstatus }]}>
            <Text style={styles.textoBadge}>{item.estatus}</Text>
          </View>
        </View>
        <Text style={styles.cardCliente}>{item.cliente_nombre}</Text>
        {item.folio_pedido && (
          <Text style={styles.cardFolioPedido}>Pedido: {item.folio_pedido}</Text>
        )}
        <View style={styles.cardFooter}>
          <View>
            <Text style={styles.cardPares}>{item.total_pares} pares</Text>
          </View>
          <Text style={styles.cardFecha}>
            {item.fecha_pedido?.slice(0, 10) || ''}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <View style={styles.contenedor}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Pedidos de Clientes</Text>
        <Text style={styles.subtitulo}>{pedidos.length} pedidos</Text>
      </View>

      {/* Buscador */}
      <View style={styles.busqueda}>
        <TextInput
          style={styles.inputBusqueda}
          placeholder="Buscar por folio o cliente..."
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
          { clave: 'todos', label: 'Todos' },
          { clave: 'pendiente', label: 'Pendientes' },
          { clave: 'programado', label: 'Programados' },
          { clave: 'surtido', label: 'Surtidos' },
        ].map((f) => (
          <Pressable
            key={f.clave}
            style={[styles.filtro, filtro === f.clave && styles.filtroActivo]}
            onPress={() => {
              setFiltro(f.clave);
              cargarPedidos(f.clave === 'todos' ? undefined : f.clave);
            }}
          >
            <Text
              style={[
                styles.textoFiltro,
                filtro === f.clave && styles.textoFiltroActivo,
              ]}
            >
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
          data={pedidos}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderPedido}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No se encontraron pedidos</Text>
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
  cardCliente: { fontSize: fuentes.cuerpo, color: colores.texto, fontWeight: '500', marginBottom: 2 },
  cardFolioPedido: { fontSize: fuentes.pequena, color: colores.textoSuave, marginBottom: 4 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardPares: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardFecha: { fontSize: fuentes.pequena, color: colores.textoSuave },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
