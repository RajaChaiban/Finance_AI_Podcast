import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'path';
import fs from 'fs';

const compositionId = 'InteractiveDemoVideo';

const main = async () => {
  try {
    console.log('📦 Bundling video composition...');
    const bundled = await bundle(path.join(__dirname, 'src/index.tsx'));

    console.log('🎬 Selecting composition...');
    const composition = await selectComposition({
      serveUrl: bundled,
      id: compositionId,
    });

    // Ensure output directory exists
    const outDir = path.join(__dirname, 'out');
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    console.log('🎥 Rendering video...');
    await renderMedia({
      composition,
      serveUrl: bundled,
      codec: 'h264',
      outputLocation: path.join(outDir, 'interactive-demo-video.mp4'),
    });

    console.log('✅ Video rendered successfully: out/interactive-demo-video.mp4');
  } catch (error) {
    console.error('❌ Rendering failed:', error);
    process.exit(1);
  }
};

main();
