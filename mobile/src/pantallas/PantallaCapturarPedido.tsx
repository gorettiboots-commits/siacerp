import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colores, fuentes } from '../theme';
import {
  listarClientes,
  listarTallas,
  crearPedido,
} from '../servicios/pedidos';
import type { ClienteMovil } from '../tipos';
import type { TallaMovil } from '../servicios/pedidos';

interface Props {
  navigation: any;
}

interface LineaCaptura {
  modelo: string;
  piel: string;
  color: string;
  tallas: { talla_id: number; talla: string; pares: number }[];
}

export function PantallaCapturarPedido({ navigation }: Props) {
  const [clientes, setClientes] = useState<ClienteMovil[]>([]);
  const [tallas, setTallas] = useState<TallaMovil[]>([]);
  const [clienteSeleccionado, setClienteSeleccionado] = useState<ClienteMovil | null>(null);
  const [buscarCliente, setBuscarCliente] = useState('');
  const [mostrarClientes, setMostrarClientes] = useState(false);

  const [folioPedido, setFolioPedido] = useState('');
  const [suela, setSuela] = useState('');
  const [horma, setHorma] = useState('');
  const [observaciones, setObservaciones] = useState('');

  const [lineas, setLineas] = useState<LineaCaptura[]>([
    { modelo: '', piel: '', color: '', tallas: [] },
  ]);

  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setCargando(true);
    const [resClientes, resTallas] = await Promise.all([
      listarClientes(),
      listarTallas(),
    ]);
    if (resClientes.ok) setClientes(resClientes.datos);
    if (resTallas.ok) {
      // Inicializar tallas vacias para cada linea
      const tallasBase = resTallas.datos.map((t) => ({
        talla_id: t.id,
        talla: t.talla,
        pares: 0,
      }));
      setTallas(resTallas.datos);
      setLineas([{ modelo: '', piel: '', color: '', tallas: tallasBase }]);
    }
    setCargando(false);
  };

  // ── Clientes ──

  const clientesFiltrados = clientes.filter(
    (c) =>
      c.nombre.toLowerCase().includes(buscarCliente.toLowerCase()) ||
      (c.rfc || '').toLowerCase().includes(buscarCliente.toLowerCase()),
  );

  const seleccionarCliente = (c: ClienteMovil) => {
    setClienteSeleccionado(c);
    setBuscarCliente(c.nombre);
    setMostrarClientes(false);
  };

  // ── Lineas ──

  const actualizarLinea = (idx: number, campo: keyof LineaCaptura, valor: any) => {
    setLineas((prev) => {
      const copia = [...prev];
      (copia[idx] as any)[campo] = valor;
      return copia;
    });
  };

  const actualizarTallaEnLinea = (lineaIdx: number, tallaIdx: number, pares: number) => {
    setLineas((prev) => {
      const copia = [...prev];
      const tallas = [...copia[lineaIdx].tallas];
      tallas[tallaIdx] = { ...tallas[tallaIdx], pares };
      copia[lineaIdx] = { ...copia[lineaIdx], tallas };
      return copia;
    });
  };

  const agregarLinea = () => {
    const tallasBase = tallas.map((t) => ({
      talla_id: t.id,
      talla: t.talla,
      pares: 0,
    }));
    setLineas((prev) => [
      ...prev,
      { modelo: '', piel: '', color: '', tallas: tallasBase },
    ]);
  };

  const eliminarLinea = (idx: number) => {
    if (lineas.length <= 1) return;
    setLineas((prev) => prev.filter((_, i) => i !== idx));
  };

  const totalPares = lineas.reduce(
    (sum, l) => sum + l.tallas.reduce((s, t) => s + t.pares, 0),
    0,
  );

  // ── Guardar ──

  const onGuardar = async () => {
    if (!clienteSeleccionado) {
      Alert.alert('Error', 'Selecciona un cliente');
      return;
    }

    const lineasValidas = lineas.filter((l) => l.modelo.trim() !== '');
    if (lineasValidas.length === 0) {
      Alert.alert('Error', 'Agrega al menos una linea con modelo');
      return;
    }

    if (totalPares === 0) {
      Alert.alert('Error', 'Agrega pares a al menos una talla');
      return;
    }

    setGuardando(true);
    const resultado = await crearPedido({
      cliente_id: clienteSeleccionado.id,
      cliente_nombre: clienteSeleccionado.nombre,
      folio_pedido: folioPedido.trim() || undefined,
      suela: suela.trim() || undefined,
      horma: horma.trim() || undefined,
      observaciones: observaciones.trim() || undefined,
      lineas: lineasValidas.map((l) => ({
        modelo: l.modelo.trim(),
        piel: l.piel.trim(),
        color: l.color.trim(),
        tallas: l.tallas.filter((t) => t.pares > 0),
      })),
    });
    setGuardando(false);

    if (resultado.ok) {
      Alert.alert(
        'Pedido creado',
        `Folio: ${resultado.folio}\nTotal: ${totalPares} pares`,
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ],
      );
    } else {
      Alert.alert('Error', resultado.error || 'No se pudo crear el pedido');
    }
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

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.botonVolver} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#ffffff" />
        </Pressable>
        <Text style={styles.headerTitulo}>Capturar Pedido</Text>
        <View style={{ width: 30 }} />
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scroll}>
          {/* Seleccion de cliente */}
          <Text style={styles.seccion}>Cliente *</Text>
          <View style={styles.selectorContainer}>
            <TextInput
              style={styles.input}
              placeholder="Buscar cliente..."
              value={buscarCliente}
              onChangeText={(text) => {
                setBuscarCliente(text);
                setMostrarClientes(true);
                if (text === '') setClienteSeleccionado(null);
              }}
              onFocus={() => setMostrarClientes(true)}
            />
            <Pressable
              style={styles.botonDropdown}
              onPress={() => setMostrarClientes(!mostrarClientes)}
            >
              <Ionicons
                name={mostrarClientes ? 'chevron-up' : 'chevron-down'}
                size={18}
                color={colores.textoSuave}
              />
            </Pressable>
          </View>

          {mostrarClientes && (
            <View style={styles.listaDropdown}>
              <FlatList
                data={clientesFiltrados.slice(0, 10)}
                keyExtractor={(item) => item.id.toString()}
                renderItem={({ item }) => (
                  <Pressable
                    style={[
                      styles.itemDropdown,
                      clienteSeleccionado?.id === item.id && styles.itemDropdownActivo,
                    ]}
                    onPress={() => seleccionarCliente(item)}
                  >
                    <Text style={styles.itemDropdownTexto}>{item.nombre}</Text>
                    {item.rfc && (
                      <Text style={styles.itemDropdownDet}>{item.rfc}</Text>
                    )}
                  </Pressable>
                )}
                ListEmptyComponent={
                  <Text style={styles.sinResultados}>No hay clientes</Text>
                }
                scrollEnabled={false}
              />
            </View>
          )}

          {clienteSeleccionado && (
            <View style={styles.clienteSeleccionado}>
              <Ionicons name="checkmark-circle" size={16} color={colores.exito} />
              <Text style={styles.clienteSeleccionadoTexto}>
                {clienteSeleccionado.nombre}
              </Text>
            </View>
          )}

          {/* Info adicional */}
          <Text style={styles.seccion}>Informacion adicional</Text>
          <TextInput
            style={styles.input}
            placeholder="Folio pedido cliente (opcional)"
            value={folioPedido}
            onChangeText={setFolioPedido}
          />
          <View style={styles.row}>
            <TextInput
              style={[styles.input, styles.inputMedio]}
              placeholder="Suela"
              value={suela}
              onChangeText={setSuela}
            />
            <TextInput
              style={[styles.input, styles.inputMedio]}
              placeholder="Horma"
              value={horma}
              onChangeText={setHorma}
            />
          </View>
          <TextInput
            style={[styles.input, styles.inputMultiline]}
            placeholder="Observaciones (opcional)"
            value={observaciones}
            onChangeText={setObservaciones}
            multiline
            numberOfLines={2}
          />

          {/* Lineas del pedido */}
          <View style={styles.seccionRow}>
            <Text style={styles.seccion}>Lineas del pedido</Text>
            <Pressable style={styles.botonAgregar} onPress={agregarLinea}>
              <Ionicons name="add-circle" size={18} color="#ffffff" />
              <Text style={styles.textoAgregar}>Agregar linea</Text>
            </Pressable>
          </View>

          {lineas.map((linea, lineaIdx) => (
            <View key={lineaIdx} style={styles.cardLinea}>
              <View style={styles.cardLineaHeader}>
                <Text style={styles.cardLineaNum}>Linea {lineaIdx + 1}</Text>
                {lineas.length > 1 && (
                  <Pressable onPress={() => eliminarLinea(lineaIdx)}>
                    <Ionicons name="trash-outline" size={18} color={colores.peligro} />
                  </Pressable>
                )}
              </View>

              <TextInput
                style={styles.input}
                placeholder="Modelo *"
                value={linea.modelo}
                onChangeText={(v) => actualizarLinea(lineaIdx, 'modelo', v)}
              />
              <View style={styles.row}>
                <TextInput
                  style={[styles.input, styles.inputMedio]}
                  placeholder="Piel"
                  value={linea.piel}
                  onChangeText={(v) => actualizarLinea(lineaIdx, 'piel', v)}
                />
                <TextInput
                  style={[styles.input, styles.inputMedio]}
                  placeholder="Color"
                  value={linea.color}
                  onChangeText={(v) => actualizarLinea(lineaIdx, 'color', v)}
                />
              </View>

              {/* Tallas / puntos */}
              <Text style={styles.tallasLabel}>Pares por talla:</Text>
              <View style={styles.tallasGrid}>
                {linea.tallas.map((t, tIdx) => (
                  <View key={tIdx} style={styles.tallaItem}>
                    <Text style={styles.tallaNum}>#{t.talla}</Text>
                    <TextInput
                      style={styles.inputTalla}
                      placeholder="0"
                      keyboardType="numeric"
                      value={t.pares > 0 ? String(t.pares) : ''}
                      onChangeText={(v) => {
                        const num = parseInt(v, 10) || 0;
                        actualizarTallaEnLinea(lineaIdx, tIdx, num);
                      }}
                    />
                  </View>
                ))}
              </View>

              {/* Total de la linea */}
              <View style={styles.lineaTotal}>
                <Text style={styles.lineaTotalTexto}>
                  Total linea: {linea.tallas.reduce((s, t) => s + t.pares, 0)} pares
                </Text>
              </View>
            </View>
          ))}
        </ScrollView>

        {/* Footer con total y boton guardar */}
        <View style={styles.footer}>
          <View style={styles.footerTotal}>
            <Text style={styles.footerTotalLabel}>Total:</Text>
            <Text style={styles.footerTotalNumero}>{totalPares} pares</Text>
          </View>
          <Pressable
            style={[styles.botonGuardar, guardando && styles.botonDeshabilitado]}
            onPress={onGuardar}
            disabled={guardando}
          >
            {guardando ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <>
                <Ionicons name="checkmark-circle-outline" size={20} color="#ffffff" />
                <Text style={styles.textoGuardar}>Guardar pedido</Text>
              </>
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: colores.primario,
  },
  botonVolver: { padding: 6 },
  headerTitulo: { fontSize: fuentes.subtitulo, fontWeight: 'bold', color: '#ffffff' },
  scroll: { padding: 16, paddingBottom: 100 },
  seccion: { fontSize: fuentes.subtitulo, fontWeight: 'bold', color: colores.texto, marginBottom: 8 },
  seccionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colores.tarjeta,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    marginBottom: 8,
  },
  inputMedio: { flex: 1 },
  inputMultiline: { height: 60, textAlignVertical: 'top' },
  row: { flexDirection: 'row', gap: 8 },

  // Dropdown clientes
  selectorContainer: { flexDirection: 'row', alignItems: 'center' },
  botonDropdown: {
    position: 'absolute',
    right: 12,
    padding: 8,
  },
  listaDropdown: {
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    marginBottom: 8,
    maxHeight: 200,
  },
  itemDropdown: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
  },
  itemDropdownActivo: { backgroundColor: colores.primario + '15' },
  itemDropdownTexto: { fontSize: fuentes.cuerpo, color: colores.texto },
  itemDropdownDet: { fontSize: fuentes.pequena, color: colores.textoSuave },
  sinResultados: { padding: 12, textAlign: 'center', color: colores.textoSuave },
  clienteSeleccionado: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colores.exito + '15',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  clienteSeleccionadoTexto: { fontSize: fuentes.cuerpo, fontWeight: '600', color: colores.exito },

  // Lineas
  botonAgregar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colores.exito,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  textoAgregar: { fontSize: fuentes.pequena, color: '#ffffff', fontWeight: 'bold' },
  cardLinea: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardLineaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardLineaNum: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  tallasLabel: {
    fontSize: fuentes.etiqueta,
    fontWeight: '600',
    color: colores.texto,
    marginTop: 4,
    marginBottom: 6,
  },
  tallasGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tallaItem: {
    alignItems: 'center',
    width: 52,
  },
  tallaNum: { fontSize: 10, color: colores.textoSuave, marginBottom: 2 },
  inputTalla: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 4,
    backgroundColor: colores.fondo,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    textAlign: 'center',
    width: '100%',
  },
  lineaTotal: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  lineaTotalTexto: { fontSize: fuentes.etiqueta, fontWeight: 'bold', color: colores.primario },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colores.tarjeta,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  footerTotal: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  footerTotalLabel: { fontSize: fuentes.etiqueta, color: colores.textoSuave },
  footerTotalNumero: { fontSize: fuentes.titulo, fontWeight: 'bold', color: colores.primario },
  botonGuardar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colores.primario,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  botonDeshabilitado: { opacity: 0.6 },
  textoGuardar: { fontSize: fuentes.cuerpo, color: '#ffffff', fontWeight: 'bold' },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
