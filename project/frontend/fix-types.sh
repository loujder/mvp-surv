#!/bin/sh
find node_modules/@types/node -name '*.d.ts' -exec sed -i "s|'undici-types'|\"undici-types\"|g" {} \;
sed -i "s/throw err;//g" node_modules/vue-tsc/bin/vue-tsc.js