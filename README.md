==============================================================================
                       TIKTOK DOWNLOADER - MANUAL
==============================================================================

DESCRIPTION
-----------
This is a local web application for automatically downloading TikTok videos.
The program allows you to download videos from accounts, maintain a database
of downloaded content, and check for updates on tracked channels.

KEY FEATURES
------------
1. Download all videos from a specified account.
2. "Smart" download: if you provide a link to a specific video, the program 
   will download that video and ALL subsequent ones, skipping older ones.
3. Automatic file numbering (username_0001.mp4, username_0002.mp4...).
4. Update tracking for previously added accounts.
5. Operates via a user-friendly web interface in your browser.

REQUIREMENTS
------------
1. Python installed (version 3.8 or higher).
2. `yt-dlp.exe` file (the downloading utility).
3. Python libraries: flask, flask-cors.

INSTALLATION AND FIRST RUN
--------------------------
1. Ensure you have the `yt-dlp.exe` file.
   The path to it must be set in the `config.py` file.

2. Install the necessary libraries (one-time setup):
   Open a terminal (command prompt) in the project folder and run:
   pip install flask flask-cors

3. Configure paths:
   Open `config.py` in a text editor and check these variables:
   - YT_DLP_PATH: path to yt-dlp.exe
   - MATERIALS_PATH: folder where videos will be saved (e.g., D:\materials)

RUNNING THE PROGRAM
-------------------
1. Open a terminal in the program folder.
2. Run the `app.py` file using the command:
   python app.py
3. If successful, you will see the message:
   "Server on http://localhost:5000"
4. Open your browser and go to: http://localhost:5000
   (or simply open the index.html file if the interface works through it).

HOW TO USE
----------

OPTION A: Adding a new channel (download everything or from a specific point)
1. Copy a TikTok link.
   - Profile link (@username) -> Downloads the WHOLE channel.
   - Video link -> Downloads THIS video and all subsequent ones.
     (Older videos prior to the specified one will not be downloaded).
2. Paste the link into the input field in the browser.
3. Click the start button.
4. The process will begin. Videos will appear in: D:\materials\username\input

OPTION B: Checking for updates
1. If you have already downloaded channels, they are saved in the database.
2. Click the "Check Updates" button.
3. The program will scan all your added channels. If it finds new videos,
   it will automatically download them.

FOLDER STRUCTURE
----------------
D:\materials\           <- Root folder (configured in config.py)
  └── username\         <- Folder for a specific creator
      ├── input\        <- Downloaded videos go here
      └── output\       <- Empty folder (for your needs/sorting)

TROUBLESHOOTING
---------------
- Error "ModuleNotFoundError: No module named 'flask'":
  You forgot to run `pip install flask flask-cors`.

- Error "yt-dlp not found":
  Check the path in `config.py`. Note the use of double backslashes (\\)
  or the letter 'r' before the path (r"C:\Path...").

- Videos are not downloading:
  TikTok frequently changes its algorithms. You may need to update 
  yt-dlp.exe. To do this, run in the command prompt: yt-dlp -U