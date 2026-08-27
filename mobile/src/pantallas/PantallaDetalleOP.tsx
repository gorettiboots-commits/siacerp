import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';

import { colores, fuentes } from '../theme';
import type { ProduccionStackParamList } from '../navegacion';
import type { SeguimientoMovil } from '../tipos';
import { obtenerSeguimiento, cambiarEstatusLinea, avanzarEstacion, actualizarAvance } from '../servicios/produccion';

type Route = RouteProp<ProduccionStackParamList, 'DetalleOP'>;

const COLORES_ESTADO: Record<string, string> = {
  pendiente: colores.textoSuave,
  en_proceso: '#F59E0B',
  completado: colores.exito,
};

const ICONOS_ESTADO: Record<string, string> = {
  pendiente: '○',
  en_proceso: '◉',
  completado: '✓',
};

export function PantallaDetalleOP() {
  const navigation = useNavigation();
  const route = useRoute<Route>();
  const { opId } = route.params;

  const [seguimiento, setSeguimiento] = useState<SeguimientoMovil[]>([]);
  const [cargando, setCargando] = useState(true);
  const [editando, setEditando] = useState<number | null>(null);
  const [paresNuevos, setParesNuevos] = useState('');
  const [defectuosos, setDefectuosos] = useState('');
  const [observaciones, setObservaciones] = useState('');

  useEffect(() => {
    cargarSeguimiento();
  }, []);

  const cargarSeguimiento = async () => {
    const resultado = await obtenerSeguimiento(opId);
    if (resultado.ok) {
      setSeguimiento(resultado.datos);
    }
    setCargando(false);
  };

  const handleCambiarEstatus = async (seguimientoId: number, nuevoEstatus: string) => {
    Alert.alert(
      'Cambiar estatus',
      `¿Cambiar a "${nuevoEstatus.replace('_', ' ')}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Confirmar',
          onPress: async () => {
            const resultado = await cambiarEstatusLinea(seguimientoId, nuevoEstatus);
            if (resultado.ok) {
              Alert.alert('Éxito', 'Estatus actualizado');
              cargarSeguimiento();
            } else {
              Alert.alert('Error', resultado.error || 'Error desconocido');
            }
          },
        },
      ],
    );
  };

  const handleAvanzar = async (seguimientoId: number) => {
    const resultado = await avanzarEstacion(opId, seguimientoId);
    if (resultado.ok) {
      Alert.alert('Avance', 'Estación avanzada correctamente');
      cargarSeguimiento();
    } else {
      Alert.alert('Error', resultado.error || 'No se pudo avanzar');
    }
  };

  const handleGuardarAvance = async (seguimientoId: number) => {
    const pares = parseInt(paresNuevos, 10);
    if (isNaN(pares) || pares < 0) {
      Alert.alert('Error', 'Ingresa un número válido de pares.');
      return;
    }

    const defect = parseInt(defectuosos, 10) || 0;

    const resultado = await actualizarAvance(
      seguimientoId,
      pares,
      defect,
      observaciones || undefined,
    );
    if (resultado.ok) {
      Alert.alert('Avance guardado', `${pares} pares procesados, ${defect} defectuosos`);
      setEditando(null);
      setParesNuevos('');
      setDefectuosos('');
      setObservaciones('');
      cargarSeguimiento();
    } else {
      Alert.alert('Error', resultado.error || 'Error al guardar');
    }
  };

  if (cargando) {
    return (
      <View style={styles.cargando}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.contenedor}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()}>
          <Text style={styles.volver}>← Volver</Text>
        </Pressable>
        <Text style={styles.titulo}>Avance de Producción</Text>
      </View>

      {/* Kanban vertical */}
      {seguimiento.map((seg, idx) => {
        const color = COLORES_ESTADO[seg.estatus] || colores.textoSuave;
        const icono = ICONOS_ESTADO[seg.estatus] || '○';
        const esEditando = editando === seg.id;

        return (
          <View key={seg.id} style={styles.estacion}>
            {/* Línea de conexión */}
            {idx > 0 && (
              <View style={[styles.linea, { backgroundColor: color }]} />
            )}

            {/* Tarjeta de estación */}
            <View style={[styles.estacionCard, { borderLeftColor: color }]}>
              <View style={styles.estacionHeader}>
                <Text style={[styles.estacionIcono, { color }]}>{icono}</Text>
                <View style={styles.estacionInfo}>
                  <Text style={styles.estacionNombre}>{seg.estacion_nombre}</Text>
                  <Text style={[styles.estacionEstatus, { color }]}>
                    {seg.estatus.replace('_', ' ')}
                  </Text>
                </View>
              </View>

              {/* Pares procesados */}
              <View style={styles.paresRow}>
                <View style={styles.paresItem}>
                  <Text style={styles.paresValor}>{seg.pares_procesados}</Text>
                  <Text style={styles.paresLabel}>Procesados</Text>
                </View>
                <View style={styles.paresItem}>
                  <Text style={[styles.paresValor, styles.paresDefecto]}>
                    {seg.pares_defectuosos}
                  </Text>
                  <Text style={styles.paresLabel}>Defectuosos</Text>
                </View>
              </View>

              {/* Botones de acción */}
              <View style={styles.acciones}>
                {seg.estatus === 'pendiente' && (
                  <Pressable
                    style={styles.botonIniciar}
                    onPress={() => handleCambiarEstatus(seg.id, 'en_proceso')}
                  >
                    <Text style={styles.textoBotonIniciar}>▶ Iniciar</Text>
                  </Pressable>
                )}

                {seg.estatus === 'en_proceso' && (
                  <>
                    <Pressable
                      style={styles.botonAvanzar}
                      onPress={() => handleAvanzar(seg.id)}
                    >
                      <Text style={styles.textoBotonAvanzar}>→ Avanzar</Text>
                    </Pressable>

                    {!esEditando ? (
                      <Pressable
                        style={styles.botonEditar}
                        onPress={() => setEditando(seg.id)}
                      >
                        <Text style={styles.textoBotonEditar}>✎ Editar</Text>
                      </Pressable>
                    ) : (
                      <View style={styles.formulario}>
                        <TextInput
                          style={styles.input}
                          placeholder="Pares procesados"
                          keyboardType="numeric"
                          value={paresNuevos}
                          onChangeText={setParesNuevos}
                        />
                        <TextInput
                          style={styles.input}
                          placeholder="Defectuosos"
                          keyboardType="numeric"
                          value={defectuosos}
                          onChangeText={setDefectuosos}
                        />
                        <TextInput
                          style={styles.input}
                          placeholder="Observaciones (opcional)"
                          value={observaciones}
                          onChangeText={setObservaciones}
                        />
                        <View style={styles.botonesForm}>
                          <Pressable
                            style={styles.botonCancelar}
                            onPress={() => { setEditando(null); setParesNuevos(''); setDefectuosos(''); }}
                          >
                            <Text style={styles.textoCancelar}>Cancelar</Text>
                          </Pressable>
                          <Pressable
                            style={styles.botonGuardar}
                            onPress={() => handleGuardarAvance(seg.id)}
                          >
                            <Text style={styles.textoGuardar}>Guardar</Text>
                          </Pressable>
                        </View>
                      </View>
                    )}
                  </>
                )}

                {seg.estatus === 'completado' && (
                  <Text style={styles.textoCompletado}>✓ Estación completada</Text>
                )}
              </View>
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  header: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 },
  volver: { color: colores.primario, fontSize: fuentes.cuerpo },
  titulo: { fontSize: fuentes.titulo, fontWeight: 'bold', color: colores.texto, marginTop: 8 },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  estacion: { paddingHorizontal: 16 },
  linea: { width: 3, height: 20, marginLeft: 24, borderRadius: 2 },
  estacionCard: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  estacionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  estacionIcono: { fontSize: 24, marginRight: 12 },
  estacionInfo: { flex: 1 },
  estacionNombre: { fontSize: fuentes.cuerpo, fontWeight: 'bold', color: colores.texto },
  estacionEstatus: { fontSize: fuentes.pequena, textTransform: 'capitalize' },
  paresRow: { flexDirection: 'row', gap: 24, marginBottom: 12 },
  paresItem: { alignItems: 'center' },
  paresValor: { fontSize: 22, fontWeight: 'bold', color: colores.texto },
  paresDefecto: { color: colores.peligro },
  paresLabel: { fontSize: 10, color: colores.textoSuave },
  acciones: { gap: 8 },
  botonIniciar: {
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  textoBotonIniciar: { color: '#ffffff', fontWeight: 'bold' },
  botonAvanzar: {
    backgroundColor: colores.exito,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  textoBotonAvanzar: { color: '#ffffff', fontWeight: 'bold' },
  botonEditar: {
    backgroundColor: colores.tarjeta,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colores.primario,
  },
  textoBotonEditar: { color: colores.primario, fontWeight: '600' },
  formulario: { gap: 8, marginTop: 8 },
  input: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colores.fondo,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
  },
  botonesForm: { flexDirection: 'row', gap: 8 },
  botonCancelar: {
    flex: 1,
    backgroundColor: colores.tarjeta,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colores.borde,
  },
  textoCancelar: { color: colores.textoSuave },
  botonGuardar: {
    flex: 1,
    backgroundColor: colores.exito,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  textoGuardar: { color: '#ffffff', fontWeight: 'bold' },
  textoCompletado: { color: colores.exito, fontWeight: '600', textAlign: 'center' },
});
