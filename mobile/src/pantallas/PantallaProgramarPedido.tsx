import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
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
  obtenerPedido,
  obtenerDetallePedido,
  programarPedido,
} from '../servicios/pedidos';
import { listarSemanas } from '../servicios/programacion';
import type {
  PedidoClienteMovil,
  DetallePedidoMovil,
  ProgramacionSemanaMovil,
  PuntoPedidoMovil,
} from '../tipos';

interface Props {
  route: { params: { pedidoId: number; folio: string } };
  navigation: any;
}

interface DetalleProgramable {
  detalle_id: number;
  modelo: string;
  piel: string;
  color: string;
  tallas: { talla: string; pares: number; pares_originales: number }[];
  seleccionado: boolean;
}

export function PantallaProgramarPedido({ route, navigation }: Props) {
  const { pedidoId, folio } = route.params;
  const [pedido, setPedido] = useState<PedidoClienteMovil | null>(null);
  const [detalles, setDetalles] = useState<DetalleProgramable[]>([]);
  const [semanas, setSemanas] = useState<ProgramacionSemanaMovil[]>([]);
  const [semanaId, setSemanaId] = useState<number | null>(null);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    cargarDatos();
  }, [pedidoId]);

  const cargarDatos = async () => {
    setCargando(true);
    const [resPedido, resDetalle, resSemanas] = await Promise.all([
      obtenerPedido(pedidoId),
      obtenerDetallePedido(pedidoId),
      listarSemanas(),
    ]);

    if (resPedido.ok && resPedido.datos) {
      setPedido(resPedido.datos);
    }

    if (resDetalle.ok) {
      const prog: DetalleProgramable[] = resDetalle.datos.map((d) => ({
        detalle_id: d.id,
        modelo: d.modelo,
        piel: d.piel || '',
        color: d.color || '',
        tallas: (d.puntos || []).map((p) => ({
          talla: p.talla,
          pares: p.pares,
          pares_originales: p.pares,
        })),
        seleccionado: true,
      }));
      setDetalles(prog);
    }

    if (resSemanas.ok && resSemanas.datos.length > 0) {
      setSemanas(resSemanas.datos);
      // Seleccionar semana actual por defecto
      const hoy = new Date().toISOString().slice(0, 10);
      const semanaActual = resSemanas.datos.find((s) => {
        const ini = s.fecha_inicio;
        const fin = new Date(new Date(ini).getTime() + 6 * 86400000)
          .toISOString()
          .slice(0, 10);
        return hoy >= ini && hoy <= fin;
      });
      setSemanaId(semanaActual ? semanaActual.id : resSemanas.datos[0].id);
    }

    setCargando(false);
  };

  const toggleDetalle = (idx: number) => {
    setDetalles((prev) =>
      prev.map((d, i) => (i === idx ? { ...d, seleccionado: !d.seleccionado } : d)),
    );
  };

  const actualizarPares = (detIdx: number, tallaIdx: number, valor: string) => {
    const num = parseInt(valor, 10);
    const nuevo = isNaN(num) || num < 0 ? 0 : num;
    setDetalles((prev) =>
      prev.map((d, i) => {
        if (i !== detIdx) return d;
        return {
          ...d,
          tallas: d.tallas.map((t, j) =>
            j === tallaIdx ? { ...t, pares: nuevo } : t,
          ),
        };
      }),
    );
  };

  const seleccionarTodos = () => {
    const todosSel = detalles.every((d) => d.seleccionado);
    setDetalles((prev) => prev.map((d) => ({ ...d, seleccionado: !todosSel })));
  };

  const totalProgramar = detalles
    .filter((d) => d.seleccionado)
    .reduce(
      (sum, d) => sum + d.tallas.reduce((s, t) => s + t.pares, 0),
      0,
    );

  const handleProgramar = async () => {
    if (!semanaId) {
      Alert.alert('Selecciona una semana');
      return;
    }
    const seleccionados = detalles.filter((d) => d.seleccionado);
    if (seleccionados.length === 0) {
      Alert.alert('Selecciona al menos una linea');
      return;
    }

    // Verificar que tengan pares
    const conPares = seleccionados.filter((d) =>
      d.tallas.some((t) => t.pares > 0),
    );
    if (conPares.length === 0) {
      Alert.alert('Asigna pares a al menos una talla');
      return;
    }

    setEnviando(true);
    const resultado = await programarPedido(
      pedidoId,
      semanaId,
      conPares.map((d) => ({
        detalle_id: d.detalle_id,
        modelo: d.modelo,
        piel: d.piel,
        color: d.color,
        tallas: d.tallas.map((t) => ({ talla: t.talla, pares: t.pares })),
      })),
    );
    setEnviando(false);

    if (resultado.ok) {
      Alert.alert(
        'Pedido programado',
        `Se crearon ${resultado.folios?.length || 0} folio(s): ${resultado.folios?.join(', ')}`,
        [{ text: 'OK', onPress: () => navigation.goBack() }],
      );
    } else {
      Alert.alert('Error', resultado.error || 'No se pudo programar');
    }
  };

  const fmt_talla = (talla: string | number) => {
    const v = parseFloat(String(talla));
    return String(v);
  };

  const renderDetalle = (det: DetalleProgramable, idx: number) => (
    <View key={det.detalle_id} style={[styles.card, !det.seleccionado && styles.cardDesactivado]}>
      <Pressable style={styles.cardRow} onPress={() => toggleDetalle(idx)}>
        <Ionicons
          name={det.seleccionado ? 'checkbox' : 'square-outline'}
          size={22}
          color={det.seleccionado ? colores.primario : colores.textoSuave}
        />
        <View style={styles.cardInfo}>
          <Text style={styles.cardModelo}>{det.modelo}</Text>
          {(det.piel || det.color) && (
            <Text style={styles.cardDet}>
              {det.piel} {det.color ? `/ ${det.color}` : ''}
            </Text>
          )}
        </View>
        <Text style={styles.cardPares}>
          {det.tallas.reduce((s, t) => s + t.pares, 0)} pares
        </Text>
      </Pressable>

      {det.seleccionado && det.tallas.length > 0 && (
        <View style={styles.tallasContainer}>
          <Text style={styles.tallasTitulo}>Pares por talla:</Text>
          <View style={styles.tallasGrid}>
            {det.tallas.map((t, tIdx) => (
              <View key={tIdx} style={styles.tallaItem}>
                <Text style={styles.tallaLabel}>#{fmt_talla(t.talla)}</Text>
                <TextInput
                  style={styles.inputTalla}
                  keyboardType="numeric"
                  value={String(t.pares)}
                  onChangeText={(v) => actualizarPares(idx, tIdx, v)}
                />
              </View>
            ))}
          </View>
        </View>
      )}
    </View>
  );

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
      <View style={styles.header}>
        <Text style={styles.headerFolio}>Programar: {folio}</Text>
        {pedido && (
          <Text style={styles.headerCliente}>{pedido.cliente_nombre}</Text>
        )}
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Selector de semana */}
        <View style={styles.seccion}>
          <Text style={styles.seccionTitulo}>Semana de produccion</Text>
          {semanas.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {semanas.map((s) => (
                <Pressable
                  key={s.id}
                  style={[
                    styles.semanaChip,
                    semanaId === s.id && styles.semanaChipActivo,
                  ]}
                  onPress={() => setSemanaId(s.id)}
                >
                  <Text
                    style={[
                      styles.semanaTexto,
                      semanaId === s.id && styles.semanaTextoActivo,
                    ]}
                    numberOfLines={2}
                  >
                    {s.nombre}
                  </Text>
                </Pressable>
              ))}
            </ScrollView>
          ) : (
            <Text style={styles.sinSemanas}>
              No hay semanas disponibles. Crea una en el escritorio.
            </Text>
          )}
        </View>

        {/* Seleccionar todos */}
        <View style={styles.accionBar}>
          <Pressable onPress={seleccionarTodos} style={styles.botonSeleccionar}>
            <Text style={styles.textoSeleccionar}>
              {detalles.every((d) => d.seleccionado)
                ? 'Desmarcar todas'
                : 'Seleccionar todas'}
            </Text>
          </Pressable>
          <Text style={styles.totalPares}>
            {totalProgramar} pares a programar
          </Text>
        </View>

        {/* Detalles del pedido */}
        <View style={styles.seccion}>
          <Text style={styles.seccionTitulo}>
            Lineas del pedido ({detalles.length})
          </Text>
          {detalles.map((det, idx) => renderDetalle(det, idx))}
        </View>
      </ScrollView>

      {/* Boton programar */}
      <View style={styles.footer}>
        <Pressable
          style={[
            styles.botonProgramar,
            (!semanaId || totalProgramar === 0 || enviando) &&
              styles.botonDeshabilitado,
          ]}
          onPress={handleProgramar}
          disabled={!semanaId || totalProgramar === 0 || enviando}
        >
          {enviando ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <>
              <Ionicons name="calendar-outline" size={20} color="#ffffff" />
              <Text style={styles.textoProgramar}>
                Programar ({totalProgramar} pares)
              </Text>
            </>
          )}
        </Pressable>
      </View>
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
  scroll: { paddingBottom: 80 },
  seccion: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 4 },
  seccionTitulo: {
    fontSize: fuentes.subtitulo,
    fontWeight: 'bold',
    color: colores.texto,
    marginBottom: 8,
  },
  semanaChip: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    marginRight: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  semanaChipActivo: { backgroundColor: colores.primario, borderColor: colores.primario },
  semanaTexto: { fontSize: fuentes.pequena, color: colores.textoSuave, textAlign: 'center' },
  semanaTextoActivo: { color: '#ffffff', fontWeight: 'bold' },
  sinSemanas: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
    fontStyle: 'italic',
  },
  accionBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  botonSeleccionar: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: colores.fondo,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  textoSeleccionar: { fontSize: fuentes.pequena, color: colores.primario, fontWeight: '500' },
  totalPares: { fontSize: fuentes.pequena, color: colores.textoSuave, fontWeight: 'bold' },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardDesactivado: { opacity: 0.5 },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  cardInfo: { flex: 1 },
  cardModelo: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  cardDet: { fontSize: fuentes.etiqueta, color: colores.textoSuave, marginTop: 2 },
  cardPares: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.primario },
  tallasContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  tallasTitulo: { fontSize: fuentes.pequena, color: colores.textoSuave, marginBottom: 6 },
  tallasGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tallaItem: {
    alignItems: 'center',
    backgroundColor: colores.fondo,
    borderRadius: 8,
    padding: 6,
    borderWidth: 1,
    borderColor: colores.borde,
    minWidth: 60,
  },
  tallaLabel: { fontSize: 10, color: colores.textoSuave, marginBottom: 4 },
  inputTalla: {
    width: 50,
    height: 32,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    textAlign: 'center',
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    backgroundColor: colores.tarjeta,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: colores.fondo,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  botonProgramar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: colores.primario,
    paddingVertical: 14,
    borderRadius: 10,
  },
  botonDeshabilitado: { opacity: 0.5 },
  textoProgramar: { fontSize: fuentes.subtitulo, color: '#ffffff', fontWeight: 'bold' },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
