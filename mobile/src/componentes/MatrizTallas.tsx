import React from 'react';
import { FlatList, StyleSheet, Text, TextInput, View } from 'react-native';

import { colores, fuentes } from '../theme';

export const TALLAS: string[] = [
  '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',
  '12.5', '13', '13.5', '14', '14.5', '15', '15.5', '16', '16.5', '17', '17.5',
  '18', '18.5', '19', '19.5', '20', '20.5', '21', '21.5', '22', '22.5', '23',
  '23.5', '24', '24.5', '25', '25.5', '26', '26.5', '27', '27.5', '28', '28.5',
  '29', '29.5', '30', '30.5', '31',
];

interface Props {
  valores: Record<string, number>;
  onCambiar: (talla: string, cantidad: number) => void;
  tallas?: string[];
}

export function MatrizTallas({ valores, onCambiar, tallas = TALLAS }: Props) {
  return (
    <View style={styles.contenedor}>
      <View style={styles.filaEncabezado}>
        <Text style={styles.textoEncabezado}>TALLA</Text>
        <Text style={styles.textoEncabezado}>CANTIDAD DE ETIQUETAS</Text>
      </View>
      <FlatList
        data={tallas}
        keyExtractor={(t) => t}
        style={styles.lista}
        renderItem={({ item }) => {
          const cantidad = valores[item] ?? 0;
          return (
            <View style={styles.fila}>
              <Text style={styles.talla}>{item}</Text>
              <TextInput
                style={styles.campo}
                keyboardType="number-pad"
                value={String(cantidad)}
                onChangeText={(texto) => {
                  const num = parseInt(texto.replace(/[^0-9]/g, '') || '0', 10);
                  onCambiar(item, num);
                }}
              />
            </View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: {
    flex: 1,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colores.borde,
    backgroundColor: colores.tarjeta,
    overflow: 'hidden',
  },
  filaEncabezado: {
    flexDirection: 'row',
    backgroundColor: colores.encabezadoTabla,
    paddingVertical: 10,
    paddingHorizontal: 12,
    justifyContent: 'space-between',
  },
  lista: { flex: 1 },
  textoEncabezado: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: fuentes.etiqueta,
  },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colores.borde,
  },
  talla: {
    fontSize: fuentes.cuerpo,
    fontWeight: '600',
    color: colores.texto,
    width: 90,
  },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    width: 90,
    textAlign: 'center',
    fontSize: fuentes.cuerpo,
    color: colores.texto,
  },
});