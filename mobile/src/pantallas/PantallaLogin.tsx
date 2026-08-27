import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colores, fuentes } from '../theme';
import { iniciarSesion } from '../servicios/auth';

interface Props {
  onLogin: () => void;
}

export function PantallaLogin({ onLogin }: Props) {
  const [email, setEmail] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [cargando, setCargando] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !contrasena.trim()) {
      Alert.alert('Error', 'Ingresa tu correo y contraseña.');
      return;
    }

    setCargando(true);
    const resultado = await iniciarSesion(email.trim(), contrasena);
    setCargando(false);

    if (resultado.ok) {
      onLogin();
    } else {
      Alert.alert('Error de inicio de sesión', resultado.mensaje || 'Error desconocido');
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.contenedor}>
        <View style={styles.header}>
          <Text style={styles.titulo}>SIAC ERP</Text>
          <Text style={styles.subtitulo}>Sistema Integral de Administración</Text>
        </View>

        <View style={styles.formulario}>
          <Text style={styles.etiqueta}>Correo electrónico</Text>
          <TextInput
            style={styles.campo}
            placeholder="tu@correo.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!cargando}
          />

          <Text style={styles.etiqueta}>Contraseña</Text>
          <TextInput
            style={styles.campo}
            placeholder="••••••••"
            value={contrasena}
            onChangeText={setContrasena}
            secureTextEntry
            editable={!cargando}
          />

          <Pressable
            style={[styles.boton, cargando && styles.botonDeshabilitado]}
            onPress={handleLogin}
            disabled={cargando}
          >
            {cargando ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.textoBoton}>Iniciar Sesión</Text>
            )}
          </Pressable>
        </View>

        <Text style={styles.pie}>
          Versión 1.0.0 — © 2026 SIAC ERP
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  contenedor: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  titulo: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colores.primario,
    letterSpacing: 2,
  },
  subtitulo: {
    fontSize: fuentes.subtitulo,
    color: colores.textoSuave,
    marginTop: 4,
  },
  formulario: {
    gap: 12,
  },
  etiqueta: {
    fontSize: fuentes.etiqueta,
    color: colores.textoSuave,
    marginBottom: 2,
  },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    backgroundColor: colores.tarjeta,
    fontSize: fuentes.cuerpo,
    color: colores.texto,
  },
  boton: {
    backgroundColor: colores.primario,
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  botonDeshabilitado: {
    opacity: 0.7,
  },
  textoBoton: {
    color: '#ffffff',
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
  },
  pie: {
    textAlign: 'center',
    color: colores.textoSuave,
    fontSize: fuentes.pequena,
    marginTop: 40,
  },
});
