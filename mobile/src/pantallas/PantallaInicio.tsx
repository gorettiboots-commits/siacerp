import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colores, fuentes } from '../theme';

interface Props {
  onFlejes: () => void;
  onPartidas: () => void;
}

export function PantallaInicio({ onFlejes, onPartidas }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      <View style={styles.contenedor}>
        <Text style={styles.titulo}>Imprimir Etiquetas</Text>
        <Text style={styles.subtitulo}>
          Seleccione el tipo de etiquetas a imprimir
        </Text>

        <Pressable style={styles.boton} onPress={onFlejes}>
          <Text style={styles.textoBoton}>Flejes (Cajas)</Text>
        </Pressable>

        <Pressable style={styles.boton} onPress={onPartidas}>
          <Text style={styles.textoBoton}>Partidas</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  contenedor: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 16,
  },
  titulo: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
    textAlign: 'center',
  },
  subtitulo: {
    fontSize: fuentes.subtitulo,
    color: colores.textoSuave,
    textAlign: 'center',
    marginBottom: 12,
  },
  boton: {
    backgroundColor: colores.primario,
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginVertical: 4,
  },
  textoBoton: {
    color: '#ffffff',
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
  },
});