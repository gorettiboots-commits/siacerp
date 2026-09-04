import React, { useCallback, useEffect, useState } from 'react';
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
import type { InventarioStackParamList } from '../navegacion';
import type { InsumoMovil } from '../tipos';
import { buscarInsumos, obtenerStockBajo } from '../servicios/inventario';

type Nav = NativeStackNavigationProp<InventarioStackParamList, 'ListaInsumos'>;

export function PantallaInventario() {
  const navigation = useNavigation<Nav>();
  const [termino, setTermino] = useState('');
  const [insumos, setInsumos] = useState<InsumoMovil[]>([]);
  const [stockBajo, setStockBajo] = useState<InsumoMovil[]>([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarBajo, setMostrarBajo] = useState(false);

  const cargarDatos = useCallback(async () => {
    try {
      setCargando(true);
      const resultado = termino.trim()
        ? await buscarInsumos(termino)
        : await buscarInsumos('');

      if (resultado.ok) {
        setInsumos(resultado.datos);
      }

      const bajo = await obtenerStockBajo();
      if (bajo.ok) {
        setStockBajo(bajo.datos);
      }
      setCargando(false);
    } catch (e: any) {
      console.error('[Inventario] Error:', e.message);
      setCargando(false);
    }
  }, [termino]);

  useEffect(() => {
    cargarDatos();
  }, []);

  const handleBuscar = async () => {
    setCargando(true);
    const resultado = termino.trim()
      ? await buscarInsumos(termino)
      : await buscarInsumos('');
    if (resultado.ok) {
      setInsumos(resultado.datos);
    }
    setCargando(false);
  };

  const renderInsumo = ({ item }: { item: InsumoMovil }) => {
    const esBajo = item.stock_actual <= item.stock_minimo;
    return (
      <Pressable
        style={[styles.card, esBajo && styles.cardBajo]}
        onPress={() => navigation.navigate('DetalleInsumo', { insumoId: item.id })}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardCodigo}>{item.codigo}</Text>
          {esBajo && <Text style={styles.badgeBajo}>STOCK BAJO</Text>}
        </View>
        <Text style={styles.cardNombre}>{item.nombre}</Text>
        <View style={styles.cardFooter}>
          <Text style={styles.cardCategoria}>{item.categoria}</Text>
          <Text style={[styles.cardStock, esBajo && styles.cardStockBajo]}>
            {item.stock_actual} {item.unidad_medida}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <View style={styles.contenedor}>
      {/* Encabezado */}
      <View style={styles.header}>
        <Text style={styles.titulo}>Inventario</Text>
        <Text style={styles.subtitulo}>
          {insumos.length} insumos · {stockBajo.length} con stock bajo
        </Text>
      </View>

      {/* Buscador */}
      <View style={styles.busqueda}>
        <TextInput
          style={styles.inputBusqueda}
          placeholder="Buscar por código, nombre o categoría..."
          value={termino}
          onChangeText={setTermino}
          onSubmitEditing={handleBuscar}
          returnKeyType="search"
        />
        <Pressable style={styles.botonBuscar} onPress={handleBuscar}>
          <Text style={styles.textoBotonBuscar}>🔍</Text>
        </Pressable>
      </View>

      {/* Filtro stock bajo */}
      {stockBajo.length > 0 && (
        <Pressable
          style={[styles.filtroBajo, mostrarBajo && styles.filtroBajoActivo]}
          onPress={() => setMostrarBajo(!mostrarBajo)}
        >
          <Text style={[styles.textoFiltroBajo, mostrarBajo && styles.textoFiltroBajoActivo]}>
            ⚠️ Stock bajo ({stockBajo.length})
          </Text>
        </Pressable>
      )}

      {/* Lista */}
      {cargando ? (
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
          <Text style={styles.textoCargando}>Cargando insumos...</Text>
        </View>
      ) : (
        <FlatList
          data={mostrarBajo ? stockBajo : insumos}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderInsumo}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vacio}>
              <Text style={styles.textoVacio}>No se encontraron insumos</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  header: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  titulo: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  subtitulo: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
    marginTop: 2,
  },
  busqueda: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 8,
    gap: 8,
  },
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
  filtroBajo: {
    marginHorizontal: 16,
    marginBottom: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  filtroBajoActivo: {
    backgroundColor: '#F59E0B',
  },
  textoFiltroBajo: {
    fontSize: fuentes.etiqueta,
    color: '#92400E',
    fontWeight: '600',
    textAlign: 'center',
  },
  textoFiltroBajoActivo: {
    color: '#ffffff',
  },
  lista: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  card: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  cardBajo: {
    borderColor: '#F59E0B',
    borderLeftWidth: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  cardCodigo: {
    fontSize: fuentes.etiqueta,
    color: colores.primario,
    fontWeight: 'bold',
  },
  badgeBajo: {
    fontSize: 10,
    color: '#ffffff',
    backgroundColor: '#F59E0B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontWeight: 'bold',
  },
  cardNombre: {
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    fontWeight: '500',
    marginBottom: 6,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardCategoria: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
  },
  cardStock: {
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
    color: colores.exito,
  },
  cardStockBajo: {
    color: colores.peligro,
  },
  cargando: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  textoCargando: {
    color: colores.textoSuave,
    fontSize: fuentes.cuerpo,
  },
  vacio: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  textoVacio: {
    color: colores.textoSuave,
    fontSize: fuentes.cuerpo,
  },
});
