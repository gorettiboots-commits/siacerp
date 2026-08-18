import React, { useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { PantallaFlejes } from './src/pantallas/PantallaFlejes';
import { PantallaInicio } from './src/pantallas/PantallaInicio';
import { PantallaPartidas } from './src/pantallas/PantallaPartidas';

type Pantalla = 'inicio' | 'flejes' | 'partidas';

function App() {
  const [pantalla, setPantalla] = useState<Pantalla>('inicio');

  switch (pantalla) {
    case 'flejes':
      return <PantallaFlejes onVolver={() => setPantalla('inicio')} />;
    case 'partidas':
      return <PantallaPartidas onVolver={() => setPantalla('inicio')} />;
    case 'inicio':
    default:
      return (
        <PantallaInicio
          onFlejes={() => setPantalla('flejes')}
          onPartidas={() => setPantalla('partidas')}
        />
      );
  }
}

export default function Raiz() {
  return (
    <SafeAreaProvider>
      <App />
    </SafeAreaProvider>
  );
}