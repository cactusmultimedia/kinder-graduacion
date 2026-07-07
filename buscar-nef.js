const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const SCOPES = ['https://www.googleapis.com/auth/drive.readonly'];
const TOKEN_PATH = path.join(__dirname, 'token.json');
const CREDENTIALS_PATH = path.join(__dirname, 'credentials.json');

async function authorize() {
  if (!fs.existsSync(CREDENTIALS_PATH)) {
    console.log('❌ No se encontró credentials.json');
    process.exit(1);
  }
  if (!fs.existsSync(TOKEN_PATH)) {
    console.log('❌ No hay token. Corre primero: node drive.js folders');
    process.exit(1);
  }
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
  const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
  oAuth2Client.setCredentials(JSON.parse(fs.readFileSync(TOKEN_PATH)));
  return oAuth2Client;
}

async function main() {
  const auth = await authorize();
  const drive = google.drive({ version: 'v3', auth });

  // 22 de abril de 2026: de 00:00 a 23:59
  const desde = '2026-04-22T00:00:00';
  const hasta = '2026-04-22T23:59:59';

  const query = "mimeType contains 'image/nikon' and modifiedTime >= '${desde}' and modifiedTime <= '${hasta}' and trashed = false";

  console.log('\n🔍 Buscando NEF del 22 de abril de 2026...\n');

  let pageToken = null;
  let total = 0;

  do {
    const res = await drive.files.list({
      q: query,
      fields: 'nextPageToken, files(id, name, size, owners, modifiedTime, webViewLink)',
      pageToken,
      pageSize: 100,
      orderBy: 'name',
    });
    pageToken = res.data.nextPageToken;

    for (const f of res.data.files) {
      total++;
      const size = f.size ? `${(parseInt(f.size) / 1024 / 1024).toFixed(1)} MB` : '?';
      const owner = f.owners?.[0]?.displayName || '?';
      const date = new Date(f.modifiedTime).toLocaleString('es-MX');
      console.log(`  📄 ${f.name}`);
      console.log(`     Tamaño: ${size}  |  Dueño: ${owner}  |  ${date}`);
      console.log(`     Link: ${f.webViewLink || 'https://drive.google.com/file/d/' + f.id}`);
      console.log('');
    }
  } while (pageToken);

  if (total === 0) {
    console.log('  (sin resultados)');
    console.log('  Probando búsqueda más amplia por extensión .NEF...\n');
    // intentar por nombre también
    const res2 = await drive.files.list({
      q: "name contains '.nef' or name contains '.NEF' and trashed = false",
      fields: 'files(id, name, size, modifiedTime, webViewLink)',
      pageSize: 50,
      orderBy: 'modifiedTime desc',
    });
    for (const f of res2.data.files) {
      total++;
      const size = f.size ? `${(parseInt(f.size) / 1024 / 1024).toFixed(1)} MB` : '?';
      const date = new Date(f.modifiedTime).toLocaleString('es-MX');
      console.log(`  📄 ${f.name}`);
      console.log(`     Tamaño: ${size}  |  ${date}`);
      console.log(`     Link: ${f.webViewLink || 'https://drive.google.com/file/d/' + f.id}`);
      console.log('');
    }
  }

  console.log(`📊 Total: ${total} archivos encontrados`);
}

main().catch(err => console.error('Error:', err.message));
