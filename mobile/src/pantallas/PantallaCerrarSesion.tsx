import React from 'react';
import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colores, fuentes } from '../theme';
import { cerrarSesion, obtenerUsuarioActual, esSuperAdmin } from '../servicios/auth';

interface Props {
  onLogout: () => void;
}

export function PantallaCerrarSesion({ onLogout }: Props) {
  const usuario = obtenerUsuarioActual();

  const handleLogout = async () => {
    Alert.alert(
      'Cerrar sesión',
      '¿Estás seguro de que deseas cerrar sesión?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Cerrar sesión',
          style: 'destructive',
          onPress: async () => {
            await cerrarSesion();
            onLogout();
          },
        },
      ],
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.contenedor}>
        <View style={styles.avatar}>
          <Ionicons name="person-circle" size={80} color={colores.primario} />
        </View>

        <Text style={styles.nombre}>{usuario?.nombre_completo || 'Usuario'}</Text>
        <Text style={styles.username}>@{usuario?.username || 'username'}</Text>

        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Ionicons name="shield-checkmark" size={18} color={colores.textoSuave} />
            <Text style={styles.infoLabel}>Rol:</Text>
            <Text style={styles.infoValor}>{usuario?.rol || 'N/A'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Ionicons name="business" size={18} color={colores.textoSuave} />
            <Text style={styles.infoLabel}>Tipo:</Text>
            <Text style={styles.infoValor}>
              {esSuperAdmin() ? 'Super Administrador' : 'Usuario'}
            </Text>
          </View>
        </View>

        <View style={styles.version}>
          <Text style={styles.versionTexto}>SIAC ERP — v1.0.0</Text>
          <Text style={styles.versionCopy}>© 2026 Goretti. Todos los derechos reservados.</Text>
        </View>

        <Pressable style={styles.botonLogout} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color="#ffffff" />
          <Text style={styles.textoLogout}>Cerrar Sesión</Text>
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
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  avatar: {
    marginBottom: 16,
  },
  nombre: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
    textAlign: 'center',
  },
  username: {
    fontSize: fuentes.subtitulo,
    color: colores.textoSuave,
    marginTop: 4,
    marginBottom: 24,
  },
  infoCard: {
    backgroundColor: colores.tarjeta,
    borderRadius: 12,
    padding: 16,
    width: '100%',
    gap: 12,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  infoLabel: {
    fontSize: fuentes.cuerpo,
    color: colores.textoSuave,
  },
  infoValor: {
    fontSize: fuentes.cuerpo,
    color: colores.texto,
    fontWeight: '600',
  },
  version: {
    marginTop: 32,
    alignItems: 'center',
  },
  versionTexto: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
  },
  versionCopy: {
    fontSize: fuentes.pequena - 1,
    color: colores.textoSuave,
    marginTop: 4,
  },
  botonLogout: {
    flexDirection: 'row',
    backgroundColor: colores.peligro,
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    gap: 8,
    marginTop: 32,
    width: '100%',
    justifyContent: 'center',
  },
  textoLogout: {
    color: '#ffffff',
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
  },
});
