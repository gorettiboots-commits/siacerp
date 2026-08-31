import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colores, fuentes } from '../theme';
import { supabase } from '../lib/supabase';
import { cambiarEmpresaContexto } from '../servicios/auth';

interface EmpresaStats {
  id: string;
  nombre: string;
  rfc?: string;
  activo: boolean;
  usuarios: number;
  insumos: number;
  ocs: number;
  ops: number;
}

interface UsuarioInfo {
  id: string;
  username: string;
  nombre_completo: string;
  rol: string;
  activo: boolean;
  empresa_id?: string;
}

function TarjetaKPI({ titulo, valor, color }: { titulo: string; valor: string; color: string }) {
  return (
    <View style={[styles.kpiCard, { borderLeftColor: color }]}>
      <Text style={[styles.kpiLabel, { color }]}>{titulo.toUpperCase()}</Text>
      <Text style={styles.kpiValor}>{valor}</Text>
    </View>
  );
}

export function PantallaSuperAdmin() {
  const [cargando, setCargando] = useState(true);
  const [refrescando, setRefrescando] = useState(false);
  const [stats, setStats] = useState({
    total_empresas: 0,
    total_usuarios: 0,
    total_insumos: 0,
    total_ocs: 0,
    total_ops: 0,
  });
  const [empresas, setEmpresas] = useState<EmpresaStats[]>([]);
  const [empresaSeleccionada, setEmpresaSeleccionada] = useState<string | null>(null);
  const [usuarios, setUsuarios] = useState<UsuarioInfo[]>([]);
  const [cambiandoEstado, setCambiandoEstado] = useState<string | null>(null);

  const cargarDatos = async () => {
    if (!supabase) return;

    try {
      // Cargar empresas
      const { data: empresasData } = await supabase
        .from('empresas')
        .select('*')
        .order('nombre');

      if (!empresasData) return;

      const empresasConStats: EmpresaStats[] = [];
      let totalUsuarios = 0;
      let totalInsumos = 0;
      let totalOcs = 0;
      let totalOps = 0;

      for (const emp of empresasData) {
        const { count: usCount } = await supabase
          .from('perfiles_usuario')
          .select('*', { count: 'exact', head: true })
          .eq('empresa_id', emp.id)
          .eq('activo', true);

        const { count: insCount } = await supabase
          .from('insumos_movil')
          .select('*', { count: 'exact', head: true })
          .eq('empresa_id', emp.id);

        const { count: ocCount } = await supabase
          .from('ordenes_compra_movil')
          .select('*', { count: 'exact', head: true })
          .eq('empresa_id', emp.id);

        const { count: opCount } = await supabase
          .from('ordenes_produccion_movil')
          .select('*', { count: 'exact', head: true })
          .eq('empresa_id', emp.id);

        const u = usCount || 0;
        const i = insCount || 0;
        const o = ocCount || 0;
        const p = opCount || 0;

        empresasConStats.push({
          id: emp.id,
          nombre: emp.nombre,
          rfc: emp.rfc,
          activo: emp.activo,
          usuarios: u,
          insumos: i,
          ocs: o,
          ops: p,
        });

        totalUsuarios += u;
        totalInsumos += i;
        totalOcs += o;
        totalOps += p;
      }

      setEmpresas(empresasConStats);
      setStats({
        total_empresas: empresasData.length,
        total_usuarios: totalUsuarios,
        total_insumos: totalInsumos,
        total_ocs: totalOcs,
        total_ops: totalOps,
      });

      // Si hay empresa seleccionada, recargar sus usuarios
      if (empresaSeleccionada) {
        await cargarUsuarios(empresaSeleccionada);
      } else {
        await cargarTodosUsuarios();
      }
    } catch (e) {
      console.error('Error cargando datos super admin:', e);
    }
  };

  const cargarUsuarios = async (empresaId: string) => {
    if (!supabase) return;

    const { data } = await supabase
      .from('perfiles_usuario')
      .select('id, username, nombre_completo, rol, activo, empresa_id')
      .eq('empresa_id', empresaId)
      .order('username');

    setUsuarios(data || []);
  };

  const cargarTodosUsuarios = async () => {
    if (!supabase) return;

    const { data } = await supabase
      .from('perfiles_usuario')
      .select('id, username, nombre_completo, rol, activo, empresa_id')
      .order('username');

    setUsuarios(data || []);
  };

  useEffect(() => {
    const init = async () => {
      setCargando(true);
      await cargarDatos();
      setCargando(false);
    };
    init();
  }, []);

  const onRefresh = async () => {
    setRefrescando(true);
    await cargarDatos();
    setRefrescando(false);
  };

  const onEmpresaPress = async (empresaId: string) => {
    const nuevaSeleccion = empresaSeleccionada === empresaId ? null : empresaId;
    setEmpresaSeleccionada(nuevaSeleccion);
    if (nuevaSeleccion) {
      await cargarUsuarios(nuevaSeleccion);
    } else {
      await cargarTodosUsuarios();
    }
  };

  const toggleEmpresa = async (empresaId: string, activoActual: boolean, nombre: string) => {
    const accion = activoActual ? 'desactivar' : 'activar';
    Alert.alert(
      `${accion.charAt(0).toUpperCase() + accion.slice(1)} empresa`,
      `¿Desea ${accion} la empresa "${nombre}"?\n\n${activoActual ? 'Los usuarios no podrán iniciar sesión en desktop ni móvil.' : 'Los usuarios podrán iniciar sesión nuevamente.'}`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: accion.charAt(0).toUpperCase() + accion.slice(1),
          style: activoActual ? 'destructive' : 'default',
          onPress: async () => {
            if (!supabase) return;
            setCambiandoEstado(empresaId);
            try {
              const { error } = await supabase
                .from('empresas')
                .update({ activo: !activoActual })
                .eq('id', empresaId);

              if (error) {
                Alert.alert('Error', `No se pudo ${accion} la empresa: ${error.message}`);
              } else {
                Alert.alert('Éxito', `Empresa "${nombre}" ${accion}da correctamente.`);
                await cargarDatos();
              }
            } catch (e) {
              Alert.alert('Error', `No se pudo ${accion} la empresa.`);
            }
            setCambiandoEstado(null);
          },
        },
      ],
    );
  };

  const renderEmpresa = ({ item }: { item: EmpresaStats }) => (
    <View
      style={[
        styles.empresaCard,
        empresaSeleccionada === item.id && styles.empresaCardSeleccionada,
        !item.activo && styles.empresaCardInactiva,
      ]}
    >
      <Pressable
        style={styles.empresaPressable}
        onPress={() => onEmpresaPress(item.id)}
      >
        <View style={styles.empresaHeader}>
          <Ionicons
            name="business"
            size={20}
            color={item.activo ? colores.primario : colores.textoSuave}
          />
          <View style={styles.empresaInfo}>
            <Text style={styles.empresaNombre}>{item.nombre}</Text>
            {item.rfc && <Text style={styles.empresaRfc}>RFC: {item.rfc}</Text>}
          </View>
          <View
            style={[
              styles.estadoBadge,
              { backgroundColor: item.activo ? '#d1fae5' : '#fee2e2' },
            ]}
          >
            <Text
              style={[
                styles.estadoTexto,
                { color: item.activo ? colores.exito : colores.peligro },
              ]}
            >
              {item.activo ? 'Activa' : 'Inactiva'}
            </Text>
          </View>
        </View>
        <View style={styles.empresaStats}>
          <Text style={styles.statTexto}>{item.usuarios} usuarios</Text>
          <Text style={styles.statTexto}>{item.insumos} insumos</Text>
          <Text style={styles.statTexto}>{item.ocs} OCs</Text>
          <Text style={styles.statTexto}>{item.ops} OPs</Text>
        </View>
      </Pressable>

      {/* Botones de acción */}
      <View style={styles.botonesRow}>
        {/* Cambiar contexto */}
        {item.activo && (
          <Pressable
            style={[styles.botonAccion, { backgroundColor: '#EFF6FF' }]}
            onPress={() => cambiarEmpresaContexto(item.id, item.nombre)}
          >
            <Ionicons name="swap-horizontal" size={14} color={colores.primario} />
            <Text style={[styles.textoBotonAccion, { color: colores.primario }]}>
              Ver datos
            </Text>
          </Pressable>
        )}

        {/* Activar/desactivar */}
        <Pressable
          style={[styles.botonAccion, { backgroundColor: item.activo ? '#FEE2E2' : '#D1FAE5' }]}
          onPress={() => toggleEmpresa(item.id, item.activo, item.nombre)}
          disabled={cambiandoEstado === item.id}
        >
          {cambiandoEstado === item.id ? (
            <ActivityIndicator size="small" color={colores.textoSuave} />
          ) : (
            <Ionicons
              name={item.activo ? 'ban-outline' : 'checkmark-circle-outline'}
              size={14}
              color={item.activo ? colores.peligro : colores.exito}
            />
          )}
          <Text
            style={[styles.textoBotonAccion, { color: item.activo ? colores.peligro : colores.exito }]}>
            {item.activo ? 'Desactivar' : 'Activar'}
          </Text>
        </Pressable>
      </View>
    </View>
  );

  const renderUsuario = ({ item }: { item: UsuarioInfo }) => (
    <View style={styles.usuarioCard}>
      <Ionicons name="person" size={16} color={colores.textoSuave} />
      <View style={styles.usuarioInfo}>
        <Text style={styles.usuarioNombre}>
          {item.nombre_completo || item.username}
        </Text>
        <Text style={styles.usuarioRol}>
          {item.rol} — @{item.username}
        </Text>
      </View>
      <View
        style={[
          styles.estadoBadge,
          { backgroundColor: item.activo ? '#d1fae5' : '#fee2e2' },
        ]}
      >
        <Text
          style={[
            styles.estadoTexto,
            { color: item.activo ? colores.exito : colores.peligro },
          ]}
        >
          {item.activo ? 'Activo' : 'Inactivo'}
        </Text>
      </View>
    </View>
  );

  if (cargando) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.cargando}>
          <ActivityIndicator size="large" color={colores.primario} />
          <Text style={styles.cargandoTexto}>Cargando panel de administración...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const empresaSeleccionadaInfo = empresaSeleccionada
    ? empresas.find((e) => e.id === empresaSeleccionada)
    : null;

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Ionicons name="shield-checkmark" size={24} color={colores.primario} />
        <Text style={styles.headerTitle}>Panel de Administración</Text>
      </View>

      <FlatList
        data={[]}
        renderItem={() => null}
        ListHeaderComponent={
          <>
            {/* KPIs */}
            <View style={styles.kpiGrid}>
              <TarjetaKPI titulo="Empresas" valor={String(stats.total_empresas)} color="#7C3AED" />
              <TarjetaKPI titulo="Usuarios" valor={String(stats.total_usuarios)} color="#2563EB" />
              <TarjetaKPI titulo="Insumos" valor={String(stats.total_insumos)} color="#16A34A" />
              <TarjetaKPI titulo="OCs" valor={String(stats.total_ocs)} color="#EA580C" />
              <TarjetaKPI titulo="OPs" valor={String(stats.total_ops)} color="#DC2626" />
            </View>

            {/* Lista de empresas */}
            <Text style={styles.seccionTitulo}>Empresas Registradas</Text>
            <FlatList
              data={empresas}
              renderItem={renderEmpresa}
              keyExtractor={(item) => item.id}
              scrollEnabled={false}
            />

            {/* Sección de usuarios */}
            <Text style={styles.seccionTitulo}>
              {empresaSeleccionadaInfo
                ? `Usuarios de ${empresaSeleccionadaInfo.nombre}`
                : 'Todos los Usuarios'}
              {' '}({usuarios.length})
            </Text>

            {empresaSeleccionada && (
              <Pressable
                style={styles.botonLimpiar}
                onPress={() => onEmpresaPress(empresaSeleccionada)}
              >
                <Ionicons name="close-circle" size={14} color={colores.primario} />
                <Text style={styles.botonLimpiarTexto}>Mostrar todos</Text>
              </Pressable>
            )}

            <FlatList
              data={usuarios}
              renderItem={renderUsuario}
              keyExtractor={(item) => item.id}
              scrollEnabled={false}
            />
          </>
        }
        refreshControl={
          <RefreshControl refreshing={refrescando} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.lista}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colores.fondo },
  cargando: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  cargandoTexto: { marginTop: 12, color: colores.textoSuave, fontSize: fuentes.subtitulo },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colores.tarjeta,
    borderBottomWidth: 1,
    borderBottomColor: colores.borde,
    gap: 8,
  },
  headerTitle: {
    fontSize: fuentes.titulo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  lista: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
  },
  kpiCard: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    borderLeftWidth: 3,
    padding: 12,
    width: '30%',
    minWidth: 100,
  },
  kpiLabel: {
    fontSize: 9,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  kpiValor: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colores.texto,
    marginTop: 2,
  },
  seccionTitulo: {
    fontSize: fuentes.subtitulo,
    fontWeight: 'bold',
    color: colores.texto,
    marginTop: 20,
    marginBottom: 8,
  },
  empresaCard: {
    backgroundColor: colores.tarjeta,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colores.borde,
    overflow: 'hidden',
  },
  empresaPressable: {
    padding: 12,
  },
  empresaCardSeleccionada: {
    borderColor: colores.primario,
    borderWidth: 2,
  },
  empresaCardInactiva: {
    opacity: 0.6,
  },
  empresaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  empresaInfo: {
    flex: 1,
  },
  empresaNombre: {
    fontSize: fuentes.cuerpo,
    fontWeight: 'bold',
    color: colores.texto,
  },
  empresaRfc: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
  },
  empresaStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  statTexto: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
  },
  estadoBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  estadoTexto: {
    fontSize: fuentes.pequena,
    fontWeight: '600',
  },
  botonesRow: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colores.borde,
  },
  botonAccion: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
  },
  textoBotonAccion: {
    fontSize: fuentes.etiqueta,
    fontWeight: '600',
  },
  usuarioCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.tarjeta,
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: colores.borde,
    gap: 10,
  },
  usuarioInfo: {
    flex: 1,
  },
  usuarioNombre: {
    fontSize: fuentes.cuerpo,
    fontWeight: '500',
    color: colores.texto,
  },
  usuarioRol: {
    fontSize: fuentes.pequena,
    color: colores.textoSuave,
  },
  botonLimpiar: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colores.primario + '15',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 8,
    gap: 4,
  },
  botonLimpiarTexto: {
    fontSize: fuentes.pequena,
    color: colores.primario,
    fontWeight: '600',
  },
});
