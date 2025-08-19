const express = require('express');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

function callPythonScraper(command, args = []) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', ['scraper_bot.py', command, ...args]);
    let data = '';
    let error = '';

    pythonProcess.stdout.on('data', (chunk) => {
      data += chunk.toString();
    });

    pythonProcess.stderr.on('data', (chunk) => {
      error += chunk.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python script exited with code ${code}: ${error}`);
        return reject(new Error('Scraper script failed. Check server logs.'));
      }
      try {
        resolve(JSON.parse(data));
      } catch (e) {
        console.error("Failed to parse JSON from Python script:", data);
        reject(new Error('Failed to parse JSON from Python script.'));
      }
    });
  });
}

app.get('/api/recent', async (req, res) => {
  try {
    const data = await callPythonScraper('recent');
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/search', async (req, res) => {
  const query = req.query.query;
  if (!query) {
    return res.status(400).json({ error: 'Search query is required.' });
  }
  try {
    const data = await callPythonScraper('search', [query]);
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/details/:id', async (req, res) => {
  try {
    const data = await callPythonScraper('details', [req.params.id]);
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/stream/:episodeId', async (req, res) => {
  try {
    const data = await callPythonScraper('stream', [req.params.episodeId]);
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => console.log(`Dokianime server running on port ${PORT}`));