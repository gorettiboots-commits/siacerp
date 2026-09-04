import React, { useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { MatrizTallas } from '../componentes/MatrizTallas';
import { PantallaPreview } from './PantallaPreview';
import { colores, fuentes } from '../theme';
import type { DatosEtiquetaPartida } from '../tipos';
import { generar_corrida } from '../utilidades';

interface Props {
  onVolver: () => void;
}

export function PantallaPartidas({ onVolver }: Props) {
  const [modelo, setModelo] = useState('');
  const [corte, setCorte] = useState('');
  const [color, setColor] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [tallasGeneradas, setTallasGeneradas] = useState<string[]>([]);
  const [valores, setValores] = useState<Record<string, number>>({});
  const [enPreview, setEnPreview] = useState(false);

  const cambiarCantidad = (talla: string, cantidad: number) => {
    setValores((prev) => ({ ...prev, [talla]: cantidad }));
  };

  const generar = () => {
    const corrida = generar_corrida(desde.trim(), hasta.trim());
    if (!corrida.length) {
      Alert.alert(
        'Corrida',
        'Capture un rango válido (de X a Y) dentro del catálogo de tallas.',
      );
      return;
    }
    setTallasGeneradas(corrida);
    setValores({});
  };

  const partidas: DatosEtiquetaPartida[] = Object.entries(valores)
    .filter(([, cantidad]) => cantidad > 0)
    .map(([talla, cantidad]) => ({
      modelo: modelo.trim(),
      corte: corte.trim(),
      color: color.trim(),
      talla,
      cantidad,
    }));

  const totalEtiquetas = partidas.reduce((a, b) => a + b.cantidad, 0);

  const irAPreview = () => {
    if (!modelo.trim() || !corte.trim() || !color.trim()) {
      Alert.alert('Datos', 'Capture modelo, corte y color.');
      return;
    }
    if (!tallasGeneradas.length) {
      Alert.alert('Corrida', 'Genere la corrida de tallas (de X a Y) primero.');
      return;
    }
    if (!partidas.length) {
      Alert.alert('Cantidades', 'Indique al menos una cantidad por talla.');
      return;
    }
    setEnPreview(true);
  };

  if (enPreview) {
    return (
      <PantallaPreview
        tipo="partidas"
        partidasFleje={[]}
        partidas={partidas}
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
        <Text style={styles.titulo}>Partidas</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView
        style={styles.formulario}
        keyboardShouldPersistTaps="handled"
        nestedScrollEnabled
      >
        <Text style={styles.etiquetaCampo}>Modelo</Text>
        <TextInput
          style={styles.campo}
          placeholder="Ej: Botín Vaquero"
          value={modelo}
          onChangeText={setModelo}
        />
        <Text style={styles.etiquetaCampo}>Corte</Text>
        <TextInput
          style={styles.campo}
          placeholder="Corte de la piel"
          value={corte}
          onChangeText={setCorte}
        />
        <Text style={styles.etiquetaCampo}>Color</Text>
        <TextInput
          style={styles.campo}
          placeholder="Color"
          value={color}
          onChangeText={setColor}
        />

        <Text style={styles.etiquetaCampo}>Corrida de tallas (de X a Y)</Text>
        <View style={styles.filaCorrida}>
          <View style={styles.bloqueDesde}>
            <Text style={styles.etiquetaCampo}>Desde</Text>
            <TextInput
              style={styles.campo}
              placeholder="00"
              keyboardType="numbers-and-punctuation"
              value={desde}
              onChangeText={setDesde}
            />
          </View>
          <View style={styles.bloqueHasta}>
            <Text style={styles.etiquetaCampo}>Hasta</Text>
            <TextInput
              style={styles.campo}
              placeholder="31"
              keyboardType="numbers-and-punctuation"
              value={hasta}
              onChangeText={setHasta}
            />
          </View>
        </View>
        <Pressable style={styles.botonGenerar} onPress={generar}>
          <Text style={styles.textoBotonGenerar}>Generar partidas</Text>
        </Pressable>

        {tallasGeneradas.length > 0 && (
          <View style={styles.resumenCorrida}>
            <Text style={styles.textoResumenCorrida}>
              Corrida generada: {tallasGeneradas.length} tallas
            </Text>
          </View>
        )}
      </ScrollView>

      {tallasGeneradas.length > 0 && (
        <View style={styles.bloqueMatriz}>
          <MatrizTallas
            valores={valores}
            onCambiar={cambiarCantidad}
            tallas={tallasGeneradas}
          />
        </View>
      )}

      {tallasGeneradas.length > 0 && (
        <View style={styles.pie}>
          <Pressable style={styles.botonImprimir} onPress={irAPreview}>
            <Text style={styles.textoBotonImprimir}>
              Vista previa ({totalEtiquetas} etiquetas)
            </Text>
          </Pressable>
        </View>
      )}
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
  formulario: {
    flexShrink: 1,
    paddingHorizontal: 16,
    maxHeight: '45%',
  },
  etiquetaCampo: {
    fontSize: fuentes.etiqueta,
    color: colores.textoSuave,
    marginBottom: 4,
    marginTop: 8,
  },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colores.tarjeta,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
  },
  filaCorrida: {
    flexDirection: 'row',
    gap: 10,
  },
  bloqueDesde: { flex: 1 },
  bloqueHasta: { flex: 1 },
  botonGenerar: {
    marginTop: 10,
    backgroundColor: colores.primario,
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  textoBotonGenerar: { color: '#ffffff', fontWeight: 'bold' },
  resumenCorrida: {
    marginTop: 10,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: colores.advertencia,
  },
  textoResumenCorrida: { color: '#ffffff', fontWeight: '600' },
  bloqueMatriz: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
    minHeight: 0,
  },
  pie: { padding: 16 },
  botonImprimir: {
    backgroundColor: colores.exito,
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  textoBotonImprimir: { color: '#ffffff', fontWeight: 'bold', fontSize: fuentes.cuerpo },
});