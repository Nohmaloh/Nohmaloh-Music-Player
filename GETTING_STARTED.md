# 🎵 Focus Music Processor - Beginner's Guide

Welcome! This guide will help you get the Focus Music Processor running on your computer, even if you're new to programming.

## What Does This App Do?

The Focus Music Processor takes your regular music and transforms it into "focus-friendly" versions by:
- Reducing distracting vocals
- Adjusting the tempo to help concentration
- Applying audio effects that enhance focus

## What You'll Need

### Required Software (Don't worry, we'll install these together!)
- **Python** (3.8 or newer) - The programming language our app uses
- **Node.js** (16 or newer) - Needed for the web interface
- **PostgreSQL** - A database to store your music information
- **Git** - To download the code (optional, you can download as ZIP instead)

### Computer Requirements
- **Windows 10+**, **macOS 10.15+**, or **Linux**
- **4GB RAM minimum** (8GB recommended)
- **2-3x your music library size** in free disk space

---

## Step 1: Install Required Software

### Install Python
1. Go to [python.org](https://www.python.org/downloads/)
2. Download the latest Python 3.x version
3. **Important**: During installation, check "Add Python to PATH"
4. Test it works by opening Command Prompt/Terminal and typing: `python --version`

### Install Node.js
1. Go to [nodejs.org](https://nodejs.org/)
2. Download the "LTS" (recommended) version
3. Install with default settings
4. Test it works by typing in terminal: `node --version`

### Install PostgreSQL
1. Go to [postgresql.org/download](https://www.postgresql.org/download/)
2. Download for your operating system
3. During installation:
   - Remember the password you set for the "postgres" user
   - Use default port (5432)
4. Test by opening "pgAdmin" (comes with PostgreSQL)

### Install Git (Optional)
1. Go to [git-scm.com](https://git-scm.com/)
2. Download and install
3. Or just download this project as a ZIP file from GitHub

---

## Step 2: Get the Code

### Option A: Using Git (Recommended)
```bash
git clone <your-repository-url>
cd music-processor-full
```

### Option B: Download ZIP
1. Go to the GitHub page for this project
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file
5. Open the extracted folder

---

## Step 3: Set Up the Database

1. Open **pgAdmin** (PostgreSQL's management tool)
2. Connect to your PostgreSQL server (use the password you set)
3. Right-click "Databases" → "Create" → "Database"
4. Name it: `focus_music`
5. Click "Save"

---

## Step 4: Set Up the Backend (The Brain)

Open your terminal/command prompt and navigate to the project folder:

```bash
cd backend
```

### Create a Virtual Environment (Keeps things organized)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

**Note**: You'll need to run the activate command every time you work on this project.

### Install Python Packages
```bash
pip install -r requirements.txt
```

This might take a few minutes - it's downloading all the AI tools needed for audio processing!

### Configure the App
1. In the `backend` folder, create a new file called `.env`
2. Add these lines (replace with your actual details):

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/focus_music
MUSIC_FOLDER=../music
```

Replace `YOUR_PASSWORD` with the PostgreSQL password you set earlier.

### Initialize the Database
```bash
python database.py
```

If this works, you'll see a message saying the database tables were created.

---

## Step 5: Set Up the Frontend (The Interface)

Open a **new** terminal window (keep the backend one open) and navigate to the frontend:

```bash
cd frontend
npm install
```

This downloads all the web interface components.

---

## Step 6: Add Your Music

1. Create a folder called `music` in the main project directory (if it doesn't exist)
2. Copy some MP3, M4A, or FLAC files into this folder
3. You can organize them in subfolders like `music/Artist/Album/song.mp3`

**Supported formats**: MP3, M4A, FLAC, WAV

---

## Step 7: Start Everything Up!

You'll need **two terminal windows** open:

### Terminal 1 - Start the Backend
```bash
cd backend
# Activate virtual environment if not already active
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

python app.py
```

You should see something like: `INFO: Uvicorn running on http://127.0.0.1:8000`

### Terminal 2 - Start the Frontend
```bash
cd frontend
npm start
```

This should automatically open your web browser to `http://localhost:3000`

---

## Step 8: Use the App!

1. **First visit**: Click "Scan Music Library" to find your music files
2. **Select a song**: Click on any song in your library
3. **Create focus version**: 
   - Click "Focus Processing" to expand options
   - Adjust the "Focus Intensity" slider (start with 50%)
   - Click "Start Processing"
4. **Wait**: Processing takes 1-3 minutes depending on song length
5. **Listen**: Once done, you can switch between "Original" and "Focus" versions

---

## Troubleshooting

### "Python not found"
- Make sure you checked "Add Python to PATH" during installation
- Try `python3` instead of `python`

### "Permission denied" errors
- On Windows: Run Command Prompt as Administrator
- On Mac/Linux: You might need `sudo` for some commands

### Database connection fails
- Make sure PostgreSQL is running (check pgAdmin)
- Double-check your password in the `.env` file
- The database name should be exactly `focus_music`

### Frontend won't start
- Make sure Node.js is installed: `node --version`
- Try deleting `node_modules` folder and running `npm install` again

### No music shows up
- Check that your music files are in the `music` folder
- Supported formats: MP3, M4A, FLAC, WAV
- Click "Scan Music Library" button to refresh

### Processing fails
- Make sure you have enough disk space (2-3x song size)
- Try with a shorter song first (under 4 minutes)
- Check that the original file isn't corrupted

---

## What's Happening Behind the Scenes?

When you process a song for focus:

1. **AI Separation**: The app uses AI to separate vocals from instruments
2. **Focus Effects**: It applies special audio effects to reduce distractions
3. **Tempo Adjustment**: Optionally changes the speed to your target BPM
4. **Export**: Saves the new version as a high-quality MP3

---

## Next Steps

Once you're comfortable with the basics:

1. **Experiment**: Try different focus intensity levels
2. **Target BPM**: Set specific tempos for different activities
3. **Batch Processing**: Process multiple songs
4. **Read Full Docs**: Check out `DOCUMENTATION.md` for advanced features

---

## Getting Help

- **Check the logs**: Look for error messages in your terminal windows
- **Try simple songs first**: Start with short, clear audio files
- **Community**: Check the GitHub issues page for common problems
- **Documentation**: The full `DOCUMENTATION.md` has detailed technical info

---

## Tips for Success

1. **Start small**: Process one short song first to make sure everything works
2. **Keep terminals open**: Don't close the terminal windows while using the app
3. **Be patient**: Audio processing takes time, especially the first time
4. **Backup originals**: The app doesn't modify your original files
5. **Experiment**: Try different settings to find what works for your focus needs

Happy focusing! 🎧
