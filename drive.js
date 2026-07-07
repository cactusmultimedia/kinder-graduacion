const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

const SCOPES = ['https://www.googleapis.com/auth/drive'];
const TOKEN_PATH = path.join(__dirname, 'token.json');
const CREDENTIALS_PATH = path.join(__dirname, 'credentials.json');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function prompt(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function authorize() {
  if (!fs.existsSync(CREDENTIALS_PATH)) {
    console.log('\n❌ No se encontró credentials.json');
    console.log('\n📋 Para obtener credenciales:');
    console.log('  1. Ve a https://console.cloud.google.com/');
    console.log('  2. Crea un proyecto o selecciona uno existente');
    console.log('  3. Activa la API de Google Drive');
    console.log('  4. Ve a "Credenciales" > "Crear credenciales" > "ID de cliente OAuth"');
    console.log('  5. Descarga el JSON y renómbralo a credentials.json');
    console.log('  6. Colócalo en la carpeta: ' + __dirname + '\n');
    process.exit(1);
  }

  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
  const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  if (fs.existsSync(TOKEN_PATH)) {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH));
    oAuth2Client.setCredentials(token);
    return oAuth2Client;
  }

  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
  });

  console.log('\n🔗 Abre esta URL en tu navegador:');
  console.log(authUrl);
  const code = await prompt('\nPega el código de autorización aquí: ');
  const { tokens } = await oAuth2Client.getToken(code);
  oAuth2Client.setCredentials(tokens);
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
  console.log('✅ Token guardado en token.json\n');
  return oAuth2Client;
}

async function listTrash(drive) {
  console.log('\n📂 BUSCANDO ARCHIVOS EN LA PAPELERA...\n');
  let pageToken = null;
  let total = 0;
  const folders = [];
  const files = [];

  do {
    const res = await drive.files.list({
      q: "trashed = true",
      fields: 'nextPageToken, files(id, name, mimeType, size, owners, modifiedTime, parents)',
      pageToken,
      pageSize: 100,
      orderBy: 'modifiedTime desc',
    });
    pageToken = res.data.nextPageToken;

    for (const file of res.data.files) {
      if (file.mimeType === 'application/vnd.google-apps.folder') {
        folders.push(file);
      } else {
        files.push(file);
      }
    }
    total += res.data.files.length;
  } while (pageToken);

  console.log(`📊 Total en papelera: ${total} elementos\n`);

  if (folders.length > 0) {
    console.log(`📁 CARPETAS (${folders.length}):`);
    folders.forEach(f => {
      const date = new Date(f.modifiedTime).toLocaleDateString('es-MX');
      console.log(`  📁 ${f.name} (${date})`);
    });
    console.log('');
  }

  if (files.length > 0) {
    console.log(`📄 ARCHIVOS (${files.length}):`);
    files.forEach(f => {
      const date = new Date(f.modifiedTime).toLocaleDateString('es-MX');
      const size = f.size ? `(${(parseInt(f.size) / 1024 / 1024).toFixed(1)} MB)` : '(sin tamaño)';
      const owner = f.owners?.[0]?.displayName || 'desconocido';
      console.log(`  📄 ${f.name} ${size} - ${owner} - ${date}`);
    });
    console.log('');
  }

  if (total === 0) {
    console.log('  (vacía) 🎉\n');
  }
}

async function listRootFolders(drive) {
  console.log('\n📂 CARPETAS PRINCIPALES EN EL DRIVE...\n');
  const res = await drive.files.list({
    q: "mimeType = 'application/vnd.google-apps.folder' and trashed = false and 'root' in parents",
    fields: 'files(id, name, owners, modifiedTime)',
    pageSize: 100,
    orderBy: 'name',
  });

  if (res.data.files.length === 0) {
    console.log('  (no se encontraron carpetas raíz)');
  } else {
    res.data.files.forEach(f => {
      const date = new Date(f.modifiedTime).toLocaleDateString('es-MX');
      const owner = f.owners?.[0]?.displayName || 'desconocido';
      console.log(`  📁 ${f.name} (dueño: ${owner} - ${date})`);
    });
  }
  console.log('');
}

async function uploadFile(drive, filePath, folderId) {
  const fileName = path.basename(filePath);
  const fileSize = fs.statSync(filePath).size;
  console.log(`  📤 Subiendo ${fileName} (${(fileSize / 1024 / 1024).toFixed(1)} MB)...`);

  const res = await drive.files.create({
    requestBody: {
      name: fileName,
      parents: [folderId],
    },
    media: {
      body: fs.createReadStream(filePath),
    },
    fields: 'id, name, webViewLink',
  });

  console.log(`     ✅ ${res.data.name} → ${res.data.webViewLink}`);
  return res.data;
}

async function uploadAll(drive) {
  const folderName = process.argv[3] || 'PSD';
  console.log(`\n🔍 Buscando carpeta "${folderName}"...\n`);

  const searchRes = await drive.files.list({
    q: `name = '${folderName}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`,
    fields: 'files(id, name)',
    pageSize: 10,
  });

  if (searchRes.data.files.length === 0) {
    console.log(`❌ No se encontró la carpeta "${folderName}"`);
    console.log('   Creala o usa: node drive.js upload <folder-id>');
    rl.close();
    return;
  }

  const folder = searchRes.data.files[0];
  console.log(`📁 Carpeta encontrada: ${folder.name} (ID: ${folder.id})\n`);

  const last30 = new Date();
  last30.setDate(last30.getDate() - 30);
  const last30ISO = last30.toISOString();

  const searchDirs = [
    '/Users/navirami/Documents',
    '/Users/navirami/Downloads',
    '/Users/navirami/Desktop',
  ];

  const extensions = ['.psd', '.ai'];
  const allFiles = [];

  for (const dir of searchDirs) {
    for (const ext of extensions) {
      try {
        const find = require('child_process').execSync(
          `find "${dir}" -maxdepth 4 -iname "*${ext}" -newer "${last30ISO}" -type f 2>/dev/null`,
          { encoding: 'utf8' }
        );
        if (find.trim()) {
          allFiles.push(...find.trim().split('\n'));
        }
      } catch (e) { /* ignore */ }
    }
  }

  const uniqueFiles = [...new Set(allFiles)];
  console.log(`📦 Archivos a subir (${uniqueFiles.length}):\n`);
  uniqueFiles.forEach(f => console.log(`   📄 ${path.basename(f)}`));
  console.log('');

  for (const filePath of uniqueFiles) {
    await uploadFile(drive, filePath, folder.id);
  }

  console.log(`\n🎉 ¡Subidos ${uniqueFiles.length} archivos a "${folderName}"!`);
}

async function main() {
  const action = process.argv[2] || 'trash';

  const auth = await authorize();
  const drive = google.drive({ version: 'v3', auth });

  if (action === 'folders') {
    await listRootFolders(drive);
  } else if (action === 'upload') {
    const filePath = process.argv[3];
    const folderId = process.argv[4];
    if (!filePath || !folderId) {
      console.log('Uso: node drive.js upload <ruta-archivo> <id-carpeta>');
      process.exit(1);
    }
    await uploadFile(drive, filePath, folderId);
  } else if (action === 'upload-all') {
    await uploadAll(drive);
  } else if (action === 'create-folder') {
    const folderName = process.argv[3];
    const parentId = process.argv[4];
    if (!folderName) {
      console.log('Uso: node drive.js create-folder <nombre> [id_carpeta_padre]');
      process.exit(1);
    }
    const fileMetadata = {
      name: folderName,
      mimeType: 'application/vnd.google-apps.folder',
    };
    if (parentId) fileMetadata.parents = [parentId];
    const res = await drive.files.create({
      resource: fileMetadata,
      fields: 'id, name, webViewLink',
    });
    console.log(`\n✅ Carpeta creada: ${res.data.name}`);
    console.log(`   ID: ${res.data.id}`);
    console.log(`   Link: ${res.data.webViewLink}\n`);
  } else if (action === 'search') {
    const query = process.argv[3];
    if (!query) {
      console.log('Uso: node drive.js search <nombre>');
      process.exit(1);
    }
    const res = await drive.files.list({
      q: `name contains '${query}' and trashed = false`,
      fields: 'files(id, name, mimeType, size, owners, modifiedTime, parents)',
      pageSize: 50,
    });
    console.log(`\n🔍 Resultados para "${query}":\n`);
    if (res.data.files.length === 0) {
      console.log('  (sin resultados)');
    } else {
      res.data.files.forEach(f => {
        const icon = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : '📄';
        console.log(`  ${icon} ${f.name}`);
        console.log(`     ID: ${f.id}`);
        console.log(`     Dueño: ${f.owners?.[0]?.displayName || '?'}`);
      });
    }
  } else {
    await listTrash(drive);
  }

  rl.close();
}

main().catch(err => {
  console.error('Error:', err.message);
  rl.close();
});
