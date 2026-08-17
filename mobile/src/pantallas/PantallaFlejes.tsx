import React, { useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colores, fuentes } from '../theme';
import type { PartidaFleje } from '../tipos';
import { PantallaPreview } from './PantallaPreview';

interface Props {
  onVolver: () => void;
}

function nuevaPartida(): PartidaFleje {
  return { id: `${Date.now()}-${Math.random()}`, texto: '', cantidad: 1 };
}

export function PantallaFlejes({ onVolver }: Props) {
  const [partidas, setPartidas] = useState<PartidaFleje[]>([nuevaPartida()]);
  const [enPreview, setEnPreview] = useState(false);

  const actualizarTexto = (id: string, texto: string) => {
    setPartidas((prev) => prev.map((p) => (p.id === id ? { ...p, texto } : p)));
  };

  const actualizarCantidad = (id: string, cantidad: number) => {
    setPartidas((prev) =>
      prev.map((p) => (p.id === id ? { ...p, cantidad } : p)),
    );
  };

  const agregar = () => setPartidas((prev) => [...prev, nuevaPartida()]);

  const quitar = (id: string) => {
    setPartidas((prev) => {
      const siguientes = prev.filter((p) => p.id !== id);
      return siguientes.length ? siguientes : [nuevaPartida()];
    });
  };

  const totalEtiquetas = partidas.reduce((acc, p) => acc + p.cantidad, 0);

  const validas = partidas.filter((p) => p.texto.trim().length > 0);

  const irAPreview = () => {
    if (!validas.length) {
      Alert.alert('Partidas', 'Agregue al menos una partida con texto.');
      return;
    }
    setEnPreview(true);
  };

  if (enPreview) {
    return (
      <PantallaPreview
        tipo="flejes"
        partidasFleje={validas}
        partidas={[]}
        onVolver={() => setEnPreview(false)}
      />
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.encabezado}>
        <Pressable onPress={onVolver}>
          <Text style={styles.volver}>‹ Volver</Text>
        </Pressable>
        <Text style={styles.titulo}>Flejes (Cajas)</Text>
        <View style={{ width: 60 }} />
      </View>

      <Text style={styles.informacion}>
        Agregue las partidas: el texto que dirá la etiqueta y la cantidad de
        etiquetas con ese texto.
      </Text>

      <View style={styles.encabezadoTabla}>
        <Text style={styles.textoEncabezadoTabla}>Texto de la etiqueta</Text>
        <Text style={styles.textoEncabezadoCantidad}>Cantidad</Text>
        <Text style={styles.textoEncabezadoAccion} />
      </View>

      <FlatList
        data={partidas}
        keyExtractor={(p) => p.id}
        style={styles.lista}
        renderItem={({ item }) => (
          <View style={styles.fila}>
            <TextInput
              style={styles.campoTexto}
              placeholder="Texto de la etiqueta"
              value={item.texto}
              onChangeText={(t) => actualizarTexto(item.id, t)}
            />
            <TextInput
              style={styles.campoCantidad}
              keyboardType="number-pad"
              value={String(item.cantidad)}
              onChangeText={(t) =>
                actualizarCantidad(
                  item.id,
                  parseInt(t.replace(/[^0-9]/g, '') || '0', 10),
                )
              }
            />
            <Pressable
              style={styles.botonQuitar}
              onPress={() => quitar(item.id)}
            >
              <Text style={styles.textoQuitar}>✕</Text>
            </Pressable>
          </View>
        )}
      />

      <View style={styles.pie}>
        <View style={styles.barraBotones}>
          <Pressable style={styles.botonSecundario} onPress={agregar}>
            <Text style={styles.textoBotonSecundario}>Agregar partida</Text>
          </Pressable>
          <Pressable style={styles.botonSecundario} onPress={onVolver}>
            <Text style={styles.textoBotonSecundario}>Cerrar</Text>
          </Pressable>
        </View>
        <Pressable style={styles.botonImprimir} onPress={irAPreview}>
          <Text style={styles.textoBotonImprimir}>
            Vista previa ({totalEtiquetas} etiquetas)
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  encabezado: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  volver: { color: colores.primario, fontSize: fuentes.cuerpo },
  titulo: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  informacion: {
    fontSize: fuentes.etiqueta,
    color: colores.textoSuave,
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  encabezadoTabla: {
    flexDirection: 'row',
    backgroundColor: colores.encabezadoTabla,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  textoEncabezadoTabla: {
    flex: 1,
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: fuentes.etiqueta,
  },
  textoEncabezadoCantidad: {
    width: 80,
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: fuentes.etiqueta,
  },
  textoEncabezadoAccion: { width: 44 },
  lista: { flex: 1, paddingHorizontal: 12 },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colores.borde,
  },
  campoTexto: {
    flex: 1,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 8,
    marginRight: 8,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    backgroundColor: colores.tarjeta,
  },
  campoCantidad: {
    width: 70,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 8,
    textAlign: 'center',
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    backgroundColor: colores.tarjeta,
  },
  botonQuitar: {
    width: 36,
    height: 36,
    borderRadius: 6,
    backgroundColor: colores.peligro,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  textoQuitar: { color: '#ffffff', fontSize: fuentes.cuerpo, fontWeight: 'bold' },
  pie: { padding: 16, gap: 10 },
  barraBotones: { flexDirection: 'row', gap: 10 },
  botonSecundario: {
    flex: 1,
    borderWidth: 1,
    borderColor: colores.primario,
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  textoBotonSecundario: { color: colores.primario, fontWeight: '600' },
  botonImprimir: {
    backgroundColor: colores.exito,
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  textoBotonImprimir: { color: '#ffffff', fontWeight: 'bold', fontSize: fuentes.cuerpo },
});