import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colores, fuentes } from './src/theme';
import type {
  RootStackParamList,
  AuthStackParamList,
  TabParamList,
  InventarioStackParamList,
  OCStackParamList,
  ProduccionStackParamList,
  EtiquetasStackParamList,
  ClientesPedidosStackParamList,
  ProgramacionStackParamList,
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
import { PantallaCerrarSesion } from './src/pantallas/PantallaCerrarSesion';
import { PantallaSuperAdmin } from './src/pantallas/PantallaSuperAdmin';
import { PantallaClientes } from './src/pantallas/PantallaClientes';
import { PantallaPedidos } from './src/pantallas/PantallaPedidos';
import { PantallaDetallePedido } from './src/pantallas/PantallaDetallePedido';
import { PantallaProgramarPedido } from './src/pantallas/PantallaProgramarPedido';
import { PantallaCapturarPedido } from './src/pantallas/PantallaCapturarPedido';
import { PantallaProgramacion } from './src/pantallas/PantallaProgramacion';
import { PantallaCambiarEmpresa } from './src/pantallas/PantallaCambiarEmpresa';

import {
  obtenerUsuarioActual,
  esSuperAdmin,
  esAdmin,
  obtenerNombreEmpresaContexto,
  registrarCambioEmpresa,
} from './src/servicios/auth';
import type { UsuarioMovil } from './src/tipos';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();
const InventarioNav = createNativeStackNavigator<InventarioStackParamList>();
const OCNav = createNativeStackNavigator<OCStackParamList>();
const ProduccionNav = createNativeStackNavigator<ProduccionStackParamList>();
const ClientesPedidosNav = createNativeStackNavigator<ClientesPedidosStackParamList>();
const ProgramacionNav = createNativeStackNavigator<ProgramacionStackParamList>();

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

function ClientesPedidosNavigator() {
  return (
    <ClientesPedidosNav.Navigator screenOptions={{ headerShown: false }}>
      <ClientesPedidosNav.Screen name="ListaPedidos" component={PantallaPedidos} />
      <ClientesPedidosNav.Screen name="DetallePedido" component={PantallaDetallePedido} />
      <ClientesPedidosNav.Screen name="ProgramarPedido" component={PantallaProgramarPedido} />
      <ClientesPedidosNav.Screen name="CapturarPedido" component={PantallaCapturarPedido} />
      <ClientesPedidosNav.Screen name="ListaClientes" component={PantallaClientes} />
    </ClientesPedidosNav.Navigator>
  );
}

function ProgramacionNavigator() {
  return (
    <ProgramacionNav.Navigator screenOptions={{ headerShown: false }}>
      <ProgramacionNav.Screen name="ProgramacionLista" component={PantallaProgramacion} />
    </ProgramacionNav.Navigator>
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

function BarraEmpresaContexto({ onCambiar }: { onCambiar: () => void }) {
  const [nombre, setNombre] = useState(obtenerNombreEmpresaContexto());

  useEffect(() => {
    const unsub = registrarCambioEmpresa(() => {
      setNombre(obtenerNombreEmpresaContexto());
    });
    return unsub;
  }, []);

  if (!nombre) return null;

  return (
    <Pressable style={styles.barraEmpresa} onPress={onCambiar}>
      <Ionicons name="business" size={14} color={colores.primario} />
      <Text style={styles.barraEmpresaTexto} numberOfLines={1}>
        {nombre}
      </Text>
      <Ionicons name="swap-horizontal" size={14} color={colores.primario} />
    </Pressable>
  );
}

function MainTabs({ onLogout }: { onLogout: () => void }) {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 60 + insets.bottom;
  const usuario = obtenerUsuarioActual();
  const superAdmin = esSuperAdmin();
  const admin = esAdmin();
  const [mostrarCambioEmpresa, setMostrarCambioEmpresa] = useState(false);
  const [recargarKey, setRecargarKey] = useState(0);

  useEffect(() => {
    const unsub = registrarCambioEmpresa(() => {
      setRecargarKey((k) => k + 1);
    });
    return unsub;
  }, []);

  if (mostrarCambioEmpresa) {
    return (
      <PantallaCambiarEmpresa
        onVolver={() => setMostrarCambioEmpresa(false)}
      />
    );
  }

  return (
    <View style={{ flex: 1, paddingTop: insets.top }} key={recargarKey}>
      {superAdmin && (
        <BarraEmpresaContexto
          onCambiar={() => setMostrarCambioEmpresa(true)}
        />
      )}
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
      <Tab.Screen
        name="InventarioTab"
        component={InventarioNavigator}
        options={{
          tabBarLabel: 'Inventario',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="cube-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="OCTab"
        component={OCNavigator}
        options={{
          tabBarLabel: 'Ordenes',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="receipt-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="ProduccionTab"
        component={ProduccionNavigator}
        options={{
          tabBarLabel: 'Producción',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="construct-outline" size={size} color={color} />
          ),
        }}
      />
      {admin && (
        <Tab.Screen
          name="ClientesPedidosTab"
          component={ClientesPedidosNavigator}
          options={{
            tabBarLabel: 'Pedidos',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="people-outline" size={size} color={color} />
            ),
          }}
        />
      )}
      {admin && (
        <Tab.Screen
          name="ProgramacionTab"
          component={ProgramacionNavigator}
          options={{
            tabBarLabel: 'Prog.',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="calendar-outline" size={size} color={color} />
            ),
          }}
        />
      )}
      <Tab.Screen
        name="EtiquetasTab"
        component={EtiquetasNavigator}
        options={{
          tabBarLabel: 'Etiquetas',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="pricetag-outline" size={size} color={color} />
          ),
        }}
      />
      {superAdmin && (
        <Tab.Screen
          name="AdminTab"
          component={PantallaSuperAdmin}
          options={{
            tabBarLabel: 'Admin',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="shield-checkmark-outline" size={size} color={color} />
            ),
          }}
        />
      )}
      <Tab.Screen
        name="PerfilTab"
        options={{
          tabBarLabel: 'Salir',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="log-out-outline" size={size} color={color} />
          ),
        }}
      >
        {({ navigation }) => (
          <PantallaCerrarSesion
            onLogout={() => {
              onLogout();
            }}
          />
        )}
      </Tab.Screen>
    </Tab.Navigator>
    </View>
  );
}

export default function Raiz() {
  const [cargando, setCargando] = useState(true);
  const [sesionActiva, setSesionActiva] = useState<UsuarioMovil | null>(null);

  useEffect(() => {
    verificarSesion();
  }, []);

  const verificarSesion = async () => {
    const u = obtenerUsuarioActual();
    setSesionActiva(u);
    setCargando(false);
  };

  const handleLogout = () => {
    setSesionActiva(null);
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
          {sesionActiva ? (
            <RootStack.Screen name="Main">
              {() => <MainTabs onLogout={handleLogout} />}
            </RootStack.Screen>
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
  barraEmpresa: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: colores.primario + '12',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: colores.primario + '30',
  },
  barraEmpresaTexto: {
    fontSize: fuentes.etiqueta,
    fontWeight: '600',
    color: colores.primario,
    flex: 1,
    textAlign: 'center',
  },
});
