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

import { colores, fuentes } from '../theme';
import type { ClienteMovil } from '../tipos';
import { listarClientes, buscarClientes } from '../servicios/clientes';

export function PantallaClientes() {
  const [termino, setTermino] = useState('');
  const [clientes, setClientes] = useState<ClienteMovil[]>([]);
  const [cargando, setCargando] = useState(true);
  const [clienteSeleccionado, setClienteSeleccionado] = useState<ClienteMovil | null>(null);

  const cargarClientes = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarClientes(termino)
      : await listarClientes();
    if (resultado.ok) {
      setClientes(resultado.datos);
    }
    setCargando(false);
  };

  useEffect(() => {
    cargarClientes();
  }, []);

  const handleBuscar = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarClientes(termino)
      : await listarClientes();
    if (resultado.ok) {
      setClientes(resultado.datos);
    }
    setCargando(false);
  };

  const renderCliente = ({ item }: { item: ClienteMovil }) => (
    <Pressable
      style={[
        styles.card,
        clienteSeleccionado?.id === item.id && styles.cardSeleccionado,
      ]}
      onPress={() =>
        setClienteSeleccionado(
          clienteSeleccionado?.id === item.id ? null : item,
        )
      }
    >
      <View style={styles.cardHeader}>
        <Text style={styles.cardNombre}>{item.nombre}</Text>
        {item.nombre_comercial && (
          <Text style={styles.cardComercial}>{item.nombre_comercial}</Text>
        )}
      </View>
      <View style={styles.cardBody}>
        {item.rfc && <Text style={styles.cardRfc}>RFC: {item.rfc}</Text>}
        {item.telefono && (
          <Text style={styles.cardTelefono}>Tel: {item.telefono}</Text>
        )}
      </View>
      {item.email && (
        <Text style={styles.cardEmail}>{item.email}</Text>
      )}
    </Pressable>
  );

  return (
    <View style={styles.contenedor}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Clientes</Text>
        <Text style={styles.subtitulo}>{clientes.length} clientes activos</Text>
      </View>

      {/* Buscador */}
      <View style={styles.busqueda}>
        <TextInput
          style={styles.inputBusqueda}
          placeholder="Buscar por nombre, RFC..."
          value={termino}
          onChangeText={setTermino}
          onSubmitEditing={handleBuscar}
          returnKeyType="search"
        />
        <Pressable style={styles.botonBuscar} onPress={handleBuscar}>
          <Text style={styles.textoBotonBuscar}>🔍</Text>
        </Pressable>
      </View>

      {/* Lista */}
      {cargando ? (
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      ) : (
        <FlatList
          data={clientes}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderCliente}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No se encontraron clientes</Text>
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
  lista: { paddingHorizontal: 16, paddingBottom: 16 },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardSeleccionado: {
    borderColor: colores.primario,
    borderWidth: 2,
  },
  cardHeader: { marginBottom: 4 },
  cardNombre: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardComercial: { fontSize: fuentes.etiqueta, color: colores.primario, marginTop: 2 },
  cardBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  cardRfc: { fontSize: fuentes.etiqueta, color: colores.textoSuave },
  cardTelefono: { fontSize: fuentes.etiqueta, color: colores.textoSuave },
  cardEmail: { fontSize: fuentes.pequena, color: colores.textoSuave, marginTop: 2 },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
