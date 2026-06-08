const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve all static files under public folder
app.use(express.static(path.join(__dirname, 'public')));

// Fallback: Send index.html for root requests
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log('\n=============================================================');
    console.log(`🚀 OdoShield 3D Frontend running on: http://localhost:${PORT}`);
    console.log('=============================================================\n');
});
