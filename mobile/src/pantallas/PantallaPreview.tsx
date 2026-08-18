import React from 'react';
import { Alert, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { enviarSolicitud } from '../servicios/impresion';
import { colores, fuentes } from '../theme';
import type { DatosEtiquetaPartida, PartidaFleje } from '../tipos';

interface Props {
  tipo: 'flejes' | 'partidas';
  partidasFleje: PartidaFleje[];
  partidas: DatosEtiquetaPartida[];
  onVolver: () => void;
}

interface ItemVista {
  id: string;
  titulo: string;
  detalle: string;
  cantidad: number;
}

export function PantallaPreview({
  tipo,
  partidasFleje,
  partidas,
  onVolver,
}: Props) {
  const items: ItemVista[] =
    tipo === 'flejes'
      ? partidasFleje.map((p, i) => ({
          id: `${i}-${p.texto}`,
          titulo: p.texto,
          detalle: `Fleje / Caja`,
          cantidad: p.cantidad,
        }))
      : partidas.map((p, i) => ({
          id: `${i}-${p.talla}`,
          titulo: p.talla,
          detalle: `${p.modelo} · ${p.corte} · ${p.color}`,
          cantidad: p.cantidad,
        }));

  const totalEtiquetas = items.reduce((acc, it) => acc + it.cantidad, 0);

  const enviar = async () => {
    const resultado = await enviarSolicitud({
      tipo,
      partidas_fleje: tipo === 'flejes' ? partidasFleje : [],
      partidas: tipo === 'partidas' ? partidas : [],
      solicitado_en: new Date().toISOString(),
      origen: 'movil',
    });
    Alert.alert(
      resultado.ok ? 'Enviado' : 'Sin enviar',
      resultado.mensaje,
      [{ text: 'Aceptar', onPress: resultado.ok ? onVolver : undefined }],
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.encabezado}>
        <Pressable onPress={onVolver}>
          <Text style={styles.volver}>‹ Volver</Text>
        </Pressable>
        <Text style={styles.titulo}>Vista previa</Text>
        <View style={{ width: 60 }} />
      </View>

      <Text style={styles.informacion}>
        Revisa las etiquetas antes de enviarlas a la impresora local.
      </Text>

      <FlatList
        data={items}
        keyExtractor={(it) => it.id}
        style={styles.lista}
        contentContainerStyle={styles.contenido}
        renderItem={({ item }) => (
          <View style={styles.tarjeta}>
            <View style={styles.bloqueEtiqueta}>
              <Text style={styles.etiqueta}>{item.titulo}</Text>
            </View>
            <View style={styles.datos}>
              <Text style={styles.detalle} numberOfLines={2}>
                {item.detalle}
              </Text>
              <Text style={styles.cantidad}>{item.cantidad} etiqueta(s)</Text>
            </View>
          </View>
        )}
      />

      <View style={styles.pie}>
        <View style={styles.barraBotones}>
          <Pressable style={styles.botonSecundario} onPress={onVolver}>
            <Text style={styles.textoBotonSecundario}>Ajustar</Text>
          </Pressable>
        </View>
        <Pressable style={styles.botonEnviar} onPress={enviar}>
          <Text style={styles.textoBotonEnviar}>
            Enviar a imprimir ({totalEtiquetas} etiquetas)
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
  lista: { flex: 1 },
  contenido: { paddingHorizontal: 16, gap: 12, paddingBottom: 8 },
  tarjeta: {
    flexDirection: 'row',
    backgroundColor: colores.tarjeta,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colores.borde,
    overflow: 'hidden',
  },
  bloqueEtiqueta: {
    width: 130,
    backgroundColor: '#ffffff',
    borderRightWidth: 1,
    borderRightColor: colores.borde,
    padding: 8,
    justifyContent: 'center',
  },
  etiqueta: {
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
    color: colores.texto,
    textAlign: 'center',
  },
  datos: { flex: 1, padding: 10, justifyContent: 'center' },
  detalle: { fontSize: fuentes.etiqueta, color: colores.textoSuave },
  cantidad: {
    fontSize: fuentes.cuerpo,
    fontWeight: '600',
    color: colores.texto,
    marginTop: 2,
  },
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
  botonEnviar: {
    backgroundColor: colores.exito,
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  textoBotonEnviar: { color: '#ffffff', fontWeight: 'bold', fontSize: fuentes.cuerpo },
});