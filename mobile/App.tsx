import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View, StyleSheet, Text } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colores } from './src/theme';
import type {
  RootStackParamList,
  AuthStackParamList,
  TabParamList,
  InventarioStackParamList,
  OCStackParamList,
  ProduccionStackParamList,
  EtiquetasStackParamList,
} from './src/navegacion';

import { PantallaLogin } from './src/pantallas/PantallaLogin';
import { PantallaInventario } from './src/pantallas/PantallaInventario';
import { PantallaDetalleInsumo } from './src/pantallas/PantallaDetalleInsumo';
import { PantallaOrdenesCompra } from './src/pantallas/PantallaOrdenesCompra';
import { PantallaDetalleOC } from './src/pantallas/PantallaDetalleOC';
import { PantallaProduccion } from './src/pantallas/PantallaProduccion';
import { PantallaDetalleOP } from './src/pantallas/PantallaDetalleOP';
import { PantallaInicio } from './src/pantallas/PantallaInicio';
import { PantallaFlejes } from './src/pantallas/PantallaFlejes';
import { PantallaPartidas } from './src/pantallas/PantallaPartidas';

import { obtenerUsuarioActual } from './src/servicios/auth';
import type { UsuarioMovil } from './src/tipos';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();
const InventarioNav = createNativeStackNavigator<InventarioStackParamList>();
const OCNav = createNativeStackNavigator<OCStackParamList>();
const ProduccionNav = createNativeStackNavigator<ProduccionStackParamList>();

function AuthNavigator({ onLogin }: { onLogin: () => void }) {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login">
        {() => <PantallaLogin onLogin={onLogin} />}
      </AuthStack.Screen>
    </AuthStack.Navigator>
  );
}

function InventarioNavigator() {
  return (
    <InventarioNav.Navigator screenOptions={{ headerShown: false }}>
      <InventarioNav.Screen name="ListaInsumos" component={PantallaInventario} />
      <InventarioNav.Screen name="DetalleInsumo" component={PantallaDetalleInsumo} />
    </InventarioNav.Navigator>
  );
}

function OCNavigator() {
  return (
    <OCNav.Navigator screenOptions={{ headerShown: false }}>
      <OCNav.Screen name="ListaOCs" component={PantallaOrdenesCompra} />
      <OCNav.Screen name="DetalleOC" component={PantallaDetalleOC} />
    </OCNav.Navigator>
  );
}

function ProduccionNavigator() {
  return (
    <ProduccionNav.Navigator screenOptions={{ headerShown: false }}>
      <ProduccionNav.Screen name="ListaOPs" component={PantallaProduccion} />
      <ProduccionNav.Screen name="DetalleOP" component={PantallaDetalleOP} />
    </ProduccionNav.Navigator>
  );
}

function EtiquetasNavigator() {
  const [pantalla, setPantalla] = useState<'inicio' | 'flejes' | 'partidas'>('inicio');
  switch (pantalla) {
    case 'flejes':
      return <PantallaFlejes onVolver={() => setPantalla('inicio')} />;
    case 'partidas':
      return <PantallaPartidas onVolver={() => setPantalla('inicio')} />;
    default:
      return (
        <PantallaInicio
          onFlejes={() => setPantalla('flejes')}
          onPartidas={() => setPantalla('partidas')}
        />
      );
  }
}

function MainTabs() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 60 + insets.bottom;
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colores.primario,
        tabBarInactiveTintColor: colores.textoSuave,
        tabBarStyle: {
          backgroundColor: colores.tarjeta,
          borderTopColor: colores.borde,
          paddingBottom: insets.bottom > 0 ? insets.bottom : 4,
          height: tabBarHeight,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tab.Screen name="InventarioTab" component={InventarioNavigator} options={{ tabBarLabel: 'Inventario' }} />
      <Tab.Screen name="OCTab" component={OCNavigator} options={{ tabBarLabel: 'Ordenes' }} />
      <Tab.Screen name="ProduccionTab" component={ProduccionNavigator} options={{ tabBarLabel: 'Produccion' }} />
      <Tab.Screen name="EtiquetasTab" component={EtiquetasNavigator} options={{ tabBarLabel: 'Etiquetas' }} />
    </Tab.Navigator>
  );
}

export default function Raiz() {
  const [cargando, setCargando] = useState(true);
  const [usuario, setUsuario] = useState<UsuarioMovil | null>(null);

  useEffect(() => {
    verificarSesion();
  }, []);

  const verificarSesion = async () => {
    const u = await obtenerUsuarioActual();
    setUsuario(u);
    setCargando(false);
  };

  if (cargando) {
    return (
      <View style={styles.cargando}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <RootStack.Navigator screenOptions={{ headerShown: false }}>
          {usuario ? (
            <RootStack.Screen name="Main" component={MainTabs} />
          ) : (
            <RootStack.Screen name="Auth">
              {() => <AuthNavigator onLogin={() => verificarSesion()} />}
            </RootStack.Screen>
          )}
        </RootStack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colores.fondo },
});
