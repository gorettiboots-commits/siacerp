#!/bin/bash
cd mobile
echo "Iniciando build de APK..."
echo "Fecha: $(date)"
npx eas-cli build --platform android --profile production --non-interactive 2>&1
echo ""
echo "Build finalizado: $(date)"
