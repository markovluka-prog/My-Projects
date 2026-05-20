const webdav = require('webdav-server').v2;
const path = require('path');

const PORT = process.env.PORT || 1900;
const WD_USER = process.env.WD_USER || 'luka';
const WD_PASS = process.env.WD_PASS;

if (!WD_PASS) {
    console.error('ERROR: WD_PASS environment variable is required');
    process.exit(1);
}

const userManager = new webdav.SimpleUserManager();
const user = userManager.addUser(WD_USER, WD_PASS, false);

const privilegeManager = new webdav.SimplePathPrivilegeManager();
privilegeManager.setRights(user, '/', ['canRead', 'canReadProperties', 'canReadContent', 'canGetMimeType', 'canGetSize', 'canListLocks']);

const server = new webdav.WebDAVServer({
    port: PORT,
    requireAuthentification: true,
    httpAuthentification: new webdav.HTTPBasicAuthentification(userManager, privilegeManager)
});

const repoRoot = path.join(__dirname, '..');

server.setFileSystem('/', new webdav.PhysicalFileSystem(repoRoot), () => {
    server.start(() => {
        console.log(`WebDAV server on port ${PORT}`);
        console.log(`Serving: ${repoRoot}`);
    });
});
