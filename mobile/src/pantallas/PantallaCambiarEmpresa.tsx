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
import {
  listarEmpresas,
  cambiarEmpresaContexto,
  obtenerEmpresaId,
} from '../servicios/auth';

interface Props {
  onVolver: () => void;
}

interface EmpresaItem {
  id: string;
  nombre: string;
  activo: boolean;
}

export function PantallaCambiarEmpresa({ onVolver }: Props) {
  const [empresas, setEmpresas] = useState<EmpresaItem[]>([]);
  const [cargando, setCargando] = useState(true);
  const empresaActualId = obtenerEmpresaId();

  useEffect(() => {
    cargarEmpresas();
  }, []);

  const cargarEmpresas = async () => {
    setCargando(true);
    const resultado = await listarEmpresas();
    if (resultado.ok) {
      setEmpresas(resultado.datos);
    }
    setCargando(false);
  };

  const seleccionarEmpresa = async (empresa: EmpresaItem) => {
    if (!empresa.activo) return;
    await cambiarEmpresaContexto(empresa.id, empresa.nombre);
    onVolver();
  };

  const quitarContexto = async () => {
    await cambiarEmpresaContexto(null);
    onVolver();
  };

  const renderEmpresa = ({ item }: { item: EmpresaItem }) => {
    const esSeleccionada = empresaActualId === item.id;
    return (
      <Pressable
        style={[
          styles.card,
          esSeleccionada && styles.cardSeleccionada,
          !item.activo && styles.cardInactiva,
        ]}
        onPress={() => seleccionarEmpresa(item)}
        disabled={!item.activo}
      >
        <View style={styles.cardContent}>
          <View style={styles.cardIcon}>
            <Ionicons
              name={esSeleccionada ? 'checkmark-circle' : 'business-outline'}
              size={24}
              color={esSeleccionada ? colores.exito : colores.primario}
            />
          </View>
          <View style={styles.cardInfo}>
            <Text style={[styles.cardNombre, !item.activo && styles.textoInactivo]}>
              {item.nombre}
            </Text>
            {!item.activo && (
              <Text style={styles.cardInactivaLabel}>Desactivada</Text>
            )}
          </View>
          {esSeleccionada && (
            <Ionicons name="chevron-forward" size={18} color={colores.exito} />
          )}
        </View>
      </Pressable>
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.botonVolver} onPress={onVolver}>
          <Ionicons name="arrow-back" size={20} color={colores.texto} />
        </Pressable>
        <View style={styles.headerTexto}>
          <Text style={styles.headerTitulo}>Cambiar Empresa</Text>
          <Text style={styles.headerSubtitulo}>
            Selecciona la empresa que deseas administrar
          </Text>
        </View>
      </View>

      {/* Botón quitar contexto */}
      {empresaActualId && (
        <Pressable style={styles.botonQuitar} onPress={quitarContexto}>
          <Ionicons name="close-circle-outline" size={16} color={colores.peligro} />
          <Text style={styles.textoBotonQuitar}>Quitar filtro de empresa</Text>
        </Pressable>
      )}

      {/* Lista */}
      {cargando ? (
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
        </View>
      ) : (
        <FlatList
          data={empresas}
          keyExtractor={(item) => item.id}
          renderItem={renderEmpresa}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No se encontraron empresas</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colores.tarjeta,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
    gap: 12,
  },
  botonVolver: {
    padding: 8,
  },
  headerTexto: { flex: 1 },
  headerTitulo: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  headerSubtitulo: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
    marginTop: 2,
  },
  botonQuitar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 4,
    paddingVertical: 10,
    backgroundColor: '#FEE2E2',
    borderRadius: 8,
  },
  textoBotonQuitar: {
    fontSize: fuentes.etiqueta,
    fontWeight: '600',
    color: colores.peligro,
  },
  lista: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardSeleccionada: {
    borderColor: colores.exito,
    borderWidth: 2,
    backgroundColor: '#F0FDF4',
  },
  cardInactiva: {
    opacity: 0.5,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardIcon: {
    width: 36,
    alignItems: 'center',
  },
  cardInfo: {
    flex: 1,
  },
  cardNombre: {
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  cardInactivaLabel: {
    fontSize: fuentes.pequena,
    color: colores.peligro,
    marginTop: 2,
  },
  textoInactivo: {
    color: colores.textoSuave,
  },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  vacio: { paddingVertical: 40, alignItems: 'center' },
  textoVacio: { color: colores.textoSuave, fontSize: fuentes.cuerpo },
});
