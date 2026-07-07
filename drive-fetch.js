const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { randomBytes } = require('crypto');

const CREDENTIALS = JSON.parse(fs.readFileSync(path.join(__dirname, 'credentials.json')));
const { client_id, client_secret, redirect_uris } = CREDENTIALS.installed;
const TOKEN_PATH = path.join(__dirname, 'token.json');

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const prompt = q => new Promise(r => rl.question(q, r));

async function getNewToken() {
  const state = randomBytes(16).toString('hex');
  const authUrl = `https://accounts.google.com/o/oauth2/auth?client_id=${client_id}&redirect_uri=${encodeURIComponent(redirect_uris[0])}&scope=${encodeURIComponent('https://www.googleapis.com/auth/drive')}&response_type=code&access_type=offline&state=${state}`;

  console.log('\n🔗 Abre esta URL en tu navegador:');
  console.log(authUrl);
  console.log('\n📋 Después de autorizar, serás redirigido a http://localhost/?code=...');
  console.log('   Copia el código (empieza con 4/...) de la URL y pégalo aquí.\n');

  const code = (await prompt('Código: ')).trim();

  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code,
      client_id,
      client_secret,
      redirect_uri: redirect_uris[0],
      grant_type: 'authorization_code',
    }),
  });

  const tokens = await resp.json();
  if (tokens.error) {
    console.error('❌ Error:', tokens.error_description || tokens.error);
    process.exit(1);
  }

  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
  console.log('✅ Token guardado en token.json\n');
  return tokens;
}

async function getToken() {
  if (fs.existsSync(TOKEN_PATH)) {
    return JSON.parse(fs.readFileSync(TOKEN_PATH));
  }
  return await getNewToken();
}

async function refreshIfNeeded(tokens) {
  const expiresAt = tokens.expiry_date || (tokens.expires_in ? Date.now() + tokens.expires_in * 1000 : 0);
  if (Date.now() >= expiresAt - 60000 && tokens.refresh_token) {
    console.log('🔄 Refrescando token...');
    const resp = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        refresh_token: tokens.refresh_token,
        client_id,
        client_secret,
        grant_type: 'refresh_token',
      }),
    });
    const newTokens = await resp.json();
    Object.assign(tokens, newTokens);
    tokens.expiry_date = Date.now() + (newTokens.expires_in || 3600) * 1000;
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
    console.log('✅ Token refrescado');
  }
  return tokens.access_token;
}

async function driveGet(accessToken, url) {
  const resp = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return resp.json();
}

async function main() {
  const action = process.argv[2] || 'search';
  const query = process.argv.slice(3).join(' ');

  const tokens = await getToken();
  const accessToken = await refreshIfNeeded(tokens);

  if (action === 'search') {
    const searchQuery = query || 'don profesor';
    console.log(`\n🔍 Buscando "${searchQuery}"...\n`);

    const data = await driveGet(accessToken,
      `https://www.googleapis.com/drive/v3/files?q=name contains '${encodeURIComponent(searchQuery)}' and trashed=false&fields=files(id,name,mimeType,size,owners,modifiedTime)`
    );

    if (!data.files || data.files.length === 0) {
      console.log('  (sin resultados)');
    } else {
      for (const f of data.files) {
        const icon = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : '📄';
        const size = f.size ? ` (${(parseInt(f.size)/1024/1024).toFixed(1)} MB)` : '';
        console.log(`  ${icon} ${f.name}${size}`);
        console.log(`     ID: ${f.id}`);
        console.log(`     Dueño: ${f.owners?.[0]?.displayName || '?'}`);
        console.log('');
      }
    }

    // If we found a folder, list its contents
    const folder = data.files?.find(f => f.mimeType === 'application/vnd.google-apps.folder');
    if (folder) {
      console.log(`📂 Contenido de "${folder.name}":\n`);
      const contents = await driveGet(accessToken,
        `https://www.googleapis.com/drive/v3/files?q='${folder.id}' in parents and trashed=false&fields=files(id,name,mimeType,size,modifiedTime)&orderBy=name`
      );
      if (!contents.files || contents.files.length === 0) {
        console.log('  (vacía)');
      } else {
        for (const f of contents.files) {
          const icon = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : '📄';
          const size = f.size ? ` (${(parseInt(f.size)/1024/1024).toFixed(1)} MB)` : '';
          const date = new Date(f.modifiedTime).toLocaleDateString('es-MX');
          console.log(`  ${icon} ${f.name}${size} - ${date}`);
        }
      }
    }
  } else if (action === 'list') {
    if (!query) {
      console.log('Uso: node drive-fetch.js list <folder-id>');
      process.exit(1);
    }
    console.log(`\n📂 Archivos en carpeta ${query}:\n`);
    const contents = await driveGet(accessToken,
      `https://www.googleapis.com/drive/v3/files?q='${query}' in parents and trashed=false&fields=files(id,name,mimeType,size,modifiedTime)&orderBy=name&pageSize=100`
    );
    if (!contents.files || contents.files.length === 0) {
      console.log('  (vacía)');
    } else {
      for (const f of contents.files) {
        const icon = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : '📄';
        const size = f.size ? ` (${(parseInt(f.size)/1024/1024).toFixed(1)} MB)` : '';
        const date = new Date(f.modifiedTime).toLocaleDateString('es-MX');
        console.log(`  ${icon} ${f.name}${size} - ${date}`);
        console.log(`     ID: ${f.id}`);
      }
    }
  } else if (action === 'download') {
    const fileId = process.argv[3];
    const destName = process.argv[4] || 'descarga';
    if (!fileId) {
      console.log('Uso: node drive-fetch.js download <file-id> [nombre-destino]');
      process.exit(1);
    }
    console.log(`\n⬇️  Descargando ${fileId}...`);
    const resp = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const buffer = Buffer.from(await resp.arrayBuffer());
    fs.writeFileSync(destName, buffer);
    console.log(`✅ Descargado como: ${destName} (${(buffer.length/1024/1024).toFixed(1)} MB)`);
  } else if (action === 'folders') {
    console.log('\n📂 Carpetas raíz:\n');
    const data = await driveGet(accessToken,
      `https://www.googleapis.com/drive/v3/files?q=mimeType='application/vnd.google-apps.folder' and trashed=false and 'root' in parents&fields=files(id,name,owners,modifiedTime)&orderBy=name`
    );
    if (!data.files || data.files.length === 0) {
      console.log('  (sin resultados)');
    } else {
      for (const f of data.files) {
        console.log(`  📁 ${f.name} (dueño: ${f.owners?.[0]?.displayName || '?'})`);
        console.log(`     ID: ${f.id}`);
      }
    }
  }

  rl.close();
}

main().catch(err => {
  console.error('Error:', err.message);
  rl.close();
});
