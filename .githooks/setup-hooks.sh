#!/bin/sh
#
# Script per configurare i git hooks
# Esegui questo script dopo aver clonato il repository
#

echo "Configurazione git hooks..."

# Configura git per usare la directory .githooks
git config core.hooksPath .githooks

# Rendi eseguibili i file degli hooks
chmod +x .githooks/*

echo "Git hooks configurati correttamente!"
echo "La directory .githooks è ora attiva per questo repository."
