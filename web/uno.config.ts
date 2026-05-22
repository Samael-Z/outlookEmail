import { defineConfig, presetUno, presetAttributify, presetIcons, transformerDirectives, transformerVariantGroup } from 'unocss';

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
      collections: {
        tabler: () => import('@iconify-json/tabler/icons.json').then(i => i.default as any),
        'material-symbols': () => import('@iconify-json/material-symbols/icons.json').then(i => i.default as any)
      }
    })
  ],
  transformers: [transformerDirectives(), transformerVariantGroup()],
  theme: {
    colors: {
      primary: '#646cff',
      info: '#2080f0',
      success: '#18a058',
      warning: '#f0a020',
      error: '#d03050'
    }
  },
  shortcuts: {
    'flex-center': 'flex items-center justify-center',
    'flex-x-center': 'flex justify-center',
    'flex-y-center': 'flex items-center',
    'flex-col-center': 'flex flex-col items-center justify-center',
    'wh-full': 'w-full h-full',
    'absolute-center': 'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2'
  }
});
